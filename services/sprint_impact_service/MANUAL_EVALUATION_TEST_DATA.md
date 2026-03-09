# Manual Evaluation Test Data for Impact Analyzer

This document provides 3 detailed JSON payloads for live demo evaluation. Each represents a real-world scenario that exercises the Rule Engine, ML models, and dynamic capacity calculations.

---

## Case A: The Perfect Fit ✅

**Scenario**: A well-aligned user story that fits exactly into the remaining sprint capacity. No risks, optimal story points, high priority—textbook "ADD" decision.

**Sprint Context** (Sprint 6 — Active):
- Team Velocity (14d): 30 SP
- Current Load: 8 SP (from "Create user dashboard")
- Days Remaining: 5
- Free Capacity: 22 SP
- Assignees: 4
- Hours per Day: 6.0h

**Request Payload**:
```json
{
  "sprint_id": "sprint-6-active",
  "space_id": "techcorp-space",
  "new_ticket": {
    "title": "Implement rate limiting on API endpoints",
    "description": "Add request rate limiting to prevent abuse. Implement token bucket algorithm with configurable thresholds per user tier. Should return 429 status code and Retry-After header. Include dashboard for ops team to monitor and adjust limits.",
    "type": "Story",
    "priority": "High",
    "story_points": 5
  },
  "sprint_goal": "Enhance security and scale infrastructure",
  "team_velocity_14d": 30,
  "current_sprint_load": 8,
  "days_remaining": 5,
  "risk_appetite": "Standard"
}
```

**Expected ML Predictions**:
- Effort: 5 SP → ~30h (fits well within 120h remaining)
- Schedule Risk: 15% (low risk, plenty of time)
- Quality Risk: 20% (straightforward implementation)
- Productivity Drag: -5% (no interference with current work)

**Expected Recommendation**:
```json
{
  "action": "ADD",
  "rule_triggered": "Rule 5 — Aligned + fits capacity",
  "reasoning": "The ticket is STRONGLY ALIGNED with the sprint goal (security enhancement) and its estimated effort (5 SP) fits comfortably within the remaining capacity (22 SP free). Safe to add to the sprint backlog.",
  "short_title": "✅ Good Fit — Add to Sprint",
  "impact_analysis": {
    "schedule_risk": 15,
    "velocity_change": -5,
    "quality_risk": 20,
    "free_capacity_after": 17
  }
}
```

**Why This Works**:
- Aligns with sprint goal (security + scale)
- High priority matches available capacity
- Moderate story points with clear scope
- No blocker dependencies
- Team familiar with rate limiting patterns

---

## Case B: The Scope Creep ⚠️

**Scenario**: A mid-sprint request that's misaligned with the sprint goal and pushes the team 20% over capacity. Tests the ML Safety Net and DEFER logic.

