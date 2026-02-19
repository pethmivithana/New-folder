"""
ROBUST RECOMMENDATION ENGINE
============================
Implements the "3-Engine Architecture" logic for Agile Sprint Replanning.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class RecommendationResult:
    action: str
    target_to_remove: Optional[Dict]
    reasoning: str
    impact_analysis: Dict[str, Any]
    action_plan: Dict[str, Any]

class RecommendationEngine:
    def __init__(self):
        self.MIN_DAYS_FOR_NEW_WORK = 2
        self.MAX_SP_FOR_SPLIT = 8
        self.CONTEXT_SWITCH_PENALTY = 0.2

    def generate_recommendation(
        self, 
        new_ticket: Dict, 
        sprint_context: Dict, 
        active_items: List[Dict],
        ml_predictions: Dict
    ) -> Dict:
        """Main entry point for recommendations"""
        days_remaining = sprint_context.get("days_remaining", 10)
        current_load = sprint_context.get("sprint_load_7d", 0)
        velocity = sprint_context.get("team_velocity_14d", 30)
        
        real_capacity = velocity if velocity > 0 else 30
        
        new_sp = new_ticket.get("story_points", 1)
        priority = new_ticket.get("priority", "Medium")

        # Safety checks
        if days_remaining < self.MIN_DAYS_FOR_NEW_WORK and priority != "Highest":
            return self._build_response(
                action="DEFER",
                reason=f"Sprint ends in {days_remaining:.1f} days. Too risky to add non-critical work.",
                impact={"schedule_risk": "Critical"}
            )

        if new_sp >= 13 and days_remaining < 10:
            return self._build_response(
                action="SPLIT",
                reason=f"Ticket size ({new_sp} SP) is too large for mid-sprint. Split required.",
                plan={"split_suggestion": f"Break into 'Analysis' ({int(new_sp*0.3)} SP) and 'Dev' ({int(new_sp*0.7)} SP)."}
            )

        # Capacity logic
        free_space = real_capacity - current_load
        
        if free_space >= new_sp:
            return self._build_response(
                action="ADD",
                reason=f"Sprint has capacity (Free: {free_space:.1f} SP). Safe to add.",
                impact={"velocity_impact": "None"}
            )

        # Need to swap
        swap_candidate = self._find_swap_candidate(new_sp, active_items, priority)
        
        if swap_candidate:
            switch_cost = self._calculate_switch_cost(swap_candidate)
            
            return self._build_response(
                action="SWAP",
                target=swap_candidate,
                reason=f"Sprint full. Swapping '{swap_candidate['title']}' ({swap_candidate['story_points']} SP) keeps capacity neutral.",
                impact={"productivity_cost": f"{switch_cost:.1f} Days lost to context switching"},
                plan={
                    "step_1": f"Move '{swap_candidate['title']}' to Backlog",
                    "step_2": f"Add '{new_ticket['title']}' to Active Sprint"
                }
            )

        return self._build_response(
            action="DEFER",
            reason=f"Sprint is full ({current_load}/{real_capacity} SP) and no suitable low-priority items found to swap.",
            impact={"schedule_risk": "High"}
        )

    def _find_swap_candidate(self, needed_sp: float, items: List[Dict], new_priority: str) -> Optional[Dict]:
        """Find best item to swap"""
        candidates = []
        
        priority_rank = {"Highest": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}
        new_prio_rank = priority_rank.get(new_priority, 3)

        for item in items:
            if item.get("status") in ["Done", "Completed"]:
                continue
            
            status_penalty = 0 if item.get("status") == "To Do" else 100
            
            item_prio = item.get("priority", "Medium")
            if priority_rank.get(item_prio, 3) > new_prio_rank:
                continue

            diff = abs(item.get("story_points", 0) - needed_sp)
            
            candidates.append({
                "item": item,
                "score": diff + status_penalty
            })

        if not candidates:
            return None
            
        candidates.sort(key=lambda x: x["score"])
        return candidates[0]["item"]

    def _calculate_switch_cost(self, item: Dict) -> float:
        """Calculate context switch cost"""
        if item.get("status") == "In Progress":
            return 2.5
        return 0.5

    def _build_response(self, action, reason, target=None, impact=None, plan=None):
        return {
            "recommendation_type": action,
            "reasoning": reason,
            "target_ticket": target,
            "impact_analysis": impact or {},
            "action_plan": plan or {}
        }

# Create singleton instance
recommendation_engine = RecommendationEngine()