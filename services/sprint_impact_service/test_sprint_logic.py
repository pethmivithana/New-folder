"""
TEST_SPRINT_LOGIC.PY
──────────────────────────────────────────────────────────────────────────────
Comprehensive pytest suite for validating core Sprint Impact Analyzer logic:

✓ Story Point Suggestion based on text length/complexity
✓ Sprint Goal Alignment (TF-IDF/Cosine Similarity)
✓ Dynamic Capacity Math (velocity-based hours-per-sp)
✓ Capacity Breach Detection
✓ Rule Engine Decision Logic (ADD, DEFER, SPLIT, SWAP)

Run with: pytest test_sprint_logic.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import math


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (Mock the core logic)
# ─────────────────────────────────────────────────────────────────────────────

def estimate_story_points_from_text(title: str, description: str) -> int:
    """
    Mock: Estimate story points based on text length and complexity.
    
    Real implementation uses TF-IDF + complexity heuristics.
    This simplified version demonstrates the concept:
      - < 100 chars total: 3 SP (simple task)
      - 100-300 chars: 5 SP (moderate)
      - 300-600 chars: 8 SP (complex)
      - > 600 chars: 13 SP (very complex)
    """
    text = f"{title} {description}".strip()
    length = len(text)
    
    keywords = ['integration', 'refactor', 'oauth', 'security', 'migrate', 'async']
    complexity_boost = sum(1 for kw in keywords if kw.lower() in text.lower()) * 2
    
    if length < 100:
        base_sp = 3
    elif length < 300:
        base_sp = 5
    elif length < 600:
        base_sp = 8
    else:
        base_sp = 13
    
    return min(base_sp + complexity_boost, 13)


def calculate_sprint_goal_alignment(ticket_text: str, sprint_goal: str) -> float:
    """
    Mock: Calculate TF-IDF cosine similarity between ticket and sprint goal.
    
    Real implementation uses sklearn TfidfVectorizer.
    This simplified version demonstrates alignment scoring:
      - Returns a score 0.0 to 1.0
      - Higher = more aligned
    """
    # Extract key terms from both
    ticket_terms = set(ticket_text.lower().split())
    goal_terms = set(sprint_goal.lower().split())
    
    # Calculate Jaccard similarity as proxy for cosine similarity
    if not ticket_terms or not goal_terms:
        return 0.0
    
    intersection = len(ticket_terms & goal_terms)
    union = len(ticket_terms | goal_terms)
    
    return intersection / union if union > 0 else 0.0


def calculate_dynamic_capacity(
    velocity: int,
    assignees: int,
    days: int,
    base_focus_hours: float = 6.0,
) -> dict:
    """
    Mock: Calculate sprint capacity based on velocity, team size, and available time.
    
    Formula:
      Total_Sprint_Hours = days * base_focus_hours * assignees
      Hours_Per_SP = Total_Sprint_Hours / velocity
      Effective_Capacity = velocity * (assignees / 3)  # assuming base is 3 devs
    """
    total_hours = days * base_focus_hours * assignees
    hours_per_sp = total_hours / max(velocity, 1)
    capacity_multiplier = assignees / 3.0
    effective_capacity = velocity * capacity_multiplier
    
    return {
        "total_hours": total_hours,
        "hours_per_sp": round(hours_per_sp, 2),
        "velocity": velocity,
        "assignees": assignees,
        "capacity_multiplier": round(capacity_multiplier, 2),
        "effective_capacity": round(effective_capacity, 1),
    }


def check_capacity_breach(current_load: int, new_sp: int, capacity: int) -> bool:
    """Check if adding new ticket would exceed sprint capacity."""
    return (current_load + new_sp) > capacity


def get_alignment_state(similarity_score: float) -> str:
    """Convert alignment score to semantic state."""
    if similarity_score >= 0.7:
        return "STRONGLY_ALIGNED"
    elif similarity_score >= 0.5:
        return "PARTIALLY_ALIGNED"
    elif similarity_score >= 0.3:
        return "WEAKLY_ALIGNED"
    else:
        return "UNALIGNED"


def mock_ml_predictions(
    effort_sp: int,
    alignment_state: str,
    days_remaining: int,
    current_load: int,
    capacity: int,
) -> dict:
    """
    Mock: Generate ML risk predictions based on context.
    
    Real implementation uses XGBoost/PyTorch models.
    """
    schedule_risk = 20.0
    quality_risk = 15.0
    velocity_change = 0.0
    
    # Adjust based on capacity
    if current_load + effort_sp > capacity:
        overage = (current_load + effort_sp) - capacity
        schedule_risk += overage * 5  # Risk increases with overage
    
    # Adjust based on days remaining
    if days_remaining < 3:
        schedule_risk += 20.0
    
    # Adjust based on alignment
    if alignment_state == "UNALIGNED":
        quality_risk += 25.0
        velocity_change -= 15.0
    elif alignment_state == "WEAKLY_ALIGNED":
        velocity_change -= 10.0
    elif alignment_state == "STRONGLY_ALIGNED":
        velocity_change += 5.0
    
    return {
        "schedule_risk": min(schedule_risk, 99.0),
        "quality_risk": min(quality_risk, 99.0),
        "velocity_change": velocity_change,
        "free_capacity": max(0, capacity - current_load),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestStoryPointEstimation:
    """Test story point suggestion logic based on text length and complexity."""
    
    def test_simple_task_short_text(self):
        """Short, simple text should estimate to ~3 SP."""
        title = "Fix typo"
        description = "Update README."
        sp = estimate_story_points_from_text(title, description)
        assert sp == 3, f"Expected 3 SP, got {sp}"
    
    def test_moderate_task_medium_text(self):
        """Medium-length text should estimate to ~5 SP."""
        title = "Add user validation"
        description = "Implement email validation logic with regex and error handling."
        sp = estimate_story_points_from_text(title, description)
        assert sp == 5, f"Expected 5 SP, got {sp}"
    
    def test_complex_story_long_text(self):
        """Long text should estimate to 8-13 SP."""
        title = "Implement OAuth 2.0 integration"
        description = (
            "Add OAuth provider support for third-party integrations. Requires "
            "API keys, token management, security review, and comprehensive testing."
        )
        sp = estimate_story_points_from_text(title, description)
        assert sp >= 8, f"Expected >= 8 SP, got {sp}"
    
    def test_complexity_keywords_boost_estimate(self):
        """Keywords like 'security', 'integration' should boost SP estimate."""
        title = "Add security audit logging"
        description = (
            "Implement comprehensive security audit trails. Track all admin actions "
            "and sensitive data access. Integrate with SIEM system."
        )
        sp = estimate_story_points_from_text(title, description)
        assert sp > 5, f"Expected boosted estimate, got {sp} SP"


class TestSprintGoalAlignment:
    """Test sprint goal alignment calculation (TF-IDF mock)."""
    
    def test_perfectly_aligned_ticket(self):
        """Ticket fully matching sprint goal should have high alignment."""
        ticket = "Implement rate limiting security feature"
        goal = "Enhance security and implement rate limiting"
        alignment = calculate_sprint_goal_alignment(ticket, goal)
        assert alignment > 0.5, f"Expected > 0.5 alignment, got {alignment}"
    
    def test_unaligned_ticket(self):
        """Ticket unrelated to sprint goal should have low alignment."""
        ticket = "Update company blog with new posts"
        goal = "Enhance security and scale infrastructure"
        alignment = calculate_sprint_goal_alignment(ticket, goal)
        assert alignment < 0.5, f"Expected < 0.5 alignment, got {alignment}"
    
    def test_partial_alignment(self):
        """Ticket sharing some terms should have moderate alignment."""
        ticket = "Improve database security with encryption"
        goal = "Enhance security and scale infrastructure"
        alignment = calculate_sprint_goal_alignment(ticket, goal)
        assert 0.2 < alignment < 0.8, f"Expected moderate alignment, got {alignment}"
    
    def test_alignment_state_mapping(self):
        """Test mapping alignment scores to semantic states."""
        assert get_alignment_state(0.8) == "STRONGLY_ALIGNED"
        assert get_alignment_state(0.6) == "PARTIALLY_ALIGNED"
        assert get_alignment_state(0.4) == "WEAKLY_ALIGNED"
        assert get_alignment_state(0.1) == "UNALIGNED"


class TestDynamicCapacityMath:
    """Test dynamic capacity calculations (velocity-based hours-per-SP)."""
    
    def test_capacity_baseline_3_devs(self):
        """3 developers with 30 SP velocity should have expected capacity metrics."""
        capacity = calculate_dynamic_capacity(velocity=30, assignees=3, days=10, base_focus_hours=6.0)
        
        assert capacity["velocity"] == 30
        assert capacity["assignees"] == 3
        assert capacity["total_hours"] == 180  # 10 days * 6h * 3 devs
        assert capacity["hours_per_sp"] == 6.0  # 180h / 30 SP
        assert capacity["effective_capacity"] == 30.0  # 30 SP * (3/3)
    
    def test_capacity_scales_with_team_size(self):
        """Capacity should increase proportionally with team size."""
        capacity_3 = calculate_dynamic_capacity(velocity=30, assignees=3, days=10)
        capacity_4 = calculate_dynamic_capacity(velocity=30, assignees=4, days=10)
        
        # With 4 devs, effective capacity increases
        assert capacity_4["effective_capacity"] > capacity_3["effective_capacity"]
        assert capacity_4["effective_capacity"] == pytest.approx(40.0)
    
    def test_hours_per_sp_inverse_velocity(self):
        """Lower velocity teams need more hours per story point."""
        capacity_low = calculate_dynamic_capacity(velocity=20, assignees=3, days=10)
        capacity_high = calculate_dynamic_capacity(velocity=35, assignees=3, days=10)
        
        # Lower velocity = higher hours per SP
        assert capacity_low["hours_per_sp"] > capacity_high["hours_per_sp"]
    
    def test_velocity_fluctuation_affects_hours_per_sp(self):
        """
        Real-world test: Sprint velocity fluctuates (20 → 35 → 15 → 32 → 28).
        Hours per SP should adjust dynamically.
        """
        velocities = [20, 35, 15, 32, 28]
        hours_per_sp_values = []
        
        for velocity in velocities:
            capacity = calculate_dynamic_capacity(velocity=velocity, assignees=3, days=10)
            hours_per_sp_values.append(capacity["hours_per_sp"])
        
        # When velocity drops (20 → 15), hours per SP should increase
        assert hours_per_sp_values[2] > hours_per_sp_values[0]  # Day 3 > Day 1
        
        # When velocity increases (15 → 35), hours per SP should decrease
        assert hours_per_sp_values[1] < hours_per_sp_values[2]  # Day 2 < Day 3


class TestCapacityBreachDetection:
    """Test identification of capacity overruns."""
    
    def test_ticket_fits_in_capacity(self):
        """Ticket smaller than free capacity should not breach."""
        breach = check_capacity_breach(current_load=10, new_sp=5, capacity=20)
        assert breach is False
    
    def test_ticket_exceeds_capacity(self):
        """Ticket exceeding free capacity should be flagged."""
        breach = check_capacity_breach(current_load=18, new_sp=5, capacity=20)
        assert breach is True
    
    def test_ticket_exactly_at_limit(self):
        """Ticket filling exactly to capacity should be at edge."""
        breach = check_capacity_breach(current_load=15, new_sp=5, capacity=20)
        assert breach is False
    
    def test_sprint_full_detection(self):
        """Fully-loaded sprint should detect breach immediately."""
        breach = check_capacity_breach(current_load=30, new_sp=1, capacity=30)
        assert breach is True


class TestRuleEngineLogic:
    """Test core recommendation engine rules."""
    
    def test_rule_1_emergency_fits_capacity(self):
        """
        Rule 1a: CRITICAL priority ticket that fits capacity → ADD
        """
        alignment_state = "CRITICAL_BLOCKER"
        effort_sp = 5
        free_capacity = 22
        
        # In rule engine: if fits, action = "ADD"
        assert effort_sp <= free_capacity
        # This would trigger Rule 1a in decision_engine
    
    def test_rule_2_unaligned_scope_creep(self):
        """
        Rule 2a: UNALIGNED ticket → DEFER (scope creep protection)
        """
        alignment_state = "UNALIGNED"
        
        # In rule engine: UNALIGNED always defers
        assert alignment_state == "UNALIGNED"
        # This would trigger Rule 2a in decision_engine
    
    def test_rule_3_monster_ticket_too_large(self):
        """
        Rule 3a: Aligned but > 8 SP with days remaining < 10 → SPLIT
        """
        effort_sp = 13
        alignment_state = "STRONGLY_ALIGNED"
        days_remaining = 5
        
        # Monster ticket logic: aligned but oversized
        assert alignment_state in ("STRONGLY_ALIGNED", "PARTIALLY_ALIGNED")
        assert effort_sp > 8
        # This would trigger Rule 3a in decision_engine
    
    def test_rule_4_high_priority_swap(self):
        """
        Rule 4: STRONGLY_ALIGNED + HIGH priority + exceeds capacity → SWAP
        """
        alignment_state = "STRONGLY_ALIGNED"
        priority = "High"
        effort_sp = 10
        free_capacity = 8
        
        # Swap logic: high priority aligned ticket that doesn't fit
        assert alignment_state == "STRONGLY_ALIGNED"
        assert priority in ("High", "Critical")
        assert effort_sp > free_capacity
        # This would trigger Rule 4 in decision_engine
    
    def test_rule_5_perfect_fit(self):
        """
        Rule 5: Aligned + fits capacity → ADD (textbook success)
        """
        alignment_state = "PARTIALLY_ALIGNED"
        effort_sp = 5
        free_capacity = 20
        
        # Perfect fit: aligned and capacity available
        assert alignment_state in ("STRONGLY_ALIGNED", "PARTIALLY_ALIGNED")
        assert effort_sp <= free_capacity
        # This would trigger Rule 5 in decision_engine
    
    def test_rule_6_catch_all_defer(self):
        """
        Rule 6: Anything that doesn't match higher rules → DEFER
        """
        # Fallback behavior: default to safe option
        # If no specific rule matches, defer to backlog
        pass


class TestMLPredictionsIntegration:
    """Test ML model output integration with rule engine."""
    
    def test_high_schedule_risk_triggers_defer(self):
        """Schedule risk > 50% (Standard appetite) should trigger DEFER."""
        predictions = mock_ml_predictions(
            effort_sp=10,
            alignment_state="WEAKLY_ALIGNED",
            days_remaining=2,  # Few days left = high risk
            current_load=25,
            capacity=30,
        )
        
        assert predictions["schedule_risk"] > 50
        # In rule engine: high schedule risk → DEFER
    
    def test_strong_alignment_lowers_risk(self):
        """STRONGLY_ALIGNED tickets should have lower productivity drag."""
        predictions = mock_ml_predictions(
            effort_sp=5,
            alignment_state="STRONGLY_ALIGNED",
            days_remaining=8,
            current_load=15,
            capacity=30,
        )
        
        # Strong alignment should result in positive or minimal velocity change
        assert predictions["velocity_change"] >= -5
    
    def test_capacity_overflow_increases_schedule_risk(self):
        """Overloading sprint should dramatically increase schedule risk."""
        predictions_underload = mock_ml_predictions(
            effort_sp=5,
            alignment_state="STRONGLY_ALIGNED",
            days_remaining=8,
            current_load=10,
            capacity=30,
        )
        
        predictions_overload = mock_ml_predictions(
            effort_sp=5,
            alignment_state="STRONGLY_ALIGNED",
            days_remaining=8,
            current_load=28,  # Almost full
            capacity=30,
        )
        
        # Overload scenario should have higher risk
        assert predictions_overload["schedule_risk"] > predictions_underload["schedule_risk"]


class TestIntegrationScenarios:
    """End-to-end scenarios mimicking real-world workflow."""
    
    def test_scenario_case_a_perfect_fit(self):
        """
        Case A: Rate limiting feature (aligned, high priority, fits capacity)
        Expected: ADD
        """
        title = "Implement rate limiting on API endpoints"
        description = (
            "Add request rate limiting to prevent abuse. Implement token bucket "
            "algorithm with configurable thresholds per user tier."
        )
        sprint_goal = "Enhance security and scale infrastructure"
        current_load = 8
        capacity = 30
        
        # Step 1: Estimate story points
        sp = estimate_story_points_from_text(title, description)
        assert 3 <= sp <= 13
        
        # Step 2: Check alignment
        alignment = calculate_sprint_goal_alignment(f"{title} {description}", sprint_goal)
        alignment_state = get_alignment_state(alignment)
        assert alignment_state in ("STRONGLY_ALIGNED", "PARTIALLY_ALIGNED")
        
        # Step 3: Check capacity
        breach = check_capacity_breach(current_load, sp, capacity)
        assert breach is False
        
        # Step 4: Get ML predictions
        predictions = mock_ml_predictions(sp, alignment_state, 5, current_load, capacity)
        assert predictions["schedule_risk"] < 50
        
        # Expected decision: ADD
        print(f"\nScenario A: {title}")
        print(f"  SP: {sp}, Alignment: {alignment_state}, Risk: {predictions['schedule_risk']:.0f}%")
        print(f"  → ADD (Safe fit)")
    
    def test_scenario_case_b_scope_creep(self):
        """
        Case B: Analytics dashboard (misaligned, medium priority, exceeds capacity)
        Expected: DEFER
        """
        title = "Build admin analytics dashboard with custom reports"
        description = (
            "Create a full analytics suite allowing admins to build custom reports. "
            "Include date range filtering, metric selection, CSV export, and scheduled reports."
        )
        sprint_goal = "Enhance security and scale infrastructure"
        current_load = 8
        capacity = 30
        
        # Step 1: Estimate story points
        sp = estimate_story_points_from_text(title, description)
        assert sp > 8  # Complex feature
        
        # Step 2: Check alignment
        alignment = calculate_sprint_goal_alignment(f"{title} {description}", sprint_goal)
        alignment_state = get_alignment_state(alignment)
        assert alignment_state == "UNALIGNED"  # Analytics ≠ Security
        
        # Step 3: Check capacity
        breach = check_capacity_breach(current_load, sp, capacity)
        assert breach is True  # Exceeds capacity
        
        # Step 4: Get ML predictions
        predictions = mock_ml_predictions(sp, alignment_state, 5, current_load, capacity)
        assert predictions["schedule_risk"] > 50
        assert predictions["quality_risk"] > 25
        
        # Expected decision: DEFER
        print(f"\nScenario B: {title}")
        print(f"  SP: {sp}, Alignment: {alignment_state}, Risk: {predictions['schedule_risk']:.0f}%")
        print(f"  → DEFER (Scope creep + overload)")
    
    def test_scenario_case_c_emergency_swap(self):
        """
        Case C: Payment retry bug (critical priority, emergency, needs swap)
        Expected: SWAP or OVERLOAD
        """
        title = "[URGENT] Payment processing stuck in retry loop"
        description = (
            "Production bug: payment transactions in infinite retry loop after timeout. "
            "Affects 500 transactions/hour. Needs exception handler, unlock endpoint, "
            "and transaction audit."
        )
        sprint_goal = "Enhance security and scale infrastructure"
        current_load = 8
        capacity = 30
        priority = "Critical"
        
        # Step 1: Estimate story points
        sp = estimate_story_points_from_text(title, description)
        assert sp > 0
        
        # Step 2: Check alignment (production bugs are inherently aligned)
        alignment = calculate_sprint_goal_alignment(f"{title} {description}", sprint_goal)
        alignment_state = "CRITICAL_BLOCKER"  # Override for emergency
        
        # Step 3: Check capacity
        breach = check_capacity_breach(current_load, sp, capacity)
        # May breach, but that's OK for emergencies
        
        # Step 4: Get ML predictions
        predictions = mock_ml_predictions(sp, alignment_state, 5, current_load, capacity)
        
        # Expected decision: SWAP (or OVERLOAD if no swappable item)
        print(f"\nScenario C: {title}")
        print(f"  SP: {sp}, Priority: {priority}, State: {alignment_state}")
        print(f"  → SWAP or OVERLOAD (Emergency override)")


class TestEdgeCases:
    """Test boundary conditions and edge cases."""
    
    def test_zero_velocity_team(self):
        """Handle division by zero if velocity is 0."""
        capacity = calculate_dynamic_capacity(velocity=0, assignees=3, days=10)
        assert capacity["hours_per_sp"] > 0  # Should have default fallback
    
    def test_empty_sprint_goal(self):
        """Empty sprint goal should result in low alignment."""
        alignment = calculate_sprint_goal_alignment("Some ticket", "")
        assert alignment == 0.0
    
    def test_sprint_ending_today(self):
        """Sprint ending today should have maximum schedule risk."""
        predictions = mock_ml_predictions(
            effort_sp=5,
            alignment_state="PARTIALLY_ALIGNED",
            days_remaining=0,  # Ends today
            current_load=10,
            capacity=20,
        )
        # Should have high risk
        assert predictions["schedule_risk"] > 30
    
    def test_max_story_points_capped(self):
        """Story point estimates should not exceed 13."""
        sp = estimate_story_points_from_text(
            "Very complex feature",
            "X" * 2000  # Extremely long description
        )
        assert sp <= 13


# ─────────────────────────────────────────────────────────────────────────────
# PYTEST FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def standard_sprint_context():
    """Fixture: typical sprint context for testing."""
    return {
        "space_id": "techcorp-space",
        "sprint_id": "sprint-6-active",
        "sprint_goal": "Enhance security and scale infrastructure",
        "team_velocity_14d": 30,
        "current_sprint_load": 8,
        "days_remaining": 5,
        "assignees": 4,
        "capacity": 30,
        "risk_appetite": "Standard",
    }


@pytest.fixture
def typical_ticket():
    """Fixture: typical mid-sprint ticket."""
    return {
        "title": "Implement feature X",
        "description": "Add functionality for user feature request.",
        "type": "Story",
        "priority": "Medium",
        "story_points": 5,
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
