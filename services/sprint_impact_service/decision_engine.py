"""
decision_engine.py
──────────────────────────────────────────────────────────────────────────────
Phase 3 – Agile Replanning Decision Engine.

Takes Phase 1 (alignment_state) + Phase 2 (effort_sp, risk_level)
+ current sprint capacity to produce one of: ADD | DEFER | SPLIT | SWAP.

All rules are deterministic; same inputs always produce the same output.
Rules are evaluated in strict priority order (highest = first match wins).
"""

from __future__ import annotations


# ── Types ─────────────────────────────────────────────────────────────────────

VALID_ALIGNMENT_STATES = {
    "CRITICAL_BLOCKER",
    "STRONGLY_ALIGNED",
    "PARTIALLY_ALIGNED",
    "WEAKLY_ALIGNED",
    "UNALIGNED",
}

VALID_ACTIONS = {"ADD", "DEFER", "SPLIT", "SWAP"}


# ── Decision result dataclass ─────────────────────────────────────────────────

class DecisionResult:
    """Returned by calculate_agile_recommendation()."""

    def __init__(
        self,
        action: str,
        rule_triggered: str,
        reasoning: str,
        short_title: str,
    ) -> None:
        self.action         = action           # ADD | DEFER | SPLIT | SWAP
        self.rule_triggered = rule_triggered   # human-readable rule name
        self.reasoning      = reasoning        # full explanation for the UI
        self.short_title    = short_title      # one-line label for the card header

    def to_dict(self) -> dict:
        return {
            "action":          self.action,
            "rule_triggered":  self.rule_triggered,
            "reasoning":       self.reasoning,
            "short_title":     self.short_title,
        }


# ── Main entry point ──────────────────────────────────────────────────────────

