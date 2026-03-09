"""
impact_predictor.py

Runs all 4 model predictions and formats results for the frontend.
Productivity uses a hybrid XGBoost + MLP ensemble (averaged output).
"""
import sys
import io
import traceback
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from model_loader import model_loader
from feature_engineering import (
    feature_engineer,
    build_effort_features,
    build_schedule_risk_features,
    build_quality_features,
    build_productivity_features,
)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


# Label map from risk_artifacts.pkl
SCHEDULE_LABEL_MAP = {0: 'Critical Risk', 1: 'High Risk', 2: 'Low Risk', 3: 'Medium Risk'}

_DEFAULT_FOCUS_HOURS = 6.0   # fallback; real value comes from Space.focus_hours_per_day


def _cap(v: float, lo: float = 0.0, hi: float = 99.0) -> float:
    return round(max(lo, min(hi, v)), 1)


# ══════════════════════════════════════════════════════════════════════════════
def generate_display_metrics(
    eff: dict, sched: dict, prod: dict, qual: dict,
    sprint_context: dict,
    focus_hours_per_day: float = _DEFAULT_FOCUS_HOURS,
) -> dict:
    """Convert raw prediction dicts into frontend-ready display objects."""
    days_remaining  = max(1, sprint_context.get('days_remaining', 14))
    hours_remaining = days_remaining * focus_hours_per_day

    # ── Effort ────────────────────────────────────────────────────────────────
    predicted_hours = eff.get('hours_median', 0.0)
    if predicted_hours > hours_remaining:
        eff_status, eff_label = 'critical', 'Sprint Overload'
        eff_sub = (f"Needs {predicted_hours:.0f}h but only {hours_remaining:.0f}h remain "
                   f"({focus_hours_per_day:.0f}h/day). Cannot finish in this sprint.")
    elif predicted_hours > hours_remaining * 0.8:
        eff_status, eff_label = 'warning', 'Tight Fit'
        eff_sub = (f"Needs {predicted_hours:.0f}h with {hours_remaining:.0f}h remaining "
                   f"({focus_hours_per_day:.0f}h/day). Very little buffer.")
    else:
        eff_status, eff_label = 'safe', 'Fits in Sprint'
        eff_sub = (f"Needs {predicted_hours:.0f}h with {hours_remaining:.0f}h remaining "
                   f"({focus_hours_per_day:.0f}h/day). Fits comfortably.")

    # ── Schedule Risk ─────────────────────────────────────────────────────────
    spillover_pct = _cap(sched.get('probability', 0.0))
    if spillover_pct > 50:
        sch_status, sch_label = 'critical', 'Delay Imminent'
        sch_sub = (f"{spillover_pct:.0f}% chance of spillover. Sprint goal is in danger. "
                   "Consider deferring or swapping.")
    elif spillover_pct > 30:
        sch_status, sch_label = 'warning', 'Moderate Risk'
        sch_sub = f"{spillover_pct:.0f}% chance of spillover. Monitor closely."
    else:
        sch_status, sch_label = 'safe', 'On Track'
        sch_sub = f"{spillover_pct:.0f}% chance of spillover. Likely to finish on time."

    # ── Productivity ──────────────────────────────────────────────────────────
    velocity_change  = prod.get('velocity_change', 0.0)
    days_lost        = prod.get('days_lost', 0.0)
    drop_pct         = prod.get('drop_pct', abs(prod.get('velocity_change', 0.0)))
    drag_pct         = _cap(drop_pct, hi=99.0)

    if drag_pct > 30:
        prd_status, prd_label = 'critical', 'High Drag'
        prd_sub = (f"Context switching to this task will seriously disrupt team velocity. "
                   f"Approximately {drag_pct:.0f}% slowdown expected on remaining backlog.")
    elif drag_pct > 10:
        prd_status, prd_label = 'warning', 'Negative'
        prd_sub = (f"Context switching to this task will slow down the remaining "
                   f"backlog items by approximately {drag_pct:.0f}%.")
    else:
        prd_status, prd_label = 'safe', 'Minimal Impact'
        prd_sub = (f"Adding this task has minimal impact on team flow. "
                   f"Estimated {drag_pct:.0f}% slowdown on remaining backlog.")

    # ── Quality ───────────────────────────────────────────────────────────────
    defect_pct = _cap(qual.get('probability', 0.0))
    if defect_pct > 60:
        qua_status, qua_label = 'critical', 'High Bug Risk'
        qua_sub = f"{defect_pct:.0f}% defect likelihood. Double QA time recommended."
    elif defect_pct > 30:
        qua_status, qua_label = 'warning', 'Elevated Risk'
        qua_sub = f"{defect_pct:.0f}% defect likelihood. Additional review cycle advised."
    else:
        qua_status, qua_label = 'safe', 'Standard Risk'
        qua_sub = f"{defect_pct:.0f}% defect likelihood. Standard testing required."

    return {
        'effort': {
            'value':    f"{predicted_hours:.0f}h / {hours_remaining:.0f}h Remaining",
            'label':    eff_label,
            'status':   eff_status,
            'sub_text': eff_sub,
        },
        'schedule': {
            'value':    f"{spillover_pct:.0f}% Probability of Spillover",
            'label':    sch_label,
            'status':   sch_status,
            'sub_text': sch_sub,
        },
        'productivity': {
            'value':    f"-{drag_pct:.0f}% Drop",
            'label':    prd_label,
            'status':   prd_status,
            'sub_text': prd_sub,
        },
        'quality': {
            'value':    f"{defect_pct:.0f}% Defect Risk",
            'label':    qua_label,
            'status':   qua_status,
            'sub_text': qua_sub,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
class ImpactPredictor:

    def __init__(self):
        self.models = model_loader.models

    def predict_all_impacts(
        self,
        item_data: dict,
        sprint_context: dict,
        existing_items=None,
        focus_hours_per_day: float = _DEFAULT_FOCUS_HOURS,
        risk_appetite: str = "Standard",
    ) -> dict:
        ctx = self._enrich_context(sprint_context)

        effort      = self._predict_effort(item_data, ctx, focus_hours_per_day)
        schedule    = self._predict_schedule_risk(item_data, ctx)
        quality     = self._predict_quality_risk(item_data, ctx)
        productivity= self._predict_productivity(item_data, ctx)
        summary     = self._generate_summary(effort, schedule, quality, productivity, risk_appetite)
        display     = generate_display_metrics(
                          effort, schedule, productivity, quality,
                          ctx, focus_hours_per_day)
        features    = feature_engineer.extract_features(item_data, ctx)

        return {
            'effort':        effort,
            'schedule_risk': schedule,
            'quality_risk':  quality,
            'productivity':  productivity,
            'summary':       summary,
            'display':       display,
            'features':      features,
        }

    # ── context enrichment ────────────────────────────────────────────────────
    def _enrich_context(self, ctx: dict) -> dict:
        from datetime import datetime
        ctx = dict(ctx)
        start = ctx.get('start_date')
        end   = ctx.get('end_date')
        if start and end:
            if isinstance(start, str): start = datetime.strptime(start, '%Y-%m-%d')
            if isinstance(end,   str): end   = datetime.strptime(end,   '%Y-%m-%d')
            now = datetime.utcnow()
            ctx['days_since_sprint_start'] = max(0, (now - start).days)
            ctx['days_remaining']          = max(0, (end - now).days)
            total = max(1, (end - start).days)
            ctx['sprint_progress'] = ctx['days_since_sprint_start'] / total
        else:
            ctx.setdefault('days_since_sprint_start', 0)
            ctx.setdefault('days_remaining', 14)
            ctx.setdefault('sprint_progress', 0.0)
        return ctx

    # ── 1. Effort ─────────────────────────────────────────────────────────────
    def _predict_effort(
        self, item_data: dict, sprint_context: dict,
        focus_hours_per_day: float = _DEFAULT_FOCUS_HOURS,
    ) -> dict:
        try:
            feat_dict = build_effort_features(item_data, sprint_context)
            df        = pd.DataFrame([feat_dict])
            dmat      = xgb.DMatrix(df)

            lower  = float(self.models['effort_lower'].predict(dmat)[0])
            median = float(self.models['effort_median'].predict(dmat)[0])
            upper  = float(self.models['effort_upper'].predict(dmat)[0])

            # Ensure ordering
            lower, upper = min(lower, median), max(upper, median)

            days_remaining  = max(1, sprint_context.get('days_remaining', 14))
            hours_remaining = days_remaining * focus_hours_per_day

            if median > hours_remaining:
                status, label = 'critical', 'Sprint Overload'
            elif median > hours_remaining * 0.8:
                status, label = 'warning', 'Tight Fit'
            else:
                status, label = 'safe', 'Fits in Sprint'

            return {
                'hours_lower':     round(lower, 1),
                'hours_median':    round(median, 1),
                'hours_upper':     round(upper, 1),
                'hours_remaining': round(hours_remaining, 1),
                'status':          status,
                'status_label':    label,
                'explanation':     f"Predicted {median:.1f}h vs {hours_remaining:.0f}h remaining.",
            }
        except Exception as e:
            print(f"\n[EFFORT PREDICTION ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            print(f"[DEBUG] Features attempted: {feat_dict}\n")
            return self._fallback_effort(item_data, sprint_context, focus_hours_per_day)

    # ── 2. Schedule risk ──────────────────────────────────────────────────────
    def _predict_schedule_risk(self, item_data: dict, sprint_context: dict) -> dict:
        try:
            X     = build_schedule_risk_features(item_data, sprint_context)
            model = self.models['schedule_risk']
            proba = model.predict_proba(X)[0]

            # Debug: Log model info
            print(f"[v0] Model classes_: {model.classes_}", file=sys.stderr)
            print(f"[v0] Probabilities: {proba}", file=sys.stderr)
            print(f"[v0] Prediction sum: {proba.sum()}", file=sys.stderr)

            # BUG FIX: Dynamically check model.classes_ instead of hardcoded indices
            # Find indices for 'Critical Risk' and 'High Risk' classes
            classes = model.classes_
            critical_idx = None
            high_idx = None
            
            for idx, class_label in enumerate(classes):
                print(f"[v0] Class {idx}: {class_label} (type: {type(class_label).__name__})", file=sys.stderr)
                if class_label == 'Critical Risk':
                    critical_idx = idx
                elif class_label == 'High Risk':
                    high_idx = idx
            
            print(f"[v0] Critical index: {critical_idx}, High index: {high_idx}", file=sys.stderr)
            
            # Spillover probability = P(Critical Risk) + P(High Risk)
            spillover_prob_value = 0.0
            if critical_idx is not None:
                spillover_prob_value += float(proba[critical_idx])
            if high_idx is not None:
                spillover_prob_value += float(proba[high_idx])
            
            print(f"[v0] Spillover prob value before percentage: {spillover_prob_value}", file=sys.stderr)
            spillover_prob = _cap(spillover_prob_value * 100)
            print(f"[v0] Spillover prob after percentage: {spillover_prob}", file=sys.stderr)
            
            dominant_idx   = int(np.argmax(proba))
            dominant_label = SCHEDULE_LABEL_MAP.get(dominant_idx, 'Unknown')
            print(f"[v0] Dominant class: {dominant_idx} -> {dominant_label}", file=sys.stderr)

            if spillover_prob > 50:
                status, label = 'critical', 'High Risk'
            elif spillover_prob > 30:
                status, label = 'warning', 'Moderate Risk'
            else:
                status, label = 'safe', 'Low Risk'

            return {
                'probability':   spillover_prob,
                'status':        status,
                'status_label':  label,
                'dominant_class': dominant_label,
                'explanation':   f"'{dominant_label}'. {spillover_prob:.0f}% spillover probability.",
            }
        except Exception as e:
            print(f"\n[SCHEDULE RISK ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            print(f"[DEBUG] Feature array shape: {X.shape if hasattr(X, 'shape') else 'unknown'}")
            print(f"[DEBUG] Feature dtype: {X.dtype if hasattr(X, 'dtype') else 'unknown'}\n")
            return self._fallback_schedule_risk(item_data, sprint_context)

    # ── 3. Quality risk ───────────────────────────────────────────────────────
    def _predict_quality_risk(self, item_data: dict, sprint_context: dict) -> dict:
        try:
            X     = build_quality_features(item_data, sprint_context)
            model = self.models.get('quality_risk')
            if model is None:
                print("[QUALITY RISK] Model not loaded from model_loader")
                return self._fallback_quality_risk()

            # ── Debug: log array properties before inference ──────────────────
            print(f"\n[QUALITY RISK] Input array shape: {X.shape}", file=__import__('sys').stderr)
            print(f"[QUALITY RISK] Input array dtype: {X.dtype}", file=__import__('sys').stderr)
            print(f"[QUALITY RISK] Input array values: {X}", file=__import__('sys').stderr)
            print(f"[QUALITY RISK] Model type: {type(model)}", file=__import__('sys').stderr)
            print(f"[QUALITY RISK] Calling predict_proba()...", file=__import__('sys').stderr)

            proba      = model.predict_proba(X)[0]
            defect_pct = _cap(float(proba[1]) * 100)

            print(f"[QUALITY RISK] Proba output shape: {proba.shape}", file=__import__('sys').stderr)
            print(f"[QUALITY RISK] Proba values: {proba}", file=__import__('sys').stderr)
            print(f"[QUALITY RISK] Defect %: {defect_pct}\n", file=__import__('sys').stderr)

            if defect_pct > 60:
                status, label = 'critical', 'High Bug Risk'
            elif defect_pct > 30:
                status, label = 'warning', 'Elevated Risk'
            else:
                status, label = 'safe', 'Standard Risk'

            return {
                'probability':  defect_pct,
                'status':       status,
                'status_label': label,
                'explanation':  f"{defect_pct:.0f}% defect likelihood.",
            }
        except Exception as e:
            print(f"\n[QUALITY RISK ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            print(f"[DEBUG] Feature array shape: {X.shape if 'X' in locals() and hasattr(X, 'shape') else 'unknown'}")
            print(f"[DEBUG] Feature dtype: {X.dtype if 'X' in locals() and hasattr(X, 'dtype') else 'unknown'}\n")
            return self._fallback_quality_risk()

    # ── 4. Productivity — hybrid XGBoost + MLP ensemble ─────────────────���─────
    def _predict_productivity(self, item_data: dict, sprint_context: dict) -> dict:
        try:
            X = build_productivity_features(item_data, sprint_context)

            preds = []

            # XGBoost component
            if 'productivity_xgb' in self.models and XGBOOST_AVAILABLE:
                dmat = xgb.DMatrix(X)
                raw  = float(self.models['productivity_xgb'].predict(dmat)[0])
                preds.append(raw)

            # MLP component
            if 'productivity_nn' in self.models and TORCH_AVAILABLE:
                with torch.no_grad():
                    tensor = torch.tensor(X, dtype=torch.float32)
                    raw_nn = float(self.models['productivity_nn'](tensor)[0, 0])
                preds.append(raw_nn)

            if not preds:
                return self._fallback_productivity(sprint_context)

            # ── Log-space decoding ────────────────────────────────────────────
            # Both models were trained with log-space targets (stated in the
            # project description: "Log-Space Prediction to stabilise errors on
            # power-law productivity data"). Raw output = log(drop_percent), so:
            #   raw=1.0 → exp(1.0) = 2.7% drop    (light ticket)
            #   raw=2.5 → exp(2.5) = 12.2% drop   (medium ticket)
            #   raw=3.5 → exp(3.5) = 33.1% drop   (heavy mid-sprint addition)
            raw_avg        = float(np.mean(preds))
            drop_pct       = min(99.0, float(np.exp(raw_avg)))  # always positive %
            velocity_change= round(-drop_pct, 1)                # negative = drag

            days_remaining = max(1, sprint_context.get('days_remaining', 14))
            days_lost      = round((drop_pct / 100.0) * days_remaining, 1)

            if drop_pct > 30:
                status, label = 'critical', 'High Drag'
            elif drop_pct > 10:
                status, label = 'warning',  'Negative'
            else:
                status, label = 'safe',     'Minimal Impact'

            return {
                'velocity_change': velocity_change,   # e.g. -15.0
                'drop_pct':        round(drop_pct, 1),# e.g.  15.0
                'days_lost':       days_lost,
                'days_remaining':  days_remaining,
                'status':          status,
                'status_label':    label,
                'explanation':     (
                    f"Context switching to this task will slow down the remaining "
                    f"backlog items by approximately {drop_pct:.0f}%."
                ),
            }
        except Exception as e:
            print(f"\n[PRODUCTIVITY ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            print(f"[DEBUG] Feature array shape: {X.shape if 'X' in locals() and hasattr(X, 'shape') else 'unknown'}")
            print(f"[DEBUG] Feature dtype: {X.dtype if 'X' in locals() and hasattr(X, 'dtype') else 'unknown'}")
            if 'preds' in locals():
                print(f"[DEBUG] Predictions collected: {preds}")
            print(f"[DEBUG] XGBoost available: {XGBOOST_AVAILABLE}, MLP available: {TORCH_AVAILABLE}\n")
            return self._fallback_productivity(sprint_context)

    # ── summary scorer ────────────────────────────────────────────────────────
    def _generate_summary(self, effort, schedule, quality, productivity, risk_appetite: str = "Standard") -> dict:
        """
        Generate risk summary with thresholds adjusted by risk appetite.
        Strict: More conservative (DEFER score=5), Standard: Balanced (score=7), Lenient: Permissive (score=9)
        """
        # Risk appetite thresholds for recommendation scores
        thresholds = {
            "Strict": {"defer": 5, "swap": 3, "split": 1},
            "Standard": {"defer": 7, "swap": 4, "split": 2},
            "Lenient": {"defer": 9, "swap": 6, "split": 3},
        }
        
        thresh = thresholds.get(risk_appetite, thresholds["Standard"])
        defer_threshold = thresh["defer"]
        swap_threshold = thresh["swap"]
        split_threshold = thresh["split"]
        
        score = 0
        if effort['status']     == 'critical': score += 3
        elif effort['status']   == 'warning':  score += 2
        if schedule.get('probability', 0) > 50: score += 3
        elif schedule.get('probability', 0) > 30: score += 2
        if quality.get('probability', 0) > 60:  score += 2
        elif quality.get('probability', 0) > 30: score += 1
        if productivity.get('drop_pct', abs(productivity.get('velocity_change', 0))) > 30: score += 2
        elif productivity.get('drop_pct', abs(productivity.get('velocity_change', 0))) > 10: score += 1

        if score >= defer_threshold:
            return {'risk_score': score, 'overall_risk': 'critical', 'recommendation': 'DEFER', 'risk_appetite': risk_appetite}
        elif score >= swap_threshold:
            return {'risk_score': score, 'overall_risk': 'high',     'recommendation': 'SWAP', 'risk_appetite': risk_appetite}
        elif score >= split_threshold:
            return {'risk_score': score, 'overall_risk': 'medium',   'recommendation': 'SPLIT', 'risk_appetite': risk_appetite}
        else:
            return {'risk_score': score, 'overall_risk': 'low',      'recommendation': 'ADD', 'risk_appetite': risk_appetite}

    # ── fallbacks ─────────────────────────────────────────────────────────────
    def _fallback_effort(self, item_data, sprint_context,
                         focus_hours_per_day=_DEFAULT_FOCUS_HOURS):
        h = item_data.get('story_points', 5) * 5
        hr = sprint_context.get('days_remaining', 14) * focus_hours_per_day
        status = 'critical' if h > hr else 'warning'
        return {
            'hours_lower': round(h * 0.8, 1), 'hours_median': float(h),
            'hours_upper': round(h * 1.2, 1), 'hours_remaining': float(hr),
            'status': status,
            'status_label': 'Sprint Overload' if status == 'critical' else 'Estimated',
            'explanation': 'Fallback: 5h per story point',
        }

    def _fallback_schedule_risk(self, item_data, sprint_context):
        sp   = item_data.get('story_points', 5)
        days = max(1, sprint_context.get('days_remaining', 14))
        risk = _cap((sp / days) * 50)
        status = 'critical' if risk > 50 else ('warning' if risk > 30 else 'safe')
        label  = 'High Risk'     if status == 'critical' else \
                 'Moderate Risk' if status == 'warning'  else 'Low Risk'
        return {'probability': risk, 'status': status, 'status_label': label,
                'dominant_class': 'N/A', 'explanation': 'Fallback estimate'}

    def _fallback_quality_risk(self):
        return {'probability': 40.0, 'status': 'warning',
                'status_label': 'Elevated Risk', 'explanation': 'Fallback quality estimate'}

    def _fallback_productivity(self, sprint_context):
        days = max(1, sprint_context.get('days_remaining', 14))
        return {
            'velocity_change': -10.0,
            'drop_pct':        10.0,
            'days_lost':       round(0.1 * days, 1),
            'days_remaining':  days,
            'status':          'warning',
            'status_label':    'Negative',
            'explanation':     'Context switching to this task will slow down the remaining backlog items.',
        }


impact_predictor = ImpactPredictor()