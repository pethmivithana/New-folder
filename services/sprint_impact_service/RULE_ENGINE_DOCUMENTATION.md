# Rule Engine Documentation

## Overview

The **Sprint Replanning & Impact Analyzer** uses a **deterministic, priority-ordered rule engine** to generate one of four recommendations:

- **ADD**: Accept the ticket into the current sprint
- **DEFER**: Reject to the backlog for future planning
- **SPLIT**: Break into smaller deliverables across sprints
- **SWAP**: Remove a lower-priority item to make room

Every decision is made by evaluating **explicit IF/THEN rules in priority order**. The **first matching rule wins**, ensuring consistency and explainability for live demonstrations.

---

## Rule Priority Order

Rules are evaluated strictly in order. Once a rule matches, its action is returned immediately. No rule is evaluated after a match.

```
┌─ Rule 0: Check if sprint is ending
├─ Rule 0.5: Emergency Protocol (Critical priority override)
├─ Rule 1: Monster ticket too large for remaining days
├─ Rule 2: ML Safety Net (multi-signal risk breach)
├─ Rule 3: Enough capacity? → ADD
├─ Rule 4: Sprint full → try SWAP
└─ Rule 5: Sprint full, no swap → DEFER
```

---

## Rule Definitions

### Rule 0: Sprint Almost Over
**Condition**: `days_remaining < 2` AND `priority ≠ Critical`

**Action**: `DEFER`

**Reasoning**:
If the sprint ends in fewer than 2 days and the ticket is not Critical priority, accept it to the backlog instead. There's insufficient runway for new work unless it's a production emergency.

**Example**:
- Sprint ends tomorrow
- Request: "Add report feature" (Medium priority, 5 SP)
- Decision: **DEFER** — too late to start new work
- Message: "Sprint ends in 1 day(s). Too risky to add non-critical work this late."

---

### Rule 0.5: Emergency Protocol
**Condition**: `priority in ("Critical", "Highest")`

**Action**: `FORCE_SWAP` or `OVERLOAD`

**Reasoning**:
Critical/production tickets bypass all ML risk checks. They **must** be added immediately. If capacity allows, add normally. If not, find the lowest-priority "To Do" item and remove it. If no item can be removed (all in progress), accept the overload.

**Critical Priority Definition**:
- Production bugs affecting revenue/users
- Security vulnerabilities
- Data loss scenarios
- System outages
- Any P0 incident

**Subcase A: FORCE_SWAP**
- Condition: Critical ticket + capacity insufficient + swap candidate exists
- Swap criteria: Find "To Do" item with (lowest_priority, fewest_sp)
- Context switch cost: ~0.5 days (interrupted work)
- Action: Remove swap candidate, add critical ticket

**Subcase B: OVERLOAD**
- Condition: Critical ticket + capacity insufficient + no swap candidate
- Decision: Add anyway, accept sprint overload
- Communication: Notify stakeholders of increased schedule risk

**Example A (SWAP)**:
- Current Sprint: 25/30 SP, items = [
  - "Create dashboard" (8 SP, High, In Progress)
  - "Write docs" (3 SP, Low, To Do)
  ]
- Request: "[P0 BUG] Payment timeout loop" (8 SP, Critical)
- Decision: **SWAP** — remove "Write docs" (lowest priority)
- Message: "EMERGENCY PROTOCOL: Removing 'Write docs' to make room for critical bug."

**Example B (OVERLOAD)**:
- Current Sprint: 30/30 SP, all items In Progress
- Request: "[P0 BUG] Database corruption detected" (5 SP, Critical)
- Decision: **OVERLOAD** — no item can be removed
- Message: "EMERGENCY PROTOCOL: No removable item. Accepting sprint overload."

---

### Rule 1: Monster Ticket Too Large
**Condition**:
- `story_points >= 13` (large ticket threshold)
- AND `days_remaining < 10` (insufficient time)

**Action**: `SPLIT`

