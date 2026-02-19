import numpy as np
import pandas as pd
from typing import Dict, Any
from model_loader import model_loader
from feature_engineering import (
    feature_engineer,
    build_effort_features,
    build_schedule_risk_features,
    build_quality_features,
    build_productivity_features,
)

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


SCHEDULE_LABEL_MAP = {0: 'Critical Risk', 1: 'High Risk', 2: 'Low Risk', 3: 'Medium Risk'}
WORK_HOURS_PER_DAY = 6


def generate_display_metrics(eff: dict, sched: dict, prod: dict, qual: dict, data: dict) -> dict:
    """Generate user-friendly display metrics from raw predictions"""
    days_remaining = max(1, data.get('days_remaining', 14))
    hours_remaining = days_remaining * WORK_HOURS_PER_DAY

    # EFFORT
    predicted_hours = eff.get('hours_median', 0.0)
    if predicted_hours > hours_remaining:
        effort_status = 'critical'
        effort_label = 'Sprint Overload'
        effort_sub_text = f"Needs {predicted_hours:.0f}h but only {hours_remaining:.0f}h remain. This ticket cannot finish in the current sprint."
    elif predicted_hours > hours_remaining * 0.8:
        effort_status = 'warning'
        effort_label = 'Tight Fit'
        effort_sub_text = f"Needs {predicted_hours:.0f}h with {hours_remaining:.0f}h remaining. Very little buffer for unexpected blockers."
    else:
        effort_status = 'safe'
        effort_label = 'Fits in Sprint'
        effort_sub_text = f"Needs {predicted_hours:.0f}h with {hours_remaining:.0f}h remaining. Effort fits comfortably."

    display_effort = {
        'value': f"{predicted_hours:.0f}h / {hours_remaining:.0f}h Remaining",
        'label': effort_label,
        'status': effort_status,
        'sub_text': effort_sub_text,
    }

    # SCHEDULE
    spillover_pct = sched.get('probability', 0.0)
    if spillover_pct > 50:
        sched_status = 'critical'
        sched_label = 'Delay Imminent'
        sched_sub_text = f"{spillover_pct:.0f}% chance of spillover. Sprint goal is in danger. Consider deferring or swapping."
    elif spillover_pct > 30:
        sched_status = 'warning'
        sched_label = 'Moderate Risk'
        sched_sub_text = f"{spillover_pct:.0f}% chance of spillover. Monitor closely and flag blockers early."
    else:
        sched_status = 'safe'
        sched_label = 'On Track'
        sched_sub_text = f"{spillover_pct:.0f}% chance of spillover. Likely to finish on time."

    display_schedule = {
        'value': f"{spillover_pct:.0f}% Probability of Spillover",
        'label': sched_label,
        'status': sched_status,
        'sub_text': sched_sub_text,
    }

    # PRODUCTIVITY
    raw_velocity_pct = prod.get('velocity_change', 0.0)
    days_lost = prod.get('days_lost', abs(raw_velocity_pct / 100.0) * days_remaining)
    velocity_drag_pct = (days_lost / days_remaining) * 100

    if velocity_drag_pct > 30:
        prod_status = 'critical'
        prod_label = 'High Drag'
        prod_sub_text = f"{days_lost:.1f} days lost to context switching. Team workflow disrupted — avoid adding mid-sprint."
    elif velocity_drag_pct > 10:
        prod_status = 'warning'
        prod_label = 'Noticeable Slowdown'
        prod_sub_text = f"{days_lost:.1f} days lost to context switching. Noticeable slowdown expected for the team."
    else:
        prod_status = 'safe'
        prod_label = 'Minimal Distraction'
        prod_sub_text = f"{days_lost:.1f} days lost to context switching. Minimal distraction to team velocity."

    display_productivity = {
        'value': f"-{velocity_drag_pct:.0f}% Velocity",
        'label': prod_label,
        'status': prod_status,
        'sub_text': prod_sub_text,
    }

    # QUALITY
    defect_pct = qual.get('probability', 0.0)
    if defect_pct > 60:
        qual_status = 'critical'
        qual_label = 'High Bug Risk'
        qual_sub_text = f"{defect_pct:.0f}% defect likelihood. Complex/rushed work — double QA time recommended."
    elif defect_pct > 30:
        qual_status = 'warning'
        qual_label = 'Elevated Risk'
        qual_sub_text = f"{defect_pct:.0f}% defect likelihood. Additional review cycle advised."
    else:
        qual_status = 'safe'
        qual_label = 'Standard Risk'
        qual_sub_text = f"{defect_pct:.0f}% defect likelihood. Standard testing required."

    display_quality = {
        'value': f"{defect_pct:.0f}% Defect Risk",
        'label': qual_label,
        'status': qual_status,
        'sub_text': qual_sub_text,
    }

    return {
        'effort': display_effort,
        'schedule': display_schedule,
        'productivity': display_productivity,
        'quality': display_quality,
    }


