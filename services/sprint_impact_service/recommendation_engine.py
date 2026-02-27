from typing import Dict, List, Any, Optional


PRIORITY_RANK = {"Highest": 5, "Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}


class RecommendationEngine:

    MIN_DAYS_FOR_NEW_WORK   = 2
    LARGE_TICKET_SP         = 13
    LARGE_TICKET_DAYS       = 10
    SCHEDULE_RISK_THRESHOLD = 50.0   # Rule 2: schedule_risk % above this → DEFER
    PROD_DRAG_THRESHOLD     = -30.0  # Rule 2: velocity_change % below this → DEFER
    QUALITY_RISK_THRESHOLD  = 70.0   # Rule 2: quality_risk % above this → DEFER

    def generate_recommendation(
        self,
        new_ticket:     Dict,
        sprint_context: Dict,
        active_items:   List[Dict],
        ml_predictions: Dict,
    ) -> Dict:
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

        # ── Rule 2: ML Safety Net — multi-signal DEFER ────────────────────────
        # Triggers if ANY of the three ML signals exceeds its threshold.
        # The reason text dynamically names which signal(s) caused the deferral.
        triggered = []
        if schedule_risk > self.SCHEDULE_RISK_THRESHOLD:
            triggered.append(f"Schedule Risk is too high ({schedule_risk:.0f}%)")
        if velocity_change < self.PROD_DRAG_THRESHOLD:
            triggered.append(f"Productivity Drag is too high ({abs(velocity_change):.0f}% slowdown)")
        if quality_risk > self.QUALITY_RISK_THRESHOLD:
            triggered.append(f"Quality Risk is too high ({quality_risk:.0f}% defect probability)")

        if triggered:
            trigger_text = " | ".join(triggered)
            return self._build(
                action="DEFER",
                reason=(
                    f"ML Safety Net triggered — Deferred because: {trigger_text}. "
                    f"Adding '{title}' risks the sprint goal."
                ),
                impact={
                    "schedule_risk":   schedule_risk,
                    "velocity_change": velocity_change,
                    "quality_risk":    quality_risk,
                    "triggers":        triggered,
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
            if quality_risk > 50:
                safety_note = (
                    f" Note: quality risk is elevated ({quality_risk:.0f}%) — "
                    "allocate extra QA time."
                )
            return self._build(
                action="ADD",
                reason=(
                    f"Sprint has {free_capacity:.1f} SP free and all ML signals are within "
                    f"safe thresholds (Schedule: {schedule_risk:.0f}%, "
                    f"Drag: {abs(velocity_change):.0f}%, Quality: {quality_risk:.0f}%). "
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


recommendation_engine = RecommendationEngine()