**Reasoning**:
Large tickets (13 SP = full sprint week of work) cannot realistically complete in less than 10 days. Break them into smaller, deliverable slices.

**Recommendation Approach**:
Split into ~50/50 or by logical delivery phases:
- **Slice A**: MVP or foundational work (~5-8 SP, 1st sprint)
- **Slice B**: Enhancement or completion (~5-8 SP, 2nd sprint)

**Example**:
- Request: "Rebuild payment system architecture" (13 SP)
- Days Remaining: 5
- Decision: **SPLIT**
- Message: "Too large (13 SP) to complete in 5 remaining days. Split into 'Phase 1: Infrastructure' (8 SP) and 'Phase 2: Migration' (5 SP)."

---

### Rule 2: ML Safety Net — Multi-Signal Risk
**Condition**: Any of the following thresholds exceeded (varies by risk appetite):

| Risk Appetite | Schedule Risk | Productivity Drag | Quality Risk |
|---|---|---|---|
| **Strict** | > 30% | < -20% | > 60% |
| **Standard** | > 50% | < -30% | > 70% |
| **Lenient** | > 70% | < -40% | > 80% |

**Action**: `DEFER`

**Reasoning**:
ML models predict three risk categories. If **any one** exceeds the threshold for the team's risk appetite, the ticket is too risky to include. Defer to the backlog.

**Risk Signals Explained**:

1. **Schedule Risk** (0–100%)
   - Probability that the ticket will spill into the next sprint
   - Calculated from: effort, capacity, days remaining, complexity
   - Threshold: Varies by risk appetite (30%–70%)
   - High risk = missed sprint goal likely

2. **Productivity Drag** (−100% to +100%)
   - Estimated change in team velocity if ticket is added
   - Calculated from: context switching, team familiarity, complexity
   - Threshold: More negative is worse (drag < -20% to -40%)
   - Context switching interrupts current flow

3. **Quality Risk** (0–100%)
   - Probability of defects or rework if ticket is added under time pressure
   - Calculated from: complexity, test coverage needed, domain expertise
   - Threshold: Varies by risk appetite (60%–80%)
   - High QA pressure = buggy delivery

**Triggering Logic**:
```python
if schedule_risk > threshold_schedule:
    trigger("Schedule Risk is too high")
if velocity_change < threshold_productivity:
    trigger("Productivity Drag is too high")
if quality_risk > threshold_quality:
    trigger("Quality Risk is too high")

if any(triggers):
    return DEFER
```

**Example (Standard Risk Appetite)**:
- Request: Analytics dashboard (13 SP, Medium priority)
- ML Predictions:
  - Schedule Risk: 65% (> 50% threshold) ✗
  - Productivity Drag: -35% (< -30% threshold) ✗
  - Quality Risk: 72% (< 70% threshold) ✓
- Decision: **DEFER**
- Message: "ML Safety Net triggered — Deferred because: Schedule Risk is too high (65%) | Productivity Drag is too high (35% slowdown)."

---

### Rule 3: Capacity Check
**Condition**: `free_capacity >= story_points` AND no ML risks triggered

**Action**: `ADD`

**Reasoning**:
If capacity is available and ML models give the all-clear, adding the ticket is safe. No blocker exists.

**Capacity Formula**:
```
free_capacity = team_velocity - current_sprint_load
(all in story points)
```

**Example**:
- Team velocity: 30 SP
- Current sprint load: 8 SP
- Free capacity: 22 SP
- Request: Rate limiting feature (5 SP)
- Decision: **ADD** (5 SP ≤ 22 SP)
- Message: "Sprint has 22 SP free and all ML signals within safe thresholds. Safe to add."

---

### Rule 4: Sprint Full → Try SWAP
**Condition**:
- `free_capacity < story_points` (no room)
- AND `priority in ("High", "Critical")` (must include)
- AND swap candidate exists (a lower-priority item)

