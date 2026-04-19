"""
decision_engine.py
──────────────────────────────────────────────────────────────────────────────
Unified Decision Engine — Single source of truth for all sprint planning
and replanning decisions.

This replaces BOTH the old decision_engine.py (Phase 3 task decisions) AND
the old RecommendationEngine in recommendation_engine.py.

Why unified:
  - Old system had two parallel engines producing contradictory recommendations
    for the same ticket. The one logged to MongoDB and the one shown in the UI
    could differ. This caused history coherence problems.
  - Now: one engine, one decision, one log entry.

Two entry points:

  1. calculate_agile_recommendation(alignment_state, effort_sp, free_capacity,
                                    priority, risk_level)
     ── Phase 3 task decisions: ADD | DEFER | SPLIT | SWAP
     ── Called by POST /api/ai/decide
     ── ML risk is checked FIRST. High risk blocks ADD regardless of capacity.

  2. process_developer_exit(sprint_context, task_list, ml_metadata)
     ── Mid-Sprint Resource Attrition (MSR-A) replanning
     ── Called by POST /api/impact/developer-exit
     ── Uses Stability Buffer (80% utilization) math from the spec

Productivity saturation guard:
  If the productivity model raw log-space output > 4.5, the percentage number
  is suppressed and "VOLATILE" status is returned instead of a fabricated 99%.
"""

from __future__ import annotations
import math
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_ALIGNMENT_STATES = {
    "CRITICAL_BLOCKER",
    "STRONGLY_ALIGNED",
    "PARTIALLY_ALIGNED",
    "WEAKLY_ALIGNED",
    "UNALIGNED",
}

VALID_ACTIONS = {"ADD", "DEFER", "SPLIT", "SWAP", "ABSORB", "SWARM"}

# Productivity model: if raw log-space output > this, suppress the percentage
PRODUCTIVITY_SATURATION_THRESHOLD = 4.5

# Stability Buffer — 80% planned utilization means 20% kept free
DEFAULT_BUFFER_RATIO = 0.20

# Developer exit: minimum team size enforced at business logic level
MIN_TEAM_SIZE = 2


# ── Shared result class ───────────────────────────────────────────────────────

class DecisionResult:
    """
    Returned by both calculate_agile_recommendation() and
    process_developer_exit(). The to_dict() shape is consumed by FastAPI
    response models.
    """

    def __init__(
        self,
        action: str,
        rule_triggered: str,
        reasoning: str,
        short_title: str,
        extra: dict | None = None,
    ) -> None:
        self.action         = action
        self.rule_triggered = rule_triggered
        self.reasoning      = reasoning
        self.short_title    = short_title
        self.extra          = extra or {}   # capacity math, per-task decisions, etc.

    def to_dict(self) -> dict:
        d = {
            "action":         self.action,
            "rule_triggered": self.rule_triggered,
            "reasoning":      self.reasoning,
            "short_title":    self.short_title,
        }
        d.update(self.extra)
        return d


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT 1 — Task planning decisions (replaces old decision_engine.py)
# ══════════════════════════════════════════════════════════════════════════════