class ImpactPredictor:
    def __init__(self):
        self.models = model_loader.models

    def predict_all_impacts(self, item_data, sprint_context, existing_items=None):
        """Main prediction method - returns all impact analysis results"""
        sprint_context = self._enrich_context(sprint_context)

        # Get raw predictions
        effort = self._predict_effort(item_data, sprint_context)
        schedule = self._predict_schedule_risk(item_data, sprint_context)
        quality = self._predict_quality_risk(item_data, sprint_context)
        productivity = self._predict_productivity(item_data, sprint_context)
        
        # Generate summary
        summary = self._generate_summary(effort, schedule, quality, productivity)
        
        # Generate display metrics - THIS IS THE KEY LINE
        display = generate_display_metrics(effort, schedule, productivity, quality, sprint_context)
        
        # Extract features
        features = feature_engineer.extract_features(item_data, sprint_context)

        result = {
            'effort': effort,
            'schedule_risk': schedule,
            'quality_risk': quality,
            'productivity': productivity,
            'summary': summary,
            'display': display,  # CRITICAL: Must be included
            'features': features,
        }
        
        print(f"Impact prediction result keys: {result.keys()}")  # Debug log
        print(f"Display object present: {'display' in result}")  # Debug log
        
        return result

    def _enrich_context(self, ctx: dict) -> dict:
        """Add derived timing fields if missing"""
        from datetime import datetime
        ctx = dict(ctx)
        start = ctx.get('start_date')
        end = ctx.get('end_date')
        
        if start and end:
            if isinstance(start, str):
                start = datetime.strptime(start, '%Y-%m-%d')
            if isinstance(end, str):
                end = datetime.strptime(end, '%Y-%m-%d')
            now = datetime.utcnow()
            ctx['days_since_sprint_start'] = max(0, (now - start).days)
            ctx['days_remaining'] = max(0, (end - now).days)
            total = (end - start).days
            ctx['sprint_progress'] = ctx['days_since_sprint_start'] / max(1, total)
        else:
            ctx.setdefault('days_since_sprint_start', 0)
            ctx.setdefault('days_remaining', 14)
            ctx.setdefault('sprint_progress', 0.0)
        
        return ctx

    def _predict_effort(self, item_data, sprint_context) -> Dict:
        """Predict effort required in hours"""
        try:
            feat_dict = build_effort_features(item_data, sprint_context)
            df = pd.DataFrame([feat_dict])
            dmat = xgb.DMatrix(df)

            lower = float(self.models['effort_lower'].predict(dmat)[0])
            median = float(self.models['effort_median'].predict(dmat)[0])
            upper = float(self.models['effort_upper'].predict(dmat)[0])
            lower, upper = min(lower, median), max(upper, median)

            hours_remaining = sprint_context['days_remaining'] * WORK_HOURS_PER_DAY

            if median > hours_remaining:
                status = 'critical'
                label = 'Sprint Overload'
            elif median > hours_remaining * 0.8:
                status = 'warning'
                label = 'Tight Fit'
            else:
                status = 'safe'
                label = 'Fits in Sprint'

            return {
                'hours_lower': round(lower, 1),
                'hours_median': round(median, 1),
                'hours_upper': round(upper, 1),
                'hours_remaining': round(hours_remaining, 1),
                'status': status,
                'status_label': label,
                'explanation': f"Predicted {median:.1f}h vs {hours_remaining:.0f}h remaining.",
            }
        except Exception as e:
            print(f"Effort prediction error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_effort(item_data, sprint_context)

    def _predict_schedule_risk(self, item_data, sprint_context) -> Dict:
        """Predict schedule risk probability"""
        try:
            X = build_schedule_risk_features(item_data, sprint_context)
            model = self.models['schedule_risk']
            proba = model.predict_proba(X)[0]

            spillover_prob = float((proba[0] + proba[1]) * 100)
            dominant_idx = int(np.argmax(proba))
            dominant_label = SCHEDULE_LABEL_MAP.get(dominant_idx, 'Unknown')

            if spillover_prob > 50:
                status = 'critical'
                label = 'High Risk'
            elif spillover_prob > 30:
                status = 'warning'
                label = 'Moderate Risk'
            else:
                status = 'safe'
                label = 'Low Risk'

            return {
                'probability': round(spillover_prob, 1),
                'status': status,
                'status_label': label,
                'dominant_class': dominant_label,
                'explanation': f"Model: '{dominant_label}'. {spillover_prob:.0f}% spillover probability.",
            }
        except Exception as e:
            print(f"Schedule risk error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_schedule_risk(item_data, sprint_context)

    def _predict_quality_risk(self, item_data, sprint_context) -> Dict:
        """Predict quality/defect risk"""
        try:
            X = build_quality_features(item_data, sprint_context)
            model = self.models.get('quality_risk')
            
            if model is None:
                print("Quality risk model not loaded, using fallback")
                return self._fallback_quality_risk(item_data, sprint_context)
            
            proba = model.predict_proba(X)[0]
            defect_pct = float(proba[1]) * 100

            if defect_pct > 60:
                status = 'critical'
                label = 'High Bug Risk'
            elif defect_pct > 30:
                status = 'warning'
                label = 'Elevated Risk'
            else:
                status = 'safe'
                label = 'Standard Risk'

            return {
                'probability': round(defect_pct, 1),
                'status': status,
                'status_label': label,
                'explanation': f"{defect_pct:.0f}% defect likelihood.",
            }
        except Exception as e:
            print(f"Quality risk error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_quality_risk(item_data, sprint_context)

    def _predict_productivity(self, item_data, sprint_context) -> Dict:
        """Predict productivity impact"""
        try:
            X = build_productivity_features(
                item_data, sprint_context,
                scaler_mean=feature_engineer.scaler_mean,
                scaler_scale=feature_engineer.scaler_scale,
            )
            model = self.models['productivity']
            dmat = xgb.DMatrix(X)
            raw = float(model.predict(dmat)[0])

            raw = max(-1.0, min(1.0, raw))
            velocity_change = round(raw * 100, 1)

            days_remaining = max(1, sprint_context.get('days_remaining', 14))
            days_lost = round(abs(velocity_change / 100.0) * days_remaining, 2)

            if velocity_change < -30:
                status = 'critical'
                label = 'High Drag'
            elif velocity_change < -10:
                status = 'warning'
                label = 'Noticeable Slowdown'
            else:
                status = 'safe'
                label = 'Minimal Distraction'

            return {
                'velocity_change': velocity_change,
                'days_lost': days_lost,
                'days_remaining': days_remaining,
                'status': status,
                'status_label': label,
                'explanation': f"Velocity drag: {velocity_change:+.1f}% ({days_lost:.1f} days lost).",
            }
        except Exception as e:
            print(f"Productivity error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_productivity(item_data, sprint_context)

    def _generate_summary(self, effort, schedule, quality, productivity):
        """Generate overall risk summary"""
        score = 0
        
        if effort['status'] == 'critical': 
            score += 3
        elif effort['status'] == 'warning': 
            score += 2
        
        if schedule.get('probability', 0) > 50: 
            score += 3
        elif schedule.get('probability', 0) > 30: 
            score += 2
        
        if quality.get('probability', 0) > 60: 
            score += 2
        elif quality.get('probability', 0) > 30: 
            score += 1
        
        if productivity.get('velocity_change', 0) < -30: 
            score += 2
        elif productivity.get('velocity_change', 0) < -10: 
            score += 1

        if score >= 7:
            return {'risk_score': score, 'overall_risk': 'critical', 'recommendation': 'DEFER'}
        elif score >= 4:
            return {'risk_score': score, 'overall_risk': 'high', 'recommendation': 'SWAP'}
        elif score >= 2:
            return {'risk_score': score, 'overall_risk': 'medium', 'recommendation': 'SPLIT'}
        else:
            return {'risk_score': score, 'overall_risk': 'low', 'recommendation': 'ADD'}

    def _fallback_effort(self, item_data, sprint_context):
        """Fallback effort estimation"""
        h = item_data.get('story_points', 5) * 5
        hours_remaining = sprint_context.get('days_remaining', 14) * WORK_HOURS_PER_DAY
        status = 'critical' if h > hours_remaining else 'warning'
        return {
            'hours_lower': round(h * 0.8, 1),
            'hours_median': float(h),
            'hours_upper': round(h * 1.2, 1),
            'hours_remaining': float(hours_remaining),
            'status': status,
            'status_label': 'Sprint Overload' if status == 'critical' else 'Estimated',
            'explanation': 'Fallback: 5h per story point',
        }

    def _fallback_schedule_risk(self, item_data, sprint_context):
        """Fallback schedule risk estimation"""
        sp = item_data.get('story_points', 5)
        days = max(1, sprint_context.get('days_remaining', 14))
        risk = min(100.0, (sp / days) * 50)
        status = 'critical' if risk > 50 else ('warning' if risk > 30 else 'safe')
        label = 'High Risk' if status == 'critical' else ('Moderate Risk' if status == 'warning' else 'Low Risk')
        return {
            'probability': round(risk, 1),
            'status': status,
            'status_label': label,
            'dominant_class': 'N/A',
            'explanation': 'Fallback: story_points / days_remaining ratio',
        }

    def _fallback_quality_risk(self, item_data, sprint_context):
        """Fallback quality risk estimation"""
        return {
            'probability': 40.0,
            'status': 'warning',
            'status_label': 'Elevated Risk',
            'explanation': 'Fallback quality estimation',
        }

    def _fallback_productivity(self, item_data, sprint_context):
        """Fallback productivity estimation"""
        days_remaining = max(1, sprint_context.get('days_remaining', 14))
        return {
            'velocity_change': -10.0,
            'days_lost': round(0.1 * days_remaining, 2),
            'days_remaining': days_remaining,
            'status': 'warning',
            'status_label': 'Noticeable Slowdown',
            'explanation': 'Fallback productivity estimation',
        }


impact_predictor = ImpactPredictor()