**Action**: `SWAP`

**Reasoning**:
The ticket is high-value and aligned, but doesn't fit. Remove a lower-priority, lower-SP item to make room. The trade-off is justified.

**Swap Candidate Selection**:
Find the item that minimizes disruption:
1. **Exclude**: Done/Completed items, high-priority items, critical path blockers
2. **Score** remaining items: `score = (priority_rank_diff) + (sp_diff)`
3. **Select**: Lowest score = best candidate to swap

**Context Switch Cost**:
- If item is **"To Do"**: ~0.5 days cost (just backlog it)
- If item is **"In Progress"**: ~2.5 days cost (person needs to resume later)

**Example**:
- Current Sprint: 25/30 SP
  - "Create user dashboard" (8 SP, High, In Progress)
  - "Write API docs" (3 SP, Medium, To Do)
- Request: "Add 2FA security feature" (8 SP, High)
- Swap Candidate: "Write API docs" (lowest priority, smallest SP)
- Decision: **SWAP**
- Message: "Sprint at capacity. Swapping out 'Write API docs' (3 SP, Medium) for 'Add 2FA' (8 SP, High). Context switch cost: ~0.5 days."

---

### Rule 5: Sprint Full → No Swap Candidate
**Condition**: `free_capacity < story_points` AND no suitable swap candidate exists

**Action**: `DEFER`

**Reasoning**:
The ticket doesn't fit and there's no lower-priority item to remove. Deferring is the safe option to protect the sprint goal.

**Example**:
- Current Sprint: 28/30 SP (all items critical or in progress)
- Request: "Analytics dashboard" (10 SP, Medium)
- Available swaps: None (all remaining items are High/Critical or In Progress)
- Decision: **DEFER**
- Message: "Sprint is full (28/30 SP) and no suitable lower-priority item to swap. Add to backlog for next sprint."

---

## Risk Appetite Settings

Teams can override thresholds for their risk tolerance. Default: **Standard**.

### Strict (Conservative)
- For teams that prioritize schedule certainty and quality
- Typical: Regulated industries (fintech, healthcare)
- High confidence required for mid-sprint work
- Thresholds:
  - Schedule Risk > 30%? DEFER
  - Productivity Drag < -20%? DEFER
  - Quality Risk > 60%? DEFER

### Standard (Balanced)
- **DEFAULT** — works for most teams
- Moderate confidence required
- Thresholds:
  - Schedule Risk > 50%? DEFER
  - Productivity Drag < -30%? DEFER
  - Quality Risk > 70%? DEFER

### Lenient (Permissive)
- For teams with high velocity and good error recovery
- Typical: Startups with fast iteration cycles
- Allow more mid-sprint additions
- Thresholds:
  - Schedule Risk > 70%? DEFER
  - Productivity Drag < -40%? DEFER
  - Quality Risk > 80%? DEFER

---

## Special Cases & Exceptions

### Case: Split vs. Swap
**When to SPLIT** (not SWAP):
- Ticket is > 8 SP AND days < 10
- Ticket is aligned but too large
- Better to deliver incrementally than drop other work

**When to SWAP** (not SPLIT):
- Ticket is well-aligned and high-value
- A lower-priority item exists to remove
- Team prefers focused scope over continuation

### Case: Multiple Risks Triggered
If **multiple ML signals** exceed thresholds, DEFER with a summary:
```
"ML Safety Net triggered — Deferred because:
  • Schedule Risk is too high (65%)
  • Productivity Drag is too high (35% slowdown)
This ticket poses multiple risks to the sprint goal."
```

### Case: Alignment State Mapping
ML model outputs alignment as a similarity score (0.0–1.0). Map to semantic states:
- **0.7–1.0**: STRONGLY_ALIGNED
- **0.5–0.7**: PARTIALLY_ALIGNED
- **0.3–0.5**: WEAKLY_ALIGNED
- **0.0–0.3**: UNALIGNED