def calculate_agile_recommendation(
    alignment_state: str,
    effort_sp: int | float,
    free_capacity: int | float,
    priority: str,
    risk_level: str,
) -> DecisionResult:
    """
    Priority-ordered rule engine for single-ticket sprint decisions.

    KEY CHANGE from old engine:
      ML risk is now checked BEFORE capacity. Previously Rule 5 (Perfect Fit)
      could return ADD for a STRONGLY_ALIGNED ticket even when risk_level was
      HIGH, because capacity was checked first and risk was only used in Rule 2.
      Now: HIGH risk with non-critical priority always routes to DEFER or SPLIT
      regardless of available capacity, making ML predictions non-decorative.

    Rules (first match wins):
      Rule 1  — Emergency (CRITICAL_BLOCKER): ADD if fits, SWAP if not
      Rule 2a — Scope creep (UNALIGNED): DEFER
      Rule 2b — High risk + low/medium priority: DEFER  ← now fires before capacity check
      Rule 2c — High risk + high/critical priority + aligned: SPLIT ← new
      Rule 3a — Aligned but oversized (> 8 SP): SPLIT
      Rule 3b — Partial/Weak + exceeds capacity: SPLIT
      Rule 4  — Strongly aligned + high priority + exceeds capacity: SWAP
      Rule 5  — Aligned + fits capacity + acceptable risk: ADD
      Rule 6  — Catch-all: DEFER
    """
    state    = (alignment_state or "UNALIGNED").strip().upper()
    prio     = (priority or "Medium").strip().capitalize()
    risk     = (risk_level or "LOW").strip().upper()
    effort   = float(effort_sp)
    capacity = float(free_capacity)
    fits     = effort <= capacity

    # ── Rule 1: Emergency ────────────────────────────────────────────────────
    if state == "CRITICAL_BLOCKER":
        if fits:
            return DecisionResult(
                action         = "ADD",
                rule_triggered = "Rule 1a — Emergency / fits capacity",
                reasoning      = (
                    f"Critical blocker — estimated {effort:.0f} SP fits within "
                    f"{capacity:.0f} SP remaining. Pull in immediately."
                ),
                short_title    = "🚨 Critical Blocker — Add Now",
            )
        return DecisionResult(
            action         = "SWAP",
            rule_triggered = "Rule 1b — Emergency / exceeds capacity",
            reasoning      = (
                f"Critical blocker — {effort:.0f} SP exceeds {capacity:.0f} SP remaining. "
                "Remove a lower-priority item to make room."
            ),
            short_title    = "🚨 Critical Blocker — Swap Required",
        )

    # ── Rule 2a: Scope creep ─────────────────────────────────────────────────
    if state == "UNALIGNED":
        return DecisionResult(
            action         = "DEFER",
            rule_triggered = "Rule 2a — Unaligned / scope creep",
            reasoning      = (
                "This ticket is semantically unaligned with the sprint goal. "
                "Adding it would dilute the team's focus. Defer to the backlog."
            ),
            short_title    = "🚫 Out of Scope — Defer",
        )

    # ── Rule 2b: High risk + low/medium priority (ML now blocks ADD) ─────────
    # CHANGE: This used to only fire when state was UNALIGNED too. Now it fires
    # for any aligned state when risk is HIGH and priority doesn't justify it.
    if risk == "HIGH" and prio in ("Low", "Medium"):
        return DecisionResult(
            action         = "DEFER",
            rule_triggered = "Rule 2b — High risk + low/medium priority",
            reasoning      = (
                f"ML models indicate HIGH risk but priority is only {prio}. "
                "The risk-to-value ratio does not justify inclusion now. "
                "Refine and reschedule for a lower-pressure sprint."
            ),
            short_title    = "⚠️ High Risk, Low Priority — Defer",
        )

    # ── Rule 2c: High risk + high priority + aligned → SPLIT not ADD ─────────
    # CHANGE: Previously, STRONGLY_ALIGNED + HIGH risk + fits capacity → ADD.
    # That made ML predictions "decorative". Now high risk forces SPLIT so the
    # team delivers only the safest slice this sprint.
    if risk == "HIGH" and prio in ("High", "Critical") and state in (
        "STRONGLY_ALIGNED", "PARTIALLY_ALIGNED"
    ):
        return DecisionResult(
            action         = "SPLIT",
            rule_triggered = "Rule 2c — High risk + high priority + aligned",
            reasoning      = (
                f"Ticket is {state.replace('_', ' ').title()} and priority is {prio}, "
                "but ML models flag HIGH risk. Split into a safe analysis slice "
                "(add this sprint) and an implementation slice (next sprint) "
                "to preserve sprint stability."
            ),
            short_title    = "✂️ High Risk — Split Required",
        )

    # ── Rule 3a: Aligned but oversized ───────────────────────────────────────
    if state in ("STRONGLY_ALIGNED", "PARTIALLY_ALIGNED") and effort > 8:
        return DecisionResult(
            action         = "SPLIT",
            rule_triggered = "Rule 3a — Aligned but oversized (> 8 SP)",
            reasoning      = (
                f"Ticket is {state.replace('_', ' ').title()} but at {effort:.0f} SP "
                "it is too large for healthy Agile flow. Break into slices ≤ 5 SP."
            ),
            short_title    = "✂️ Aligned but Too Large — Split",
        )

    # ── Rule 3b: Partial/Weak + exceeds capacity ──────────────────────────────
    if state in ("PARTIALLY_ALIGNED", "WEAKLY_ALIGNED") and not fits:
        return DecisionResult(
            action         = "SPLIT",
            rule_triggered = "Rule 3b — Partially/Weakly aligned + exceeds capacity",
            reasoning      = (
                f"Ticket is {state.replace('_', ' ').title()} and {effort:.0f} SP "
                f"exceeds the {capacity:.0f} SP remaining. Extract the minimum viable "
                "slice that fits and defer the rest."
            ),
            short_title    = "✂️ Exceeds Capacity — Split",
        )

    # ── Rule 4: Urgent trade-off ──────────────────────────────────────────────
    if state == "STRONGLY_ALIGNED" and not fits and prio in ("High", "Critical"):
        return DecisionResult(
            action         = "SWAP",
            rule_triggered = "Rule 4 — Strongly aligned + high priority + exceeds capacity",
            reasoning      = (
                f"STRONGLY_ALIGNED and {prio} priority but {effort:.0f} SP exceeds "
                f"{capacity:.0f} SP. Swap out a lower-priority item — the strategic "
                "value justifies the trade-off."
            ),
            short_title    = "🔄 High Priority — Swap",
        )

    # ── Rule 5: Perfect fit ───────────────────────────────────────────────────
    if state in ("STRONGLY_ALIGNED", "PARTIALLY_ALIGNED") and fits:
        return DecisionResult(
            action         = "ADD",
            rule_triggered = "Rule 5 — Aligned + fits capacity + acceptable risk",
            reasoning      = (
                f"Ticket is {state.replace('_', ' ').title()}, estimated {effort:.0f} SP "
                f"fits within {capacity:.0f} SP remaining, and risk level is {risk}. "
                "Safe to add to the sprint backlog."
            ),
            short_title    = "✅ Good Fit — Add to Sprint",
        )

    # ── Rule 6: Catch-all ─────────────────────────────────────────────────────
    return DecisionResult(
        action         = "DEFER",
        rule_triggered = "Rule 6 — Catch-all fallback",
        reasoning      = (
            f"No specific rule matched (state={state}, effort={effort:.0f} SP, "
            f"capacity={capacity:.0f} SP, priority={prio}, risk={risk}). "
            "Defaulting to DEFER to protect sprint integrity."
        ),
        short_title    = "⏸ Defer — No Matching Rule",
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT 2 — Developer exit replanning (Mid-Sprint Resource Attrition)
# ══════════════════════════════════════════════════════════════════════════════

def process_developer_exit(
    sprint_context: dict,
    task_list: list[dict],
    ml_metadata: dict | None = None,
) -> dict:
    """
    MSR-A: Mid-Sprint Resource Attrition replanning.

    sprint_context keys:
      total_points       : int   — total SP committed at sprint start
      remaining_points   : int   — SP not yet completed
      original_devs      : int   — dev count when sprint was planned
      active_devs        : int   — dev count after the exit (≥ MIN_TEAM_SIZE)
      buffer_ratio       : float — default 0.20 (20% stability buffer)

    task_list: list of dicts with keys:
      id, title, story_points, priority, alignment, status

    ml_metadata: dict keyed by task id:
      { task_id: { schedule_risk: float 0-1, quality_risk: float 0-1 } }

    Returns a dict with:
      capacity_analysis  : normalized_capacity, safe_threshold, deficit, verdict
      per_task_decisions : list of { task_id, title, action, reason, rule }
      overall_strategy   : summary string
      severity           : "LOW" | "HIGH" | "CRITICAL"
    """
    ml_metadata = ml_metadata or {}

    original_devs = max(1, int(sprint_context.get("original_devs", 1)))
    active_devs   = max(MIN_TEAM_SIZE, int(sprint_context.get("active_devs", MIN_TEAM_SIZE)))
    total_points  = float(sprint_context.get("total_points", 0))
    remaining_sp  = float(sprint_context.get("remaining_points", total_points))
    buffer_ratio  = float(sprint_context.get("buffer_ratio", DEFAULT_BUFFER_RATIO))

    # ── Capacity math (from spec) ─────────────────────────────────────────────
    # If 5 devs planned 50 SP, each dev = 10 SP of capacity.
    # 4 active devs → normalized_capacity = 40 SP.
    normalized_capacity = (total_points / original_devs) * active_devs
    safe_threshold      = normalized_capacity * (1.0 - buffer_ratio)
    deficit             = max(0.0, remaining_sp - safe_threshold)
    absorb_possible     = remaining_sp <= safe_threshold

    severity = "LOW" if absorb_possible else (
        "CRITICAL" if deficit > normalized_capacity * 0.3 else "HIGH"
    )

    capacity_analysis = {
        "original_devs":        original_devs,
        "active_devs":          active_devs,
        "total_points":         total_points,
        "remaining_points":     remaining_sp,
        "normalized_capacity":  round(normalized_capacity, 1),
        "safe_threshold":       round(safe_threshold, 1),
        "deficit_sp":           round(deficit, 1),
        "buffer_ratio":         buffer_ratio,
        "absorb_possible":      absorb_possible,
        "severity":             severity,
    }

    # ── Per-task decisions ────────────────────────────────────────────────────
    per_task_decisions = []

    for task in task_list:
        task_id    = task.get("id", "")
        task_ml    = ml_metadata.get(task_id, {})
        sched_risk = float(task_ml.get("schedule_risk", 0.0))
        alignment  = (task.get("alignment") or "MEDIUM").upper()
        priority   = (task.get("priority")  or "Medium").capitalize()
        status     = (task.get("status")    or "To Do")
        sp         = float(task.get("story_points", 0))

        # Skip already-done tasks
        if status == "Done":
            per_task_decisions.append({
                "task_id": task_id,
                "title":   task.get("title", ""),
                "action":  "KEEP",
                "reason":  "Already completed. No action needed.",
                "rule":    "Rule 0 — Done items are untouched",
            })
            continue

        # Rule 1: Critical ML risk — cannot absorb even if buffer allows it
        if sched_risk > 0.85:
            per_task_decisions.append({
                "task_id": task_id,
                "title":   task.get("title", ""),
                "action":  "SPLIT",
                "reason":  (
                    f"Schedule risk {sched_risk:.0%} is above 85% threshold. "
                    "Even with available capacity, this task is too risky to absorb whole. "
                    "Split: deliver analysis slice this sprint, implementation next sprint."
                ),
                "rule":    "Rule 1 — Critical ML risk override (> 85% schedule risk)",
            })
            continue

        # Rule 2: Buffer can absorb the remaining work — no descoping needed
        if absorb_possible:
            per_task_decisions.append({
                "task_id": task_id,
                "title":   task.get("title", ""),
                "action":  "ABSORB",
                "reason":  (
                    f"Remaining {remaining_sp:.0f} SP ≤ safe threshold {safe_threshold:.0f} SP. "
                    f"The {int(buffer_ratio * 100)}% stability buffer absorbs the exit. "
                    "Sprint goal can be maintained without descoping."
                ),
                "rule":    "Rule 2 — Buffer absorption (remaining SP within safe threshold)",
            })
            continue

        # Rule 3: Forced descoping — remove low-value tasks first
        if alignment in ("LOW", "UNALIGNED") or priority in ("Low",):
            per_task_decisions.append({
                "task_id": task_id,
                "title":   task.get("title", ""),
                "action":  "DEFER",
                "reason":  (
                    f"Capacity overload after developer exit (deficit: {deficit:.0f} SP). "
                    f"This task has {alignment} alignment and {priority} priority — "
                    "removing it first to protect high-value sprint commitments."
                ),
                "rule":    "Rule 3 — Forced descoping (low alignment or low priority)",
            })
            continue

        # Rule 4: High-value task — remaining team must swarm to complete it
        per_task_decisions.append({
            "task_id": task_id,
            "title":   task.get("title", ""),
            "action":  "SWARM",
            "reason":  (
                f"High-value task ({alignment} alignment, {priority} priority). "
                "Remaining team should swarm — pair program, reduce WIP, "
                "and focus collective effort to deliver this sprint commitment."
            ),
            "rule":    "Rule 4 — High-value swarming",
        })

    # ── Overall strategy summary ──────────────────────────────────────────────
    action_counts = {}
    for d in per_task_decisions:
        action_counts[d["action"]] = action_counts.get(d["action"], 0) + 1

    if absorb_possible:
        overall_strategy = (
            f"Developer exit absorbed by stability buffer. "
            f"Normalized capacity: {normalized_capacity:.0f} SP. "
            f"Remaining work ({remaining_sp:.0f} SP) is within the safe threshold "
            f"({safe_threshold:.0f} SP). Sprint goal is intact."
        )
    elif severity == "CRITICAL":
        deferred = action_counts.get("DEFER", 0)
        overall_strategy = (
            f"CRITICAL capacity deficit of {deficit:.0f} SP. "
            f"Descoping {deferred} task(s) and swarming on remaining commitments. "
            f"Sprint goal may need renegotiation with stakeholders."
        )
    else:
        overall_strategy = (
            f"HIGH impact exit. {deficit:.0f} SP deficit. "
            f"Swarming on high-value tasks, deferring low-priority work. "
            "Consider pulling in a contractor or renegotiating one deliverable."
        )

    return {
        "capacity_analysis":  capacity_analysis,
        "per_task_decisions": per_task_decisions,
        "overall_strategy":   overall_strategy,
        "severity":           severity,
        "action_summary":     action_counts,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Productivity saturation guard (used by impact_routes.py)
# ══════════════════════════════════════════════════════════════════════════════

def check_productivity_saturation(raw_log_output: float) -> dict:
    """
    If the productivity model's raw log-space output exceeds the saturation
    threshold (4.5), the percentage number is no longer meaningful.

    Returns:
      { saturated: bool, drop_pct: float | None, status: str, display_value: str }

    OLD behaviour: exp(raw) was capped at 99.0 and shown as "-99% Drop"
    NEW behaviour: if saturated, show "VOLATILE" instead of a fake percentage
    """
    if raw_log_output > PRODUCTIVITY_SATURATION_THRESHOLD:
        return {
            "saturated":     True,
            "drop_pct":      None,
            "status":        "critical",
            "display_value": "VOLATILE",
            "sub_text": (
                "Workload exceeds model prediction limits. "
                "The situation is severe enough that a percentage is no longer accurate. "
                "Immediate sprint replanning is recommended."
            ),
        }

    drop_pct = min(99.0, float(math.exp(raw_log_output)))
    if drop_pct > 30:
        status = "critical"
    elif drop_pct > 10:
        status = "warning"
    else:
        status = "safe"

    return {
        "saturated":     False,
        "drop_pct":      round(drop_pct, 1),
        "status":        status,
        "display_value": f"-{drop_pct:.0f}% Drop",
        "sub_text":      None,
    }