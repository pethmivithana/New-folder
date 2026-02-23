"""
explanation_generator.py
─────────────────────────
Converts raw RecommendationEngine output into polished, user-facing
explanations for the Agile Replanning Dashboard.

Supports all four action types: ADD, SWAP, DEFER, SPLIT.
Returns a typed dict with `short_title`, `detailed_explanation`,
`confidence_color`, and supplementary metadata.
"""

from __future__ import annotations

from typing import TypedDict


# ──────────────────────────────────────────────────────────────────────────────
# Return type
# ──────────────────────────────────────────────────────────────────────────────

class ExplanationResult(TypedDict):
    short_title:          str   # ≤ 60 chars – shown as card headline
    detailed_explanation: str   # full paragraph shown in expanded view
    confidence_color:     str   # "green" | "yellow" | "red"
    action_verb:          str   # imperative verb for the CTA button
    icon:                 str   # emoji icon for the action card
    risk_summary:         str   # one-liner risk breakdown


# ──────────────────────────────────────────────────────────────────────────────
# Helper: derive confidence colour from risk signals
# ──────────────────────────────────────────────────────────────────────────────

def _confidence_color(
    schedule_risk: float,
    quality_risk:  float,
    velocity_change: float,
) -> str:
    """
    Map combined risk signals to a traffic-light colour.

    green  → safe to proceed with minor caveats
    yellow → noticeable risk; action advised but not critical
    red    → critical risk; strong intervention required
    """
    if schedule_risk > 55 or quality_risk > 60 or velocity_change < -30:
        return "red"
    if schedule_risk > 30 or quality_risk > 30 or velocity_change < -10:
        return "yellow"
    return "green"


def _fmt_pct(value: float, *, decimals: int = 0) -> str:
    return f"{value:.{decimals}f}%"


def _fmt_sp(sp: int | float) -> str:
    sp = int(round(sp))
    return f"{sp} SP"


# ──────────────────────────────────────────────────────────────────────────────
# Per-action explanation builders
# ──────────────────────────────────────────────────────────────────────────────

def _explain_add(data: dict, risk_scores: dict, color: str) -> ExplanationResult:
    sp   = data.get("story_points", "?")
    free = risk_scores.get("free_capacity", "?")

    return ExplanationResult(
        short_title          = "✅ Safe to Add to Sprint",
        detailed_explanation = (
            f"The sprint has sufficient capacity ({free} SP available) to absorb this "
            f"{_fmt_sp(sp)} ticket without disrupting velocity or schedule. "
            f"Schedule risk is low ({_fmt_pct(risk_scores.get('schedule_risk', 0))}), "
            f"defect probability is within acceptable limits "
            f"({_fmt_pct(risk_scores.get('quality_risk', 0))}), and the team's "
            f"productivity impact is negligible. Proceed with confidence."
        ),
        confidence_color = color,
        action_verb      = "Add to Sprint",
        icon             = "✅",
        risk_summary     = (
            f"Schedule: {_fmt_pct(risk_scores.get('schedule_risk', 0))} · "
            f"Quality: {_fmt_pct(risk_scores.get('quality_risk', 0))} · "
            f"Velocity: {risk_scores.get('velocity_change', 0):+.0f}%"
        ),
    )


def _explain_swap(data: dict, risk_scores: dict, target: dict | None, color: str) -> ExplanationResult:
    new_title    = data.get("title", "this ticket")
    new_sp       = data.get("story_points", "?")
    target_title = (target or {}).get("title", "a lower-priority ticket")
    target_sp    = (target or {}).get("story_points", "?")
    target_prio  = (target or {}).get("priority", "lower-priority")

    return ExplanationResult(
        short_title = f"🔄 Swap with '{target_title}'",
        detailed_explanation = (
            f"The sprint is currently at or near capacity. To accommodate "
            f"'{new_title}' ({_fmt_sp(new_sp)}), the engine recommends swapping it "
            f"with '{target_title}' ({_fmt_sp(target_sp)}, priority: {target_prio}). "
            f"This keeps the sprint's total story-point load neutral while prioritising "
            f"higher-value work. "
            f"The displaced ticket will be moved back to the backlog and re-planned in "
            f"the next sprint. "
            f"Expected schedule risk after the swap: "
            f"{_fmt_pct(risk_scores.get('schedule_risk', 0))}."
        ),
        confidence_color = color,
        action_verb      = "Execute Swap",
        icon             = "🔄",
        risk_summary     = (
            f"Capacity freed by swap: {_fmt_sp(target_sp)} · "
            f"Net load change: 0 SP · "
            f"Velocity impact: {risk_scores.get('velocity_change', 0):+.0f}%"
        ),
    )


def _explain_defer(data: dict, risk_scores: dict, color: str) -> ExplanationResult:
    new_title     = data.get("title", "this ticket")
    sched_risk    = risk_scores.get("schedule_risk", 0)
    quality_risk  = risk_scores.get("quality_risk", 0)
    vel_change    = risk_scores.get("velocity_change", 0)
    days_left     = risk_scores.get("days_remaining", "?")

    # Identify the primary risk driver for the explanation
    if sched_risk >= quality_risk and sched_risk >= abs(vel_change):
        primary_risk = f"schedule risk is critically high ({_fmt_pct(sched_risk)})"
    elif quality_risk >= abs(vel_change):
        primary_risk = f"defect probability is elevated ({_fmt_pct(quality_risk)})"
    else:
        primary_risk = f"adding this work will drag team velocity by {vel_change:+.0f}%"

    return ExplanationResult(
        short_title = f"⏸ Defer to Next Sprint",
        detailed_explanation = (
            f"Adding '{new_title}' to the current sprint is not recommended because "
            f"{primary_risk}. "
            f"With only {days_left} day(s) remaining and the sprint already under "
            f"pressure, introducing new scope now creates a high probability of "
            f"missing the sprint goal. "
            f"Deferring to the next sprint allows the team to plan properly, "
            f"allocate sufficient capacity, and deliver the work with higher quality. "
            f"Schedule risk: {_fmt_pct(sched_risk)} · "
            f"Quality risk: {_fmt_pct(quality_risk)}."
        ),
        confidence_color = color,
        action_verb      = "Defer to Backlog",
        icon             = "⏸",
        risk_summary     = (
            f"Schedule risk: {_fmt_pct(sched_risk)} · "
            f"Quality risk: {_fmt_pct(quality_risk)} · "
            f"Days remaining: {days_left}"
        ),
    )


