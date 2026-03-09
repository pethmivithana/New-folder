# Impact Analysis Testing Requirements

Use this document to verify that impact analysis recommendations are working correctly after seeding test data.

## Setup

```bash
cd services/sprint_impact_service
python test_data.py
python main.py
```

---

## Test Case 1: FinTech Project - ADD Decision
**Project**: FinTech Payment Orchestration (Sprint 4)

**Request Body** (POST /api/backlog-items/):
```json
{
  "title": "Implement Liquidity Pool Integration for DEX Swaps",
  "description": "Connect to Uniswap V3 liquidity pools with slippage protection mechanisms and MEV protection",
  "type": "Story",
  "priority": "High",
  "story_points": 8,
  "space_id": "<FINTECH_SPACE_ID>",
  "sprint_id": "<SPRINT_4_ID>"
}
```

**Expected Decision**: **ADD** ✓
- **Reasoning**: 
  - Active sprint has 30 SP capacity, 26 SP allocated → 4 SP free
  - Item requests 8 SP → requires evaluation
  - Velocity trends: Sprint 1 (28 SP), Sprint 2 (35 SP spike), Sprint 3 (20 SP) → Avg ~27.7 SP
  - Days remaining in sprint: 11 days
  - Risk appetite: "Strict" → Higher threshold but manageable
  - **Recommendation**: ADD if team capacity absorbs it (consider velocity spike pattern)

**Alternative Test**: Reduce story_points to 5 → Should definitely ADD

---

## Test Case 2: Identity Project - DEFER Decision (Scope Creep)
**Project**: Identity Management (Sprint 3 - Active)

**Request Body**:
```json
{
  "title": "Implement Advanced Anomaly Detection with ML Models",
  "description": "Deploy machine learning models to detect suspicious login patterns using isolation forests and DBSCAN clustering algorithms for identity fraud prevention",
  "type": "Story",
  "priority": "Medium",
  "story_points": 13,
  "space_id": "<IDENTITY_SPACE_ID>",
  "sprint_id": "<SPRINT_3_ID>"
}
```

**Expected Decision**: **DEFER** ⚠️
- **Reasoning**:
  - Sprint 3: 28 SP capacity, 18 SP allocated → 10 SP free
  - Item requests 13 SP → exceeds free capacity
  - This is **scope creep**: adding 13 SP to remaining 10 SP capacity
  - Velocity trend: Sprint 1 (30 SP), Sprint 2 (32 SP) → Stable ~31 SP
  - Days remaining: 11 days
  - **ML Safety Net**: Flags as high-risk (65%+ schedule risk)
  - **Recommendation**: DEFER to next sprint

---

## Test Case 3: Healthcare Project - SWAP Decision (Critical Bug)
**Project**: Healthcare Analytics (Sprint 3 - Active)

**Request Body** (POST to create bug + request SWAP):
```json
{
  "title": "Critical: HIPAA Query Engine Memory Leak in Production",
  "description": "Production incident: federated query engine consuming unbounded memory on large cohort selections, causing OOM crashes affecting patient data retrieval for 500+ concurrent users",
  "type": "Bug",
  "priority": "Critical",
  "story_points": 8,
  "space_id": "<HEALTHCARE_SPACE_ID>",
  "sprint_id": null
}
```

**Then Call Recommendation Engine** with swap request:
```
GET /api/sprints/<SPRINT_3_ID>/impact-analysis?action=SWAP&item_story_points=8&priority=Critical
```

**Expected Decision**: **SWAP** ⚡
- **Reasoning**:
  - Critical priority bug (production incident)
  - Healthcare domain: HIPAA regulation compliance critical
  - Risk appetite: "Strict" → Prioritizes stability over velocity
  - Current sprint has: "Implement Cohort Definition DSL" (3 SP, Low priority) → Perfect swap candidate
  - **Recommendation**: SWAP the low-priority 3 SP task, absorb 8 SP bug (escalate to 11 SP in sprint)
  - **Output**: Recommend swapping out "Cohort Definition DSL" task

---

## Test Case 4: FinTech Project - SPLIT Decision
**Project**: FinTech (Sprint 4 - Active)

**Request Body**:
```json
{
  "title": "Implement Zero-Knowledge Proofs for Transaction Privacy",
  "description": "Engineer zk-SNARK implementation for proving payment authenticity without revealing transaction amounts, using circom framework and trusted ceremony results",
  "type": "Story",
  "priority": "High",
  "story_points": 21,
  "space_id": "<FINTECH_SPACE_ID>",
  "sprint_id": "<SPRINT_4_ID>"
}
```

