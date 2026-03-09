# Live Demo Cheat Sheet

**Print this before your evaluation.** Quick reference for 3 API calls and expected outcomes.

---

## Pre-Demo Setup

### 1. Database Seeded?
```bash
python enhanced_seed_test_data.py
```
✓ Confirm: "1 Space, 6 Sprints, 8 Backlog Items created"

### 2. Backend Running?
```bash
python services/sprint_impact_service/main.py
```
✓ Confirm: "Uvicorn running on http://localhost:8000"

### 3. Tests Pass?
```bash
pytest test_sprint_logic.py -v -k "scenario" --tb=short
```
✓ Confirm: "3 integration tests pass"

---

## Case A: Perfect Fit ✅

**Talking Point**: "This is what every sprint needs—aligned, high-value, fits capacity."

### API Request
```bash
curl -X POST http://localhost:8000/api/impact/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sprint_id": "sprint-6-active",
    "space_id": "techcorp-space",
    "new_ticket": {
      "title": "Implement rate limiting on API endpoints",
      "description": "Add request rate limiting with token bucket algorithm. Support per-user-tier limits.",
      "type": "Story",
      "priority": "High",
      "story_points": 5
    },
    "sprint_goal": "Enhance security and scale infrastructure",
    "team_velocity_14d": 30,
    "current_sprint_load": 8,
    "days_remaining": 5,
    "risk_appetite": "Standard"
  }'
```

### Expected Response
```json
{
  "action": "ADD",
  "rule_triggered": "Rule 5 — Aligned + fits capacity",
  "reasoning": "The ticket is STRONGLY ALIGNED with the sprint goal and its estimated effort fits comfortably within the remaining capacity. Safe to add.",
  "short_title": "✅ Good Fit — Add to Sprint",
  "impact_analysis": {
    "schedule_risk": 15,
    "velocity_change": -5,
    "quality_risk": 20,
    "free_capacity_after": 17
  }
}
```

### Key Talking Points
- ✓ **Alignment**: High (rate limiting = security)
- ✓ **Capacity**: 5 SP < 22 SP free
- ✓ **Risk**: All ML signals green (< thresholds)
- → **Decision**: ADD immediately

---

## Case B: Scope Creep ⚠️

**Talking Point**: "This looks tempting—high-priority feature—but ML caught the problem."

### API Request
```bash
curl -X POST http://localhost:8000/api/impact/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sprint_id": "sprint-6-active",
    "space_id": "techcorp-space",
    "new_ticket": {
      "title": "Build admin analytics dashboard with custom reports",
      "description": "Create analytics suite: date filtering, CSV export, scheduled reports, email delivery. Support 20+ metrics.",
      "type": "Story",
      "priority": "Medium",
      "story_points": 13
    },
    "sprint_goal": "Enhance security and scale infrastructure",
    "team_velocity_14d": 30,
    "current_sprint_load": 8,
    "days_remaining": 5,
    "risk_appetite": "Standard"
  }'
```

### Expected Response
```json
{
  "action": "DEFER",
  "rule_triggered": "Rule 2 — ML Safety Net triggered",
  "reasoning": "ML Safety Net triggered — Deferred because: Schedule Risk is too high (65%) | Productivity Drag is too high (25% slowdown). Adding this ticket risks the sprint goal.",
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
  }
}
```

### Key Talking Points
- ✗ **Alignment**: Low (analytics ≠ security goal)
- ✗ **Capacity**: 13 SP > 22 SP? Actually fits, but...
- ✗ **Risk**: ML predicted 65% schedule risk (exceeds 50% threshold)
- ✗ **Context Switch**: -25% productivity drag from complexity
- → **Decision**: DEFER to next sprint

**Show This**: "Watch how schedule risk jumped from 15% (Case A) to 65% (Case B). Same capacity, but different complexity."

---

## Case C: Emergency 🚨

**Talking Point**: "Production bug—all bets are off. Emergency Protocol takes over."

### API Request
```bash
curl -X POST http://localhost:8000/api/impact/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sprint_id": "sprint-6-active",
    "space_id": "techcorp-space",
    "new_ticket": {
      "title": "[URGENT] Payment processing stuck in retry loop",
      "description": "P0 BUG: Payments trapped in infinite retry after timeout. Affects ~500 transactions/hour. Need: exception handler, unlock endpoint, transaction audit.",
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
  }'
```