In Rule 2, UNALIGNED tickets **always DEFER** (scope creep protection).

---

## Implementation Details

### Key Formulas

**1. Dynamic Capacity**
```
Total_Sprint_Hours = days_remaining * focus_hours_per_day * num_assignees
Hours_Per_SP = Total_Sprint_Hours / historical_velocity
Effective_Capacity = velocity * (assignees / base_assignees)
```

**2. Free Capacity**
```
free_capacity = team_velocity - current_sprint_load
(in story points)
```

**3. Schedule Risk** (XGBoost model)
```
schedule_risk = f(effort_sp, capacity_load, days_remaining, complexity)
Output: 0–100%
```

**4. Productivity Drag** (MLP neural net)
```
velocity_change = f(context_switches, team_familiarity, alignment, complexity)
Output: -100% to +100%
```

**5. Quality Risk** (XGBoost model)
```
quality_risk = f(complexity, test_coverage_needed, time_pressure)
Output: 0–100%
```

---

## Presentation for Examiners

### Flow Chart
```
Request comes in
    ↓
Rule 0: Sprint ending? → DEFER
    ↓
Rule 0.5: Critical? → SWAP/OVERLOAD
    ↓
Rule 1: > 13 SP & < 10 days? → SPLIT
    ↓
Rule 2: ML signals exceeded? → DEFER
    ↓
Rule 3: Capacity available? → ADD
    ↓
Rule 4: Sprint full, high-value? → SWAP
    ↓
Rule 5: Fallback → DEFER
```

### Key Talking Points for Demo
1. **Deterministic**: Same input always produces same output (no randomness)
2. **Explainable**: Every rule is written in plain language, understandable to non-technical stakeholders
3. **Context-Aware**: Considers team velocity, capacity, alignment, and risk appetite
4. **Emergency-Ready**: Rule 0.5 ensures production bugs are never blocked by process
5. **ML-Informed**: Rules 2–5 integrate XGBoost/MLP predictions for schedule/quality risk

### Live Demo Sequence
1. **Show Case A (Perfect Fit)**
   - "This is the ideal: aligned ticket, fits capacity, all green lights → ADD"
2. **Show Case B (Scope Creep)**
   - "This looks tempting (high priority), but ML safety net caught the risk → DEFER"
   - "Watch how schedule risk jumped from 15% to 65% due to capacity constraints"
3. **Show Case C (Emergency)**
   - "Production bug overrides everything → automatically found the swap"
   - "No manual triage needed; emergency protocol is built-in"

---

## Debugging & Tuning

### Adjusting Thresholds
If teams are getting DEFER too often:
- Shift from **Strict** to **Standard** or **Lenient** risk appetite
- Or adjust thresholds in `recommendation_engine.py`:
  ```python
  def get_thresholds_by_appetite(risk_appetite):
      thresholds["Standard"]["schedule_risk_threshold"] = 50.0  # Default
      # Lower number = stricter, higher number = more permissive
  ```

### Tuning Swap Logic
If swaps are too aggressive:
- Increase `status_penalty` in `_find_swap_candidate()` to avoid In Progress items
- Or require `priority >= "Medium"` before allowing swap

### ML Model Performance
If ML predictions seem off:
- Check `feature_engineering.py` for feature calculations
- Verify model loading in `model_loader.py`
- Review XGBoost/MLP parameters in `ml_models/`

---

## References

- **Decision Engine**: `decision_engine.py` (Rule 0–5 logic)
- **Recommendation Engine**: `recommendation_engine.py` (Risk appetite, SWAP selection)
- **Feature Engineering**: `feature_engineering.py` (ML input preparation)
- **Impact Predictor**: `impact_predictor.py` (XGBoost/MLP output formatting)
- **Test Suite**: `test_sprint_logic.py` (Validation of all rules)
- **Manual Test Cases**: `MANUAL_EVALUATION_TEST_DATA.md` (Live demo payloads)