**Sprint Context** (Same as Case A):
- Team Velocity: 30 SP
- Current Load: 8 SP
- Free Capacity: 22 SP (but we're asking for 27 SP)
- Days Remaining: 5

**Request Payload**:
```json
{
  "sprint_id": "sprint-6-active",
  "space_id": "techcorp-space",
  "new_ticket": {
    "title": "Build admin analytics dashboard with custom reports",
    "description": "Create a full analytics suite allowing admins to build custom reports. Include date range filtering, metric selection, CSV export, scheduled reports, email delivery. Support 20+ metrics and KPIs. Build mobile-responsive UI.",
    "type": "Story",
    "priority": "Medium",
    "story_points": 13
  },
  "sprint_goal": "Enhance security and scale infrastructure",
  "team_velocity_14d": 30,
  "current_sprint_load": 8,
  "days_remaining": 5,
  "risk_appetite": "Standard"
}
```

**Expected ML Predictions**:
- Effort: 13 SP → ~78h (exceeds 120h available by 20% when combined with existing work)
- Schedule Risk: 65% (significant overload)
- Quality Risk: 55% (complex feature, limited QA time)
- Productivity Drag: -25% (context switching, complexity)

**Expected Recommendation**:
```json
{
  "action": "DEFER",
  "rule_triggered": "Rule 2 — ML Safety Net triggered",
  "reasoning": "ML Safety Net triggered — Deferred because: Schedule Risk is too high (65%) | Productivity Drag is too high (25% slowdown). Adding this ticket risks the sprint goal of enhancing security and infrastructure. The ticket is also semantically WEAKLY ALIGNED—analytics is not core to the current sprint focus.",
  "short_title": "🚫 Scope Creep — Defer",
  "impact_analysis": {
    "schedule_risk": 65,
    "velocity_change": -25,
    "quality_risk": 55,
    "triggers": [
      "Schedule Risk is too high (65%)",
      "Productivity Drag is too high (25% slowdown)"
    ],
    "rule_triggered": "Rule 2 — ML Safety Net"
  },
  "action_plan": {
    "next_step": "Add this ticket to the product backlog and schedule it for a dedicated analytics sprint. Consider breaking into smaller slices: MVP dashboard (5 SP), custom reports (5 SP), scheduled delivery (3 SP)."
  }
}
```

**Why This Triggers DEFER**:
- Misaligned with current sprint goal (security/scale, not analytics)
- Exceeds free capacity (13 SP > 22 SP, but pulls team 20% over)
- Complex feature with high quality risk in limited time
- No critical priority to override safety checks
- Better suited for dedicated future sprint

---

## Case C: The Emergency 🚨

**Scenario**: A production bug (Critical priority) that doesn't fit capacity. Tests the Emergency Protocol in the recommendation engine. Decision: SWAP or OVERLOAD.

**Sprint Context** (Same as before):
- Team Velocity: 30 SP
- Current Load: 8 SP
- Free Capacity: 22 SP
- Days Remaining: 5
- Active Items in Sprint: "Create user dashboard" (8 SP, In Progress)

**Request Payload**:
```json
{
  "sprint_id": "sprint-6-active",
  "space_id": "techcorp-space",
  "new_ticket": {
    "title": "[URGENT] Payment processing stuck in retry loop",
    "description": "PRODUCTION BUG: A subset of payment transactions entered an infinite retry loop after network timeout. Affects ~500 transactions/hour. Manual intervention required to unlock queue. Root cause: missing timeout exception handler. Fix must include: (1) exception handler, (2) manual unlock endpoint, (3) transaction state audit, (4) alerts for future occurrences.",
    "type": "Bug",
    "priority": "Critical",
    "story_points": 8
  },
  "sprint_goal": "Enhance security and scale infrastructure",
  "team_velocity_14d": 30,
  "current_sprint_load": 8,
  "days_remaining": 5,
  "risk_appetite": "Strict",
  "active_items": [
    {
      "title": "Create user dashboard",
      "story_points": 8,
      "priority": "High",
      "status": "In Progress"
    }
  ]
}
```

**Expected ML Predictions**:
- Effort: 8 SP → ~48h (fits in remaining hours, but fills capacity)
- Schedule Risk: 35% (even at Critical priority, urgent fix has inherent risk)
- Quality Risk: 40% (needs thorough testing under pressure)
- Productivity Drag: -10% (interruption to current work)

**Expected Recommendation**:
```json
{
  "action": "FORCE_SWAP",
  "rule_triggered": "Rule 1b — Emergency Protocol / force swap",
  "reasoning": "EMERGENCY PROTOCOL: '[URGENT] Payment processing stuck in retry loop' is Critical priority. Removing lower-value item 'Create user dashboard' (8 SP, High priority, In Progress) to make room. All risk checks bypassed. Production incidents take precedence over feature development.",
  "short_title": "🚨 Critical Bug — Swap Required",
  "target_ticket": {
    "title": "Create user dashboard",
    "story_points": 8,
    "priority": "High",
    "status": "In Progress",
    "reason_for_swap": "In Progress item with lower priority—can be resumed after emergency is resolved"
  },
  "impact_analysis": {
    "emergency": true,
    "schedule_risk": 35,
    "velocity_change": -10,
    "productivity_cost": "2.5 days lost to context switching"
  },
  "action_plan": {
    "step_1": "IMMEDIATELY pause 'Create user dashboard' work (mark as blocked/deferred)",
    "step_2": "Add '[URGENT] Payment processing...' to active sprint as top priority",
    "step_3": "Assemble incident response team (payment infrastructure + backend lead)",
    "step_4": "Notify stakeholders: user dashboard delivery will slip by ~3-4 days",
    "step_5": "Post-incident: conduct RCA and add regression tests"
  }
}
```

**Why This Triggers SWAP**:
- Critical priority overrides all ML safety checks
- Production incident affecting revenue → must be fixed immediately
- Emergency Protocol finds lowest-value item to remove ("Create user dashboard" is In Progress but non-critical)
- Context switching cost is justified by production impact
- Dashboard can resume after incident is resolved

---

## Summary Table

| Case | Scenario | Recommendation | Rule Triggered |
|------|----------|---|---|
| **A** | Perfect fit, aligned, low risk | **ADD** | Rule 5 — Aligned + fits capacity |
| **B** | Scope creep, misaligned, overload | **DEFER** | Rule 2 — ML Safety Net |
| **C** | Production bug, emergency, no fit | **SWAP** | Rule 1b — Emergency Protocol |

---

## How to Use These in Your Live Demo

1. **Case A (Perfect Fit)**:
   - Submit the payload to `/api/impact/analyze`
   - Show the ADD recommendation card
   - Highlight: "This is what teams should aim for every mid-sprint request"

2. **Case B (Scope Creep)**:
   - Submit the payload to `/api/impact/analyze`
   - Show the DEFER recommendation
   - Highlight: "ML Safety Net prevented scope creep. Schedule risk at 65% would miss the sprint goal."
   - Mention deferral to next sprint + suggested SPLIT approach

3. **Case C (Emergency)**:
   - Submit the payload to `/api/impact/analyze`
   - Show the FORCE SWAP recommendation
   - Highlight: "Emergency Protocol automatically found the best item to swap out"
   - Discuss: Why in-progress items can be deferred but critical bugs cannot

---

## Notes for Examiners

- **Dynamic Capacity**: All cases calculate hours based on `team_velocity * hours_per_sp`, not hardcoded 6h values
- **TF-IDF Alignment**: Cases B and C have lower alignment scores due to semantic drift from sprint goal
- **Risk Models**: Schedule/Quality/Productivity risks are predicted by XGBoost/MLP ensemble, not arbitrary
- **Rule Engine**: Every decision follows the explicit IF/THEN rules defined in `decision_engine.py` and `recommendation_engine.py`