def _explain_split(data: dict, risk_scores: dict, color: str) -> ExplanationResult:
    """
    Implements the 'Elephant Protocol':
    Large tickets (≥ 8 SP) are split into an Analysis slice and an
    Implementation slice so neither fragment overloads the sprint.
    """
    new_title = data.get("title", "this ticket")
    total_sp  = int(data.get("story_points", 13))

    # Split ratio: 30 % analysis, 70 % implementation (minimum 1 SP each)
    analysis_sp = max(1, round(total_sp * 0.30))
    impl_sp     = total_sp - analysis_sp

    return ExplanationResult(
        short_title = f"✂️ Split Required — Elephant Protocol",
        detailed_explanation = (
            f"'{new_title}' is too large ({_fmt_sp(total_sp)}) to fit safely into "
            f"the remaining sprint capacity. Adding it as-is risks schedule spillover "
            f"({_fmt_pct(risk_scores.get('schedule_risk', 0))}) and elevated defect "
            f"rates ({_fmt_pct(risk_scores.get('quality_risk', 0))}) because large "
            f"tickets accumulate context-switching overhead and are harder to test "
            f"thoroughly under time pressure. "
            f"Apply the Elephant Protocol: "
            f"(1) '{new_title} — Analysis & Design' ({_fmt_sp(analysis_sp)}) — "
            f"spike, research, and acceptance criteria refinement, completable this sprint; "
            f"(2) '{new_title} — Implementation' ({_fmt_sp(impl_sp)}) — "
            f"full development and QA, planned for the next sprint. "
            f"This approach preserves sprint commitments while maintaining delivery momentum."
        ),
        confidence_color = color,
        action_verb      = "Split Ticket",
        icon             = "✂️",
        risk_summary     = (
            f"Original size: {_fmt_sp(total_sp)} · "
            f"Analysis slice: {_fmt_sp(analysis_sp)} · "
            f"Implementation slice: {_fmt_sp(impl_sp)}"
        ),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Public utility class
# ──────────────────────────────────────────────────────────────────────────────

class ExplanationGenerator:
    """
    Converts raw RecommendationEngine output into user-facing explanations.

    Usage
    -----
    >>> gen = ExplanationGenerator()
    >>> explanation = gen.generate_explanation(recommendation_data)
    >>> print(explanation["short_title"])
    """

    def generate_explanation(self, recommendation_data: dict) -> ExplanationResult:
        """
        Parameters
        ----------
        recommendation_data : dict
            Expected keys:
              - recommendation_type : str   ("ADD" | "SWAP" | "DEFER" | "SPLIT")
              - reasoning           : str   (raw engine reasoning text)
              - target_ticket       : dict | None  (present for SWAP actions)
              - impact_analysis     : dict  (raw ML numbers)
              - action_plan         : dict  (optional engine action plan)

            The ``impact_analysis`` sub-dict should contain:
              - schedule_risk    : float  (0–100)
              - quality_risk     : float  (0–100)
              - velocity_change  : float  (negative = slowdown %)
              - days_remaining   : int | float
              - free_capacity    : float  (SP, optional)

        Returns
        -------
        ExplanationResult
        """
        action      : str        = (recommendation_data.get("recommendation_type") or "ADD").upper()
        target      : dict | None = recommendation_data.get("target_ticket")
        impact      : dict        = recommendation_data.get("impact_analysis") or {}
        work_item   : dict        = recommendation_data.get("work_item_data") or {}

        # Normalise risk scores ─────────────────────────────────────────────
        risk_scores: dict = {
            "schedule_risk":  float(impact.get("schedule_risk",   0)),
            "quality_risk":   float(impact.get("quality_risk",    0)),
            "velocity_change": float(impact.get("velocity_change", 0)),
            "days_remaining": impact.get("days_remaining", "?"),
            "free_capacity":  impact.get("free_capacity",  "?"),
        }

        color = _confidence_color(
            risk_scores["schedule_risk"],
            risk_scores["quality_risk"],
            risk_scores["velocity_change"],
        )

        # Dispatch to per-action builder ────────────────────────────────────
        match action:
            case "ADD" | "ACCEPT":
                return _explain_add(work_item, risk_scores, color)
            case "SWAP":
                return _explain_swap(work_item, risk_scores, target, color)
            case "DEFER":
                return _explain_defer(work_item, risk_scores, color)
            case "SPLIT":
                return _explain_split(work_item, risk_scores, color)
            case _:
                # Graceful fallback for unknown action types
                return ExplanationResult(
                    short_title          = f"ℹ️ Recommendation: {action}",
                    detailed_explanation = recommendation_data.get("reasoning", "No details available."),
                    confidence_color     = "yellow",
                    action_verb          = "Review",
                    icon                 = "ℹ️",
                    risk_summary         = "No risk data available.",
                )


# ──────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ──────────────────────────────────────────────────────────────────────────────

explanation_generator = ExplanationGenerator()