**Expected Decision**: **SPLIT** ✂️
- **Reasoning**:
  - Sprint 4: 32 SP capacity, 26 SP allocated → 6 SP free
  - Item requests 21 SP → Way exceeds free capacity
  - BUT high priority and strategic (Zero-Knowledge Proofs for privacy)
  - **Too large for single sprint**: Should recommend splitting into multiple 5-8 SP chunks
  - **Recommendation**: SPLIT into 2-3 smaller stories:
    - Part 1: "Research & POC zk-SNARK Libraries" (5 SP)
    - Part 2: "Implement Circuit for Transaction Privacy" (8 SP)
    - Part 3: "Integration & Testing" (8 SP)

---

## Test Case 5: Identity Project - Velocity Variance Analysis
**Scenario**: Test system's ability to recognize velocity patterns

**Observed Pattern from seeded data**:
- Sprint 1: 30 SP completed (average team)
- Sprint 2: 32 SP completed (team ramp-up)
- Sprint 3: 18 SP active (some spillover expected)

**Request**: Get analytics for sprint 3
```
GET /api/sprints/<SPRINT_3_ID>/analytics
```

**Expected Output**:
- Velocity trend: Upward then stabilizing
- Risk factors: 18 SP allocated with 10 SP free might be too tight
- Capacity calculation: Hours/SP = (6.0 focus_hours/day × remaining_days) / allocated_sp
- **Should flag**: If more items added, velocity will compress

---

## Test Case 6: Healthcare Project - Dynamic Capacity Calculation
**Scenario**: Test hours-per-story-point dynamic calculation

**Observed Pattern**:
- Sprint 1: 25 SP in 14 days
- Sprint 2: 18 SP in 14 days
- Sprint 3: 24 SP active, 6 days remaining

**Expected Calculation**:
```
hours_per_sp = (5.5 focus_hours/day × 6 remaining_days) / 24 sp
            = 33 / 24
            = 1.375 hours per SP (extremely fast)
            ↓
Risk Alert: If new items added, team must maintain this velocity
```

**Request**: GET sprint 3 with capacity details
```
GET /api/sprints/<SPRINT_3_ID>/capacity-analysis
```

**Expected**: System shows high utilization warning

---

## Test Case 7: Cross-Project Risk Appetite Comparison
**Compare recommendation variance across projects**

**Same 8 SP Story, Different Projects**:

1. **FinTech (Strict)**: "Implement encrypted audit logging"
   - Expected: More conservative, may DEFER despite capacity

2. **Identity (Standard)**: "Implement encrypted audit logging"
   - Expected: More balanced, likely ADD if capacity exists

3. **Healthcare (Strict)**: "Implement encrypted audit logging"
   - Expected: Most conservative, likely DEFER or SPLIT

**Request**: Create same item in all 3 projects, compare recommendations
```
POST /api/backlog-items/ (to all 3 spaces with same data)
GET /api/recommendations?compare=true&item_id=<ITEM_ID>
```

**Expected**: Risk appetite directly influences ADD/DEFER threshold

---

## Test Case 8: Burndown Monitoring
**Scenario**: Track if system detects sprint completion risk

**Setup**: Make active sprints (Sprint 3 in each project)

**Check**: Get sprint burndown status
```
GET /api/sprints/<ANY_ACTIVE_SPRINT_ID>/burndown-status
```

**Expected Output**:
- Days remaining: 11 days
- Points completed: varies by sprint
- Trend: Upward velocity = less risk, flat = more risk
- **Should flag**: Any sprint with <5 points completed in 3+ days

---

## Validation Checklist

After running tests, verify:

- [ ] Test 1: ADD decision works for manageable scope creep
- [ ] Test 2: DEFER detects when item exceeds free capacity
- [ ] Test 3: SWAP automatically identifies low-priority items to swap out
- [ ] Test 4: SPLIT recommends breaking oversized stories
- [ ] Test 5: Velocity trend analysis reflects seeded patterns
- [ ] Test 6: Dynamic capacity calculation adjusts for remaining time
- [ ] Test 7: Risk appetite affects threshold (Strict < Standard < Lenient)
- [ ] Test 8: Burndown status tracks sprint health

---

## Success Criteria

✓ All endpoints return 200 OK (no 500 errors)
✓ Recommendations match expected decisions
✓ Risk scores vary based on velocity, capacity, risk appetite
✓ Dynamic capacity recalculates with remaining days
✓ No date serialization errors (all dates as strings)