### Expected Response
```json
{
  "action": "FORCE_SWAP",
  "rule_triggered": "Rule 0.5 — Emergency Protocol / force swap",
  "reasoning": "EMERGENCY PROTOCOL: '[URGENT] Payment processing...' is Critical priority. Removing 'Create user dashboard' (8 SP, High priority) to make room. All risk checks bypassed.",
  "short_title": "🚨 Critical Bug — Swap Required",
  "target_ticket": {
    "title": "Create user dashboard",
    "story_points": 8,
    "priority": "High",
    "status": "In Progress",
    "reason_for_swap": "Lower priority; can resume after emergency resolved"
  },
  "impact_analysis": {
    "emergency": true,
    "schedule_risk": 35,
    "productivity_cost": "2.5 days lost to context switching"
  },
  "action_plan": {
    "step_1": "IMMEDIATELY pause 'Create user dashboard'",
    "step_2": "Add payment bug to active sprint as top priority",
    "step_3": "Assemble incident response team",
    "step_4": "Notify stakeholders of 3-4 day dashboard delay"
  }
}
```

### Key Talking Points
- 🚨 **Priority**: Critical (overrides everything)
- 🔄 **Swap**: Automatically found lowest-value item ("Create dashboard")
- ⏱️ **Context Cost**: 2.5 days (item is In Progress)
- ✓ **Justification**: Production revenue impact > feature delivery delay
- → **Decision**: FORCE_SWAP automatically

**Show This**: "The system didn't need to be told what to do. Emergency Protocol found the swap automatically. No manual triage needed."

---

## Rule Priority Flowchart (Show During Demo)

```
┌─────────────────────────────────────┐
│ Ticket arrives mid-sprint           │
└──────────────┬──────────────────────┘
               ↓
    ┌──────────────────────┐
    │ Rule 0: Ending soon? │
    │ (< 2 days left)      │
    └──────┬───────────────┘
           ├─ YES → DEFER
           │
           └─ NO ↓
              ┌──────────────────────────┐
              │ Rule 0.5: Critical?      │
              │ (P0, production bug)     │
              └──────┬───────────────────┘
                     ├─ YES → SWAP/OVERLOAD
                     │
                     └─ NO ↓
                        ┌──────────────────────┐
                        │ Rule 1: Monster?     │
                        │ (>13 SP, <10 days)   │
                        └──────┬───────────────┘
                               ├─ YES → SPLIT
                               │
                               └─ NO ↓
                                  ┌──────────────────────┐
                                  │ Rule 2: Risk breach? │
                                  │ (ML signals)         │
                                  └──────┬───────────────┘
                                         ├─ YES → DEFER
                                         │
                                         └─ NO ↓
                                            ┌──────────────────┐
                                            │ Rule 3: Fits?    │
                                            │ (Capacity check) │
                                            └──────┬───────────┘
                                                   ├─ YES → ADD
                                                   │
                                                   └─ NO ↓
                                                      ┌──────────────┐
                                                      │ DEFER / SWAP │
                                                      └──────────────┘
```

---

## Timing Guide

| Section | Time | Notes |
|---------|------|-------|
| **Setup** | 2 min | Run seed script, verify backend |
| **Intro** | 1 min | "Mid-sprint requests are inevitable..." |
| **Case A Demo** | 2 min | "Perfect fit—aligned and green" |
| **Case B Demo** | 3 min | "ML caught scope creep we'd miss manually" |
| **Case C Demo** | 2 min | "Emergency Protocol—automatic swap" |
| **Rule Engine** | 2 min | Show flowchart + decision logic |
| **Q&A** | 3 min | Examiners' questions |
| **TOTAL** | ~15 min | Manageable, comprehensive |

---

## If Something Goes Wrong

### API timeout?
```bash
# Check backend is running
curl http://localhost:8000/api/health

# If not, restart
python services/sprint_impact_service/main.py
```

### Wrong recommendation?
1. **Check alignment**: Is ticket semantically related to sprint goal?
2. **Check capacity**: Are we > 50% loaded?
3. **Check ML predictions**: What are schedule/quality risk scores?
4. Check `RULE_ENGINE_DOCUMENTATION.md` for rule priority

### Tests failing?
```bash
pytest test_sprint_logic.py::TestIntegrationScenarios -v --tb=short
```
(Run just the 3 integration tests)

---

## Talking Points Summary

**Opening** (30 sec):
"Mid-sprint change requests are the #1 reason sprint goals fail. Our system uses ML risk prediction and transparent rules to decide: ADD, DEFER, SPLIT, or SWAP."

**Case A** (1 min):
"This is the ideal: aligned, fits capacity, all safe. System says ADD."

**Case B** (2 min):
"This looks tempting, but ML models see high schedule risk and productivity drag. Deferring protects the sprint goal."

**Case C** (1 min):
"Production emergency? All rules override. System automatically found a swap candidate and calculated context-switch cost."

**Closing** (30 sec):
"Result: sprint goals stay intact, teams avoid context switching chaos, and decisions are transparent and explainable."

---

**You've got this! 🚀**

Remember:
- ✓ Seed the database first
- ✓ Show Case A → Case B → Case C in sequence
- ✓ Point out how ML risk scores differ (15% vs 65% schedule risk)
- ✓ Explain Rule 0.5 Emergency Protocol for Case C
- ✓ Let examiners ask questions—the system is well-designed
