"""
recommendation_engine.py                     EXISTING FILE — replace fully
──────────────────────────────────────────────────────────────────────────────
Fixes vs previous version:
  BUG 1 — Mock active items
    The old code contained a hardcoded `mock_active_items` list with fake
    tickets ("Legacy API Update", "Database Migration") inside a wrapper
    function.  These were used whenever real items were unavailable.

    Fix: Removed entirely.  `active_items` must always come from the DB via
    `get_backlog_items_by_sprint()`.  If the sprint genuinely has no items,
    the list is empty and the engine handles it gracefully (no swap possible
    → DEFER).

  BUG 2 — "AI Safety Net" was ignored (Rule 5 violation)
    The old code checked capacity BEFORE checking ML schedule risk, so a
    sprint with free space always got ADD even when the ML model predicted
    100% spillover probability.

    Fix: Rule 2 (ML Safety Net) now runs BEFORE Rule 3 (capacity check).
    If schedule_risk > SCHEDULE_RISK_THRESHOLD (50%), the engine returns
    DEFER regardless of remaining capacity.  This matches the documented
    rule set:
      Rule 0  days_remaining < 2 and not Critical priority          → DEFER
      Rule 1  ticket >= 13 SP and < 10 days remaining               → SPLIT
      Rule 2  ML schedule_risk > 50%                                → DEFER  ← runs before capacity
      Rule 3  free_space >= new_sp                                  → ADD
      Rule 4  swap candidate found                                  → SWAP
      Rule 5  sprint full, no swap candidate                        → DEFER

Decision logic summary:
  • All thresholds are constants at the top of the class — easy to tune.
  • active_items comes 100% from the database — no mock data, no fallback list.
  • ml_predictions.schedule_risk and quality_risk are always consulted.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class RecommendationResult:
    action:            str
    target_to_remove:  Optional[Dict]
    reasoning:         str
    impact_analysis:   Dict[str, Any]
    action_plan:       Dict[str, Any]


class RecommendationEngine:

    # ── Tuneable thresholds ────────────────────────────────────────────────────
    MIN_DAYS_FOR_NEW_WORK    = 2      # Rule 0: sprint almost over
    LARGE_TICKET_SP          = 13     # Rule 1: force split threshold
    LARGE_TICKET_DAYS        = 10     # Rule 1: days-remaining limit for large tickets
    SCHEDULE_RISK_THRESHOLD  = 50.0   # Rule 2: ML score above this → DEFER
    QUALITY_RISK_THRESHOLD   = 70.0   # supplementary: very high defect risk adds caution
    CONTEXT_SWITCH_PENALTY   = 0.2    # used in switch-cost calculation

    def generate_recommendation(
        self,
        new_ticket:     Dict,
        sprint_context: Dict,
        active_items:   List[Dict],   # real items from DB — NEVER mocked
        ml_predictions: Dict,
    ) -> Dict:
        """
        Main entry point.

        Parameters
        ----------
        new_ticket     : dict with title, story_points, priority, type, description
        sprint_context : dict with days_remaining, sprint_load_7d, team_velocity_14d
        active_items   : list of ticket dicts currently in the sprint (from DB)
                         This list is NEVER replaced with hardcoded/mock data.
                         If the sprint is empty, pass [].
        ml_predictions : output from impact_predictor containing at least:
                           schedule_risk   (float, 0-100, spillover probability)
                           quality_risk    (float, 0-100, defect probability)
                           velocity_change (float, ≤ 0, velocity drag %)
                           free_capacity   (float, SP remaining)
        """
        days_remaining  = sprint_context.get("days_remaining", 10)
        current_load    = sprint_context.get("sprint_load_7d", 0)
        velocity        = sprint_context.get("team_velocity_14d", 30)
        real_capacity   = max(velocity, 1)

        new_sp   = new_ticket.get("story_points", 1)
        priority = new_ticket.get("priority", "Medium")
        title    = new_ticket.get("title", "New Ticket")

        # ML signals — read from the predictor output, never from mock data
        schedule_risk   = float(ml_predictions.get("schedule_risk",   0))
        quality_risk    = float(ml_predictions.get("quality_risk",    0))
        velocity_change = float(ml_predictions.get("velocity_change", 0))
        free_capacity   = float(ml_predictions.get(
            "free_capacity",
            max(0, real_capacity - current_load)
        ))

        # ── Rule 0: Sprint almost over ────────────────────────────────────────
        if days_remaining < self.MIN_DAYS_FOR_NEW_WORK and priority not in ("Critical", "Highest"):
            return self._build(
                action="DEFER",
                reason=(
                    f"Sprint ends in {days_remaining:.0f} day(s). "
                    "Too risky to add non-critical work this late."
                ),
                impact={
                    "schedule_risk": schedule_risk,
                    "days_remaining": days_remaining,
                },
            )

        # ── Rule 1: Ticket too large for mid-sprint ───────────────────────────
        if new_sp >= self.LARGE_TICKET_SP and days_remaining < self.LARGE_TICKET_DAYS:
            half_sp = int(new_sp * 0.5)
            return self._build(
                action="SPLIT",
                reason=(
                    f"Ticket size ({new_sp} SP) is too large to complete in "
                    f"{days_remaining:.0f} remaining days. Split required."
                ),
                plan={
                    "split_suggestion": (
                        f"Break into two sub-tickets: "
                        f"'Analysis & Design' ({half_sp} SP) and "
                        f"'Implementation & QA' ({new_sp - half_sp} SP)."
                    )
                },
                impact={
                    "schedule_risk": schedule_risk,
                    "original_sp":   new_sp,
                },
            )

        # ── Rule 2: ML Safety Net — HIGH SCHEDULE RISK → DEFER ───────────────
        # This rule MUST run before the capacity check (Rule 3).
        # Even if the sprint has free space, a high ML spillover probability
        # means the sprint is already stressed and adding more work is unsafe.
        if schedule_risk > self.SCHEDULE_RISK_THRESHOLD:
            return self._build(
                action="DEFER",
                reason=(
                    f"ML model predicts {schedule_risk:.0f}% probability of sprint "
                    f"spillover — well above the {self.SCHEDULE_RISK_THRESHOLD:.0f}% "
                    f"safety threshold. Adding '{title}' risks the entire sprint goal. "
                    f"Defer to the next sprint."
                ),
                impact={
                    "schedule_risk":   schedule_risk,
                    "velocity_change": velocity_change,
                    "quality_risk":    quality_risk,
                    "rule_triggered":  "Rule 2 — ML Safety Net",
                },
                plan={
                    "next_step": (
                        "Add this ticket to the backlog and schedule it for the next sprint. "
                        "Consider splitting if the ticket is larger than 8 SP."
                    )
                },
            )

        # ── Rule 3: Enough capacity → ADD ─────────────────────────────────────
        if free_capacity >= new_sp:
            safety_note = ""
            if quality_risk > self.QUALITY_RISK_THRESHOLD:
                safety_note = (
                    f" Note: quality risk is elevated ({quality_risk:.0f}%) — "
                    "allocate extra QA time."
                )
            return self._build(
                action="ADD",
                reason=(
                    f"Sprint has {free_capacity:.1f} SP free and schedule risk is "
                    f"{schedule_risk:.0f}% (within the safe threshold). "
                    f"Safe to add '{title}'.{safety_note}"
                ),
                impact={
                    "schedule_risk":   schedule_risk,
                    "velocity_change": velocity_change,
                    "free_capacity":   free_capacity,
                },
            )

        # ── Rule 4: Sprint full — try to SWAP ─────────────────────────────────
        swap_candidate = self._find_swap_candidate(new_sp, active_items, priority)

        if swap_candidate:
            switch_cost = self._calculate_switch_cost(swap_candidate)
            return self._build(
                action="SWAP",
                target=swap_candidate,
                reason=(
                    f"Sprint is at capacity ({current_load}/{real_capacity} SP). "
                    f"Swapping out '{swap_candidate['title']}' "
                    f"({swap_candidate.get('story_points', '?')} SP, "
                    f"{swap_candidate.get('priority', '?')} priority) keeps the sprint "
                    f"load balanced. Schedule risk: {schedule_risk:.0f}%."
                ),
                impact={
                    "productivity_cost": f"{switch_cost:.1f} days lost to context switching",
                    "schedule_risk":     schedule_risk,
                    "velocity_change":   velocity_change,
                },
                plan={
                    "step_1": f"Move '{swap_candidate['title']}' to Backlog",
                    "step_2": f"Add '{title}' to the Active Sprint",
                    "step_3": (
                        "Update the sprint plan and notify the team of the priority change."
                    ),
                },
            )

        # ── Rule 5: Sprint full, no swap candidate → DEFER ───────────────────
        return self._build(
            action="DEFER",
            reason=(
                f"Sprint is full ({current_load}/{real_capacity} SP) and no suitable "
                f"lower-priority item was found to swap. Deferring '{title}' to the "
                f"next sprint is the safest option."
            ),
            impact={
                "schedule_risk":  schedule_risk,
                "current_load":   current_load,
                "real_capacity":  real_capacity,
            },
            plan={
                "next_step": (
                    "Add to backlog and prioritise for next sprint planning."
                )
            },
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _find_swap_candidate(
        self,
        needed_sp:    float,
        items:        List[Dict],   # real DB items, never mocked
        new_priority: str,
    ) -> Optional[Dict]:
        """
        Find the best item to move to backlog to make room for the new ticket.
        Criteria:
          - Not already Done/Completed
          - Lower or equal priority than the new ticket
          - Story points as close as possible to needed_sp (minimises load change)
          - Prefer 'To Do' over 'In Progress' (less disruption)
        """
        priority_rank = {"Highest": 5, "Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}
        new_rank      = priority_rank.get(new_priority, 3)

        candidates = []
        for item in items:
            if item.get("status") in ("Done", "Completed", "Closed"):
                continue
            item_rank = priority_rank.get(item.get("priority", "Medium"), 3)
            if item_rank > new_rank:
                # Can't swap out a higher-priority item
                continue

            status_penalty = 0 if item.get("status") == "To Do" else 100  # penalise in-progress
            sp_diff        = abs(item.get("story_points", 0) - needed_sp)

            candidates.append({
                "item":  item,
                "score": sp_diff + status_penalty,
            })

        if not candidates:
            return None
        candidates.sort(key=lambda x: x["score"])
        return candidates[0]["item"]

    def _calculate_switch_cost(self, item: Dict) -> float:
        """Estimate days lost to context switching when deferring an item."""
        if item.get("status") == "In Progress":
            return 2.5   # significant: work-in-progress interrupted
        return 0.5       # minimal: not yet started

    def _build(self, action, reason, target=None, impact=None, plan=None) -> Dict:
        return {
            "recommendation_type": action,
            "reasoning":           reason,
            "target_ticket":       target,
            "impact_analysis":     impact or {},
            "action_plan":         plan or {},
        }


# Singleton
recommendation_engine = RecommendationEngine()