def calculate_agile_recommendation(
    alignment_state: str,
    effort_sp: int | float,
    free_capacity: int | float,
    priority: str,
    risk_level: str,
) -> DecisionResult:
    """
    Priority-ordered rule engine.  First matching rule wins.

    Parameters
    ----------
    alignment_state : str
        One of CRITICAL_BLOCKER | STRONGLY_ALIGNED | PARTIALLY_ALIGNED |
        WEAKLY_ALIGNED | UNALIGNED  (from Phase 1 endpoint).
    effort_sp : int | float
        Estimated story-point effort for the ticket (from Phase 2 TabNet model).
    free_capacity : int | float
        Remaining story points available in the current sprint
        (team_velocity - current_load).
    priority : str
        Ticket priority: "Low" | "Medium" | "High" | "Critical".
    risk_level : str
        Aggregate risk from Phase 2 models: "LOW" | "MEDIUM" | "HIGH".

    Returns
    -------
    DecisionResult
    """
    # Normalise inputs so comparisons are case-insensitive
    state    = (alignment_state or "UNALIGNED").strip().upper()
    prio     = (priority or "Medium").strip().capitalize()   # "Low" / "Medium" / "High" / "Critical"
    risk     = (risk_level or "LOW").strip().upper()
    effort   = float(effort_sp)
    capacity = float(free_capacity)

    fits = effort <= capacity

    # ── Rule 1 · The Emergency (highest priority) ─────────────────────────────
    if state == "CRITICAL_BLOCKER":
        if fits:
            return DecisionResult(
                action         = "ADD",
                rule_triggered = "Rule 1a — Emergency / fits capacity",
                reasoning      = (
                    f"This ticket is flagged as a CRITICAL BLOCKER. "
                    f"The estimated effort ({effort:.0f} SP) fits within the remaining sprint "
                    f"capacity ({capacity:.0f} SP free). Pull it in immediately."
                ),
                short_title    = "🚨 Critical Blocker — Add Now",
            )
        else:
            return DecisionResult(
                action         = "SWAP",
                rule_triggered = "Rule 1b — Emergency / exceeds capacity",
                reasoning      = (
                    f"This ticket is a CRITICAL BLOCKER but its estimated effort "
                    f"({effort:.0f} SP) exceeds available sprint capacity ({capacity:.0f} SP). "
                    "You must remove a lower-priority item to make room for it."
                ),
                short_title    = "🚨 Critical Blocker — Swap Required",
            )

    # ── Rule 2 · Scope Creep / High Risk ─────────────────────────────────────
    if state == "UNALIGNED":
        return DecisionResult(
            action         = "DEFER",
            rule_triggered = "Rule 2a — Unaligned / scope creep",
            reasoning      = (
                "This ticket is semantically UNALIGNED with the sprint goal. "
                "Adding it would constitute scope creep and dilute the team's focus. "
                "Defer to the product backlog for a future sprint whose goal matches."
            ),
            short_title    = "🚫 Out of Scope — Defer",
        )

    if risk == "HIGH" and prio in ("Low", "Medium"):
        return DecisionResult(
            action         = "DEFER",
            rule_triggered = "Rule 2b — High risk + low/medium priority",
            reasoning      = (
                f"Risk level is HIGH but ticket priority is only {prio}. "
                "The risk-to-value ratio does not justify inclusion in the current sprint. "
                "Defer and refine the ticket before committing it to a sprint."
            ),
            short_title    = "⚠️ High Risk, Low Priority — Defer",
        )

    # ── Rule 3 · The Monster Ticket ───────────────────────────────────────────
    if state in ("STRONGLY_ALIGNED", "PARTIALLY_ALIGNED") and effort > 8:
        return DecisionResult(
            action         = "SPLIT",
            rule_triggered = "Rule 3a — Aligned but oversized (> 8 SP)",
            reasoning      = (
                f"The ticket is {state.replace('_', ' ').title()} with the sprint goal, "
                f"but at {effort:.0f} SP it is too large for healthy Agile flow. "
                "Break it into smaller deliverable slices (ideally ≤ 5 SP each) "
                "so value can be shipped incrementally within the sprint."
            ),
            short_title    = "✂️ Aligned but Too Large — Split",
        )

    if state in ("PARTIALLY_ALIGNED", "WEAKLY_ALIGNED") and not fits:
        return DecisionResult(
            action         = "SPLIT",
            rule_triggered = "Rule 3b — Partially/Weakly aligned + exceeds capacity",
            reasoning      = (
                f"The ticket is {state.replace('_', ' ').title()} and its effort "
                f"({effort:.0f} SP) exceeds the remaining sprint capacity ({capacity:.0f} SP free). "
                "Extract only the minimum-viable slice that fits remaining capacity "
                "and defer the rest to the next sprint."
            ),
            short_title    = "✂️ Exceeds Capacity — Split",
        )

    # ── Rule 4 · The Urgent Trade-off ─────────────────────────────────────────
    if state == "STRONGLY_ALIGNED" and not fits and prio in ("High", "Critical"):
        return DecisionResult(
            action         = "SWAP",
            rule_triggered = "Rule 4 — Strongly aligned + high priority + exceeds capacity",
            reasoning      = (
                f"This ticket is STRONGLY ALIGNED with the sprint goal and is marked "
                f"{prio} priority, but at {effort:.0f} SP it exceeds the {capacity:.0f} SP "
                "remaining. Swap out a lower-priority item to make room for it — "
                "the strategic value justifies the trade-off."
            ),
            short_title    = "🔄 High Priority — Swap",
        )

    # ── Rule 5 · The Perfect Fit (default success) ────────────────────────────
    if state in ("STRONGLY_ALIGNED", "PARTIALLY_ALIGNED") and fits:
        return DecisionResult(
            action         = "ADD",
            rule_triggered = "Rule 5 — Aligned + fits capacity",
            reasoning      = (
                f"The ticket is {state.replace('_', ' ').title()} with the sprint goal "
                f"and its estimated effort ({effort:.0f} SP) fits within the remaining "
                f"capacity ({capacity:.0f} SP free). Safe to add to the sprint backlog."
            ),
            short_title    = "✅ Good Fit — Add to Sprint",
        )

    # ── Rule 6 · Catch-all ────────────────────────────────────────────────────
    return DecisionResult(
        action         = "DEFER",
        rule_triggered = "Rule 6 — Catch-all fallback",
        reasoning      = (
            f"No specific rule matched for alignment_state='{state}', "
            f"effort={effort:.0f} SP, capacity={capacity:.0f} SP, "
            f"priority={prio}, risk={risk}. "
            "Defaulting to DEFER to protect the current sprint's integrity."
        ),
        short_title    = "⏸ Defer — No Matching Rule",
    )