from typing import Dict, List, Any, Optional


PRIORITY_RANK = {"Highest": 5, "Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}

# ══════════════════════════════════════════════════════════════════════════════
# RISK APPETITE THRESHOLDS — Domain-specific risk tolerance tuning
# ══════════════════════════════════════════════════════════════════════════════
#
# Defines ML thresholds for different risk appetites. Overridable per Space.
#
# STRICT: Conservative — high confidence required to add mid-sprint work
#   - Schedule risk > 30% → DEFER
#   - Productivity drag < -20% → DEFER
#   - Quality risk > 60% → DEFER
#
# STANDARD (default): Balanced — moderate confidence required
#   - Schedule risk > 50% → DEFER
#   - Productivity drag < -30% → DEFER
#   - Quality risk > 70% → DEFER
#
# LENIENT: Permissive — allow more mid-sprint additions
#   - Schedule risk > 70% → DEFER
#   - Productivity drag < -40% → DEFER
#   - Quality risk > 80% → DEFER
#

def get_thresholds_by_appetite(risk_appetite: str) -> dict:
    """
    Map risk appetite setting to ML thresholds.
    
    Args:
        risk_appetite: One of "Strict", "Standard", "Lenient"
    
    Returns:
        dict with schedule_risk_threshold, prod_drag_threshold, quality_risk_threshold
    """
    thresholds = {
        "Strict": {
            "schedule_risk_threshold": 30.0,
            "prod_drag_threshold": -20.0,
            "quality_risk_threshold": 60.0,
        },
        "Standard": {
            "schedule_risk_threshold": 50.0,
            "prod_drag_threshold": -30.0,
            "quality_risk_threshold": 70.0,
        },
        "Lenient": {
            "schedule_risk_threshold": 70.0,
            "prod_drag_threshold": -40.0,
            "quality_risk_threshold": 80.0,
        },
    }
    
    return thresholds.get(risk_appetite, thresholds["Standard"])


# Legacy defaults for backward compatibility
SCHEDULE_RISK_THRESHOLD = 50.0
PROD_DRAG_THRESHOLD     = -30.0
QUALITY_RISK_THRESHOLD  = 70.0


class RecommendationEngine:

    MIN_DAYS_FOR_NEW_WORK   = 2
    LARGE_TICKET_SP         = 13
    LARGE_TICKET_DAYS       = 10

    def __init__(self, risk_appetite: str = "Standard"):
        """
        Initialize recommendation engine with configurable risk appetite.
        
        Args:
            risk_appetite: One of "Strict", "Standard", "Lenient" (case-sensitive)
        """
        thresholds = get_thresholds_by_appetite(risk_appetite)
        self.schedule_risk_threshold = thresholds["schedule_risk_threshold"]
        self.prod_drag_threshold = thresholds["prod_drag_threshold"]
        self.quality_risk_threshold = thresholds["quality_risk_threshold"]
        self.risk_appetite = risk_appetite

    def generate_recommendation(
        self,
        new_ticket:     Dict,
        sprint_context: Dict,
        active_items:   List[Dict],
        ml_predictions: Dict,
        goal_alignment: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate a recommendation considering:
        1. Sprint state (days remaining, current load, capacity)
        2. Ticket properties (SP, priority, description)
        3. ML predictions (schedule risk, quality risk, productivity impact)
        4. Goal alignment score (if provided) — determines strategic value
        
        Args:
            new_ticket: Ticket data {title, description, story_points, priority}
            sprint_context: Sprint state {days_remaining, current_load, velocity}
            active_items: List of items already in sprint
            ml_predictions: ML model outputs {schedule_risk, quality_risk, velocity_change}
            goal_alignment: Optional alignment data {score (0-1), level, recommendation}
        
        Returns:
            Recommendation dict with action, reasoning, impact analysis, action plan
        """
        days_remaining = sprint_context.get("days_remaining", 10)
        current_load   = sprint_context.get("sprint_load_7d", 0)
        velocity       = sprint_context.get("team_velocity_14d", 30)
        real_capacity  = max(velocity, 1)

        new_sp   = new_ticket.get("story_points", 1)
        priority = new_ticket.get("priority", "Medium")
        title    = new_ticket.get("title", "New Ticket")

        schedule_risk   = float(ml_predictions.get("schedule_risk",   0))
        quality_risk    = float(ml_predictions.get("quality_risk",    0))
        velocity_change = float(ml_predictions.get("velocity_change", 0))
        free_capacity   = float(ml_predictions.get(
            "free_capacity",
            max(0, real_capacity - current_load),
        ))
        
        # Extract goal alignment signal (if provided)
        alignment_score = 0.5  # Default neutral
        alignment_boost = 0.0  # Boost confidence if well-aligned
        if goal_alignment:
            alignment_score = goal_alignment.get("score", 0.5)
            # If strongly aligned (>=0.50), boost confidence in other signals
            if alignment_score >= 0.50:
                alignment_boost = 5.0  # Lower thresholds by 5%
            # If poorly aligned (<0.30), decrease confidence
            elif alignment_score < 0.30:
                alignment_boost = -10.0  # Raise thresholds by 10%

        # ── Rule 0: Sprint almost over ────────────────────────────────────────
        if days_remaining < self.MIN_DAYS_FOR_NEW_WORK and priority not in ("Critical", "Highest"):
            return self._build(
                action="DEFER",
                reason=(
                    f"Sprint ends in {days_remaining:.0f} day(s). "
                    "Too risky to add non-critical work this late."
                ),
                impact={"schedule_risk": schedule_risk, "days_remaining": days_remaining},
            )

        # ── Rule 0.5: Emergency Protocol — Critical priority ──────────────────
        # Critical tickets (production bugs, P0 issues) bypass all ML risk
        # checks.  We never defer a production emergency — we either force a
        # swap to make room or accept the overload.
        if priority in ("Critical", "Highest"):
            force_swap = self._find_force_swap_candidate(active_items)
            if force_swap:
                switch_cost = self._calculate_switch_cost(force_swap)
                return self._build(
                    action="FORCE SWAP",
                    target=force_swap,
                    reason=(
                        f"EMERGENCY PROTOCOL: '{title}' is Critical priority. "
                        f"Removing lowest-value item '{force_swap['title']}' "
                        f"({force_swap.get('story_points', '?')} SP, "
                        f"{force_swap.get('priority', '?')} priority, "
                        f"{force_swap.get('status', '?')}) to make room. "
                        "All risk checks bypassed."
                    ),
                    impact={
                        "emergency":         True,
                        "schedule_risk":     schedule_risk,
                        "velocity_change":   velocity_change,
                        "productivity_cost": f"{switch_cost:.1f} days lost to context switching",
                    },
                    plan={
                        "step_1": f"Immediately move '{force_swap['title']}' to Backlog",
                        "step_2": f"Add '{title}' to the Active Sprint as top priority",
                        "step_3": "Notify the team and update sprint goal if necessary",
                    },
                )
            else:
                return self._build(
                    action="OVERLOAD",
                    reason=(
                        f"EMERGENCY PROTOCOL: '{title}' is Critical priority and no "
                        "removable 'To Do' item exists in the sprint. Accepting sprint "
                        "overload — this ticket must be resolved immediately regardless "
                        "of capacity."
                    ),
                    impact={
                        "emergency":       True,
                        "schedule_risk":   schedule_risk,
                        "velocity_change": velocity_change,
                        "overload_sp":     new_sp,
                    },
                    plan={
                        "step_1": f"Add '{title}' to sprint immediately",
                        "step_2": "Communicate overload risk to stakeholders",
                        "step_3": "Consider pulling in extra resources or deferring a different item manually",
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
                impact={"schedule_risk": schedule_risk, "original_sp": new_sp},
            )

        # ── Rule 2: ML Safety Net — multi-signal DEFER ───────���────────────────
        # Triggers if ANY of the three ML signals exceeds its threshold.
        # The reason text dynamically names which signal(s) caused the deferral.
        # Uses module-level calibration constants for threshold tuning.
        # Adjust thresholds based on goal alignment
        adjusted_schedule_threshold = max(20, self.schedule_risk_threshold + alignment_boost)
        adjusted_quality_threshold = max(50, self.quality_risk_threshold + alignment_boost)
        adjusted_prod_threshold = self.prod_drag_threshold - (alignment_boost * 0.5)
        
        triggered = []
        if schedule_risk > adjusted_schedule_threshold:
            triggered.append(f"Schedule Risk is too high ({schedule_risk:.0f}% > {adjusted_schedule_threshold:.0f}%)")
        if velocity_change < adjusted_prod_threshold:
            triggered.append(f"Productivity Drag is too high ({abs(velocity_change):.0f}% slowdown)")
        if quality_risk > adjusted_quality_threshold:
            triggered.append(f"Quality Risk is too high ({quality_risk:.0f}% > {adjusted_quality_threshold:.0f}%)")

        if triggered:
            trigger_text = " | ".join(triggered)
            alignment_context = ""
            if goal_alignment and alignment_score < 0.50:
                alignment_context = f" (Task alignment with sprint goal is only {alignment_score:.0%} — additional caution applied.)"
            
            return self._build(
                action="DEFER",
                reason=(
                    f"ML Safety Net triggered — Deferred because: {trigger_text}.{alignment_context} "
                    f"Adding '{title}' risks the sprint goal and timeline."
                ),
                impact={
                    "schedule_risk":      schedule_risk,
                    "velocity_change":    velocity_change,
                    "quality_risk":       quality_risk,
                    "alignment_score":    alignment_score,
                    "adjusted_thresholds": {
                        "schedule": adjusted_schedule_threshold,
                        "quality": adjusted_quality_threshold,
                    },
                    "triggers":           triggered,
                    "rule_triggered":     "Rule 2 — ML Safety Net",
                },
                plan={
                    "next_step": (
                        "Add this ticket to the backlog and schedule it for the next sprint. "
                        "Consider splitting if the ticket is larger than 8 SP."
                    )
                },
            )

        # ── Rule 3: Enough capacity → ADD (with alignment sentiment) ──────────────
        if free_capacity >= new_sp:
            safety_note = ""
            alignment_sentiment = ""
            if quality_risk > 50:
                safety_note = (
                    f" Note: quality risk is elevated ({quality_risk:.0f}%) — "
                    "allocate extra QA time."
                )
            if goal_alignment:
                if alignment_score >= 0.50:
                    alignment_sentiment = (
                        f" Task is strongly aligned with sprint goal ({alignment_score:.0%}) — "
                        "adds strategic value."
                    )
                elif alignment_score < 0.30:
                    alignment_sentiment = (
                        f" WARNING: Task is not well-aligned with sprint goal ({alignment_score:.0%}). "
                        "Consider deferring despite capacity."
                    )
            
            return self._build(
                action="ADD",
                reason=(
                    f"Sprint has {free_capacity:.1f} SP free and all ML signals are within "
                    f"safe thresholds (Schedule: {schedule_risk:.0f}%, "
                    f"Drag: {abs(velocity_change):.0f}%, Quality: {quality_risk:.0f}%). "
                    f"Safe to add '{title}'.{safety_note}{alignment_sentiment}"
                ),
                impact={
                    "schedule_risk":      schedule_risk,
                    "velocity_change":    velocity_change,
                    "free_capacity":      free_capacity,
                    "alignment_score":    alignment_score,
                    "rule_triggered":     "Rule 3 — Capacity Available",
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
                    f"{swap_candidate.get('priority', '?')} priority) keeps load balanced. "
                    f"Schedule risk: {schedule_risk:.0f}%."
                ),
                impact={
                    "productivity_cost": f"{switch_cost:.1f} days lost to context switching",
                    "schedule_risk":     schedule_risk,
                    "velocity_change":   velocity_change,
                },
                plan={
                    "step_1": f"Move '{swap_candidate['title']}' to Backlog",
                    "step_2": f"Add '{title}' to the Active Sprint",
                    "step_3": "Update the sprint plan and notify the team of the priority change.",
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
                "schedule_risk": schedule_risk,
                "current_load":  current_load,
                "real_capacity": real_capacity,
            },
            plan={"next_step": "Add to backlog and prioritise for next sprint planning."},
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _find_swap_candidate(
        self,
        needed_sp:    float,
        items:        List[Dict],
        new_priority: str,
    ) -> Optional[Dict]:
        new_rank   = PRIORITY_RANK.get(new_priority, 3)
        candidates = []
        for item in items:
            if item.get("status") in ("Done", "Completed", "Closed"):
                continue
            item_rank = PRIORITY_RANK.get(item.get("priority", "Medium"), 3)
            if item_rank > new_rank:
                continue
            status_penalty = 0 if item.get("status") == "To Do" else 100
            sp_diff        = abs(item.get("story_points", 0) - needed_sp)
            candidates.append({"item": item, "score": sp_diff + status_penalty})

        if not candidates:
            return None
        candidates.sort(key=lambda x: x["score"])
        return candidates[0]["item"]

    def _find_force_swap_candidate(self, items: List[Dict]) -> Optional[Dict]:
        """
        Emergency Protocol: find the lowest-value 'To Do' item to remove.
        Lowest-value = lowest priority rank, then fewest story points.
        Only considers 'To Do' items — never pulls something already In Progress.
        """
        todo_items = [
            item for item in items
            if item.get("status") == "To Do"
            and item.get("status") not in ("Done", "Completed", "Closed")
        ]
        if not todo_items:
            return None
        todo_items.sort(key=lambda x: (
            PRIORITY_RANK.get(x.get("priority", "Medium"), 3),
            x.get("story_points", 0),
        ))
        return todo_items[0]

    def _calculate_switch_cost(self, item: Dict) -> float:
        if item.get("status") == "In Progress":
            return 2.5
        return 0.5

    def _build(self, action, reason, target=None, impact=None, plan=None) -> Dict:
        return {
            "recommendation_type": action,
            "reasoning":           reason,
            "target_ticket":       target,
            "impact_analysis":     impact or {},
            "action_plan":         plan or {},
        }


# Note: RecommendationEngine is instantiated per-request in routes with risk_appetite parameter
