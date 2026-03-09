# Testing & Integration Guide

## Overview
This document explains how to verify that all systems (frontend, backend, ML models, rules engine) are working together correctly. It includes web-based testing, API inspection, and component verification.

---

## 1. Quick System Check

### 1.1 Start the Dev Server
```bash
npm run dev
# or
pnpm dev
```
The app should start on `http://localhost:3000` with hot module replacement enabled.

### 1.2 Verify Backend Connection
Open browser DevTools (F12) → Network tab, then:
1. Navigate to the Impact Analyzer page
2. Watch the Network tab for API calls:
   - `GET /api/sprints/{id}/context` — Sprint capacity & velocity
   - `GET /api/analytics/spaces/{id}/team-pace` — Team velocity conversion
   - `POST /api/analyze-impact` — ML predictions
   - `POST /api/recommend` — Rule-based recommendation
   - `POST /api/ai/align-sprint-goal` — Goal alignment check

---

## 2. Component Integration Verification

### 2.1 Story Point Suggestion (XGBoost Model)
**What it does:** Predicts 1-21 story points based on 105 features (5 numeric + 100 TF-IDF)

**How to test:**
1. In Impact Analyzer, enter a task title (e.g., "Fix authentication bug")
2. Enter description (e.g., "Update JWT token validation logic")
3. Click the **AI** button next to Story Points field
4. Observe the suggested SP value and confidence score

**Expected flow:**
```
Frontend: User clicks AI button
  ↓
Frontend sends: {title, description} to POST /api/ai/suggest-points
  ↓
Backend: Extracts 5 numeric features + 100 TF-IDF features
  ↓
Backend: XGBoost model predicts SP (1-21) with confidence
  ↓
Frontend: Displays suggested value (e.g., "Suggested: 5 SP (87% confident)")
```

**Debug in Console:**
```javascript
// Open console and check the API call
fetch('/api/ai/suggest-points', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    title: "Test task",
    description: "Test description"
  })
}).then(r => r.json()).then(console.log)
```

---

### 2.2 Sprint Capacity Calculation
**First Sprint:** Defaults to 30 SP
**Subsequent Sprints:** Calculated from past sprint velocity

**How to test:**
1. Create or select a sprint
2. Check the CapacityBar component (upper right of Impact Analyzer)
3. It should show: "X / Y SP (A / B hrs)"

**Expected flow:**
```
Frontend loads sprint
  ↓
Frontend calls: GET /api/sprints/{sprint_id}/context
  ↓
Backend returns:
  - current_load: Total SP of items in sprint
  - team_velocity_14d: Capacity (30 for first sprint, else calculated)
  - free_capacity: team_velocity - current_load
  ↓
Frontend displays CapacityBar with:
  - used_sp = current_load
  - total_sp = team_velocity_14d
  - hours = SP * hours_per_sp (from team pace)
```

**Verify in Code:**
```javascript
// In ImpactAnalyzer.jsx, the CapacityBar receives:
<CapacityBar used={ctx.used_points} total={ctx.total_capacity} hoursPerSP={hoursPerSP} />
```

---

### 2.3 Team Pace & Hours Translation (Module 3)
**Logic:** 
- Calculates team_velocity from historical completed sprints
- Converts to hours: `hours_per_sp = 8.0 / team_velocity`
- Displays "5 SP (~40 Hours)" format

**How to test:**
1. In Impact Analyzer, change story points (e.g., to 5)
2. Below the input, should show: "5 SP (~X Hours)"
3. The hours value changes with story points

**Expected flow:**
```
Frontend loads component
  ↓
Frontend calls: GET /api/analytics/spaces/{space_id}/team-pace
  ↓
Backend queries:
  - Last 20 completed sprints
  - Sum completed_sp / sum dev_days
  - Calculates team_pace
  - Returns hours_per_sp = 8.0 / team_pace
  ↓
Frontend stores hoursPerSP in state
  ↓
Every story point change triggers:
  displayValue = formatSPWithHours(sp, hoursPerSP)
```

**Debug in Console:**
```javascript
// Check the API response
fetch('/api/analytics/spaces/{space_id}/team-pace')
  .then(r => r.json())
  .then(data => {
    console.log("Team Pace:", data.team_pace)
    console.log("Hours per SP:", data.hours_per_sp)
    console.log("Based on sprints:", data.sprints_analyzed)
  })
```

---

### 2.4 Per-Person-Per-Day Work Capacity
**Logic:** Derives actual productive hours from historical sprint data
```
Formula: (Assignees × Days × 8) / Completed_SP = hours_per_sp
Then: daily_focus_hours = (completed_sp / days) × hours_per_sp / assignees
```

**How to test:**
1. Create a sprint with specific assignees and dates
2. Complete some items
3. Create next sprint
4. In Impact Analyzer, click **Analyze Impact**
5. Check the "Effort" prediction in results

**Expected in results:**
- Effort hours predicted for new task based on team's historical productivity
- Capped between 2.0 and 10.0 hours per person per day (reasonable bounds)

**Verify in Backend:**
```python
# In impact_routes.py
focus_hours = await calculate_dynamic_focus_hours(space_id)
# Returns: 6.0 (default) or calculated value based on last sprint
```

---

### 2.5 Sprint Goal Alignment (Module 4)
**Logic:** Uses TF-IDF cosine similarity between sprint goal and task description

**Scoring:**
- 0.50+ = STRONGLY_ALIGNED (green) → safe to add
- 0.30-0.50 = PARTIALLY_ALIGNED (yellow) → review with team
- < 0.30 = UNALIGNED (red) → likely scope creep

**How to test:**
1. Select a sprint with a goal
2. Enter a task title & description
3. Alignment is automatically checked
4. Look for color-coded alignment strip (green/yellow/red)

**Expected flow:**
```
User enters task description
  ↓
Frontend calls: POST /api/ai/align-sprint-goal
  {sprint_goal: "...", task_description: "..."}
  ↓
Backend uses tfidf_cosine_similarity()
  Returns: alignment_score (0-1)
  ↓
Frontend displays GoalAlignmentStrip
  - Green if score >= 0.50
  - Yellow if 0.30-0.50
  - Red if < 0.30
```

**Debug in Console:**
```javascript
fetch('/api/ai/align-sprint-goal', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    sprint_goal: "Improve user authentication",
    task_description: "Update JWT validation and add 2FA support"
  })
}).then(r => r.json()).then(console.log)
```

---

### 2.6 Impact Analysis ML Predictions
**Models:** 4 ML models make predictions
1. **Effort:** XGBoost regressor → hours needed
2. **Schedule Risk:** XGBoost classifier → spillover probability (%)
3. **Quality Risk:** Logistic regression → defect probability (%)
4. **Productivity:** XGBoost+MLP ensemble → velocity change (%)

**How to test:**
1. Fill in task details (title, description, story points, priority)
2. Click **Analyze Impact** button
3. Wait for results (should show 4 risk cards)

**Expected results display:**
```
┌─────────────────────────────────────────┐
│ QUALITY RISK: 35% [NOMINAL]             │
│ SCHEDULE RISK: 28% [NOMINAL]            │
│ PRODUCTIVITY: +2% [NOMINAL]             │
│ EFFORT: 18 hours [NOMINAL]              │
└─────────────────────────────────────────┘
```

**Each card shows:**
- Risk metric value
- Status (NOMINAL / CAUTION / ALERT)
- Click to expand for reasoning

---

### 2.7 Rule-Based Recommendation Engine
**5 Rules (in priority order):**

| Rule | Condition | Action |
|------|-----------|--------|
| 0 | Sprint < 2 days left, non-critical | DEFER |
| 0.5 | Critical/Highest priority | FORCE SWAP or OVERLOAD |
| 1 | SP >= 13 and days < 10 | SPLIT |
| 2 | ML signals exceed thresholds | DEFER |
| 3 | Free capacity >= new_sp | ADD |
| 4 | Capacity full, find swap | SWAP |

**How to test:**
1. Complete Impact Analysis
2. Observe recommendation card
3. Check if rule triggered matches scenario:
   - Sprint ending? → DEFER
   - Critical bug? → FORCE SWAP
   - Large item? → SPLIT
   - Safe to add? → ADD

**Expected flow:**
```
ML predictions generated
  ↓
Recommendation engine evaluates rules 0→4
  ↓
First matching rule wins
  ↓
Generates:
  - Recommendation type (ADD, DEFER, SWAP, SPLIT, OVERLOAD)
  - Reasoning text
  - Action plan steps
  - Risk summary
  ↓
Frontend displays RecommendationCard
```

---

## 3. Web Search for Documentation

The tool lets you **search external docs while working** using the browser's address bar.

### 3.1 During Development
While editing or testing, you can quickly search docs:

**Example: Search Scrum Best Practices**
1. Open a new tab
2. Type in address bar: `google.com "scrum story point estimation"`
3. Read results, apply learnings to your task

**Example: Look up Sprint Planning** 
1. New tab → `site:atlassian.com sprint planning`
2. Learn about sprint goals, capacity planning
3. Apply to your sprint setup

### 3.2 Useful Documentation Sources
- **Agile Practices:** site:atlassian.com scrum
- **Story Point Sizing:** site:mountaingoatsoftware.com story point estimation
- **ML/Prediction Models:** site:scikit-learn.org xgboost
- **FastAPI Backend:** site:fastapi.tiangolo.com
- **React Frontend:** site:react.dev

### 3.3 Verifying Backend Endpoints
While developing, you can test APIs directly:

**Using curl in terminal:**
```bash
# Test sprint context
curl -X GET http://localhost:8000/api/sprints/sprint_123/context

# Test impact analysis
curl -X POST http://localhost:8000/api/analyze-impact \
  -H "Content-Type: application/json" \
  -d '{"sprint_id":"123","title":"Test","story_points":5}'

# Test recommendation
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"sprint_id":"123","title":"Test","story_points":5}'
```

**Using Postman/Thunder Client:**
1. Download Postman (free)
2. Create requests for each endpoint
3. Save as collection for regression testing

---

## 4. Full Integration Test Scenario

### Scenario: Add "Implement OAuth2" to Sprint
1. **Setup:**
   - Sprint: "Q1 Auth Hardening" (goal: improve security)
   - Team: 4 people, 2-week sprint, 5 days remaining
   - Current load: 25 SP / 30 SP capacity

2. **User Action:**
   - Title: "Implement OAuth2 authentication"
   - Description: "Add OAuth2 provider integration with social login (Google, GitHub)"
   - Story Points: [click AI] → suggests "8 SP (87% confident)"
   - Priority: High

3. **Expected Backend Flow:**
   ```
   Step 1: Story Point Suggestion
     - XGBoost model evaluates:
       * Title/description TF-IDF similarity
       * Historical tickets with "OAuth" or "authentication"
       * Predicts: 8 SP (87% confidence)
   
   Step 2: Team Pace Calculation
     - Last sprint: 28 SP completed in 10 days by 4 people
     - team_pace = 28 / 10 = 2.8 SP/day
     - hours_per_sp = 8.0 / 2.8 = 2.86 hours/SP
     - 8 SP → 22.9 hours estimated
   
   Step 3: Sprint Goal Alignment
     - Sprint goal: "improve security"
     - Task: "implement OAuth2"
     - TF-IDF similarity: 0.68 (STRONGLY_ALIGNED) ✓
   
   Step 4: Impact Analysis
     - Effort: 22.9 hours (within team pace)
     - Schedule Risk: 15% (5 days × 2.8 SP/day = 14 SP capacity remaining)
     - Quality Risk: 18% (OAuth2 is mature, low defect risk)
     - Productivity: +1.2% (mid-sprint additions slightly boost team focus)
   
   Step 5: Recommendation Engine
     - Rule 0: 5 days remaining, High priority → pass
     - Rule 0.5: High (not Critical) → pass
     - Rule 1: 8 SP < 13 → pass
     - Rule 2: All signals safe (15% < 50%, 1.2% > -30%, 18% < 70%) → pass
     - Rule 3: Free capacity = 30 - 25 = 5 SP, new = 8 SP → FAIL
     - Rule 4: Try SWAP
       * Look for "To Do" items with priority < High
       * Find: "Update documentation" (3 SP, Low)
       * SWAP: Remove 3 SP, add 8 SP
       * New load: 25 - 3 + 8 = 30 SP (full)
       * Recommendation: SWAP with reasoning + swap target
   ```

4. **Frontend Display:**
   ```
   ┌─ Capacity Bar ────────────┐
   │ 25 / 30 SP (71 / 86 hrs)  │  ← Hours translation
   │ [████████░░] 83% used     │
   └───────────────────────────┘
   
   ┌─ Goal Alignment ──────────────┐
   │ ✅ STRONGLY_ALIGNED (68%)     │  ← Green, goal match
   └───────────────────────────────┘
   
   ┌─ Risk Analysis ───────────────┐
   │ Schedule Risk: 15% [NOMINAL]  │
   │ Quality Risk: 18% [NOMINAL]   │
   │ Productivity: +1.2% [NOMINAL] │
   │ Effort: 22.9 hours [NOMINAL]  │
   └───────────────────────────────┘
   
   ┌─ Recommendation ──────────────────────┐
   │ 🔄 SWAP                               │
   │ Removing lower-priority work to       │
   │ accommodate critical authentication   │
   │ upgrade.                              │
   │ Swap: "Update documentation" (3 SP)  │
   │ [APPLY SWAP] [ADD] [DEFER] [SPLIT]   │
   └───────────────────────────────────────┘
   ```

5. **User Action:**
   - Clicks [APPLY SWAP]
   - Backend executes:
     * Remove "Update documentation" from sprint
     * Add "Implement OAuth2" to sprint
   - Success message: "Swapped out 'Update documentation'. 'Implement OAuth2' added to sprint."

---

## 5. Debugging & Logs

### 5.1 Frontend Debugging (Console)
```javascript
// Check state
console.log("[v0] Form data:", form)
console.log("[v0] Analysis result:", analysis)
console.log("[v0] Recommendation:", recommendation)
console.log("[v0] Hours per SP:", hoursPerSP)

// Monitor API calls
console.log("[v0] API call:", endpoint, payload)
```

### 5.2 Backend Debugging (Server Logs)
```python
# In Python routes
import sys

print(f"[ANALYZE] sprint_id={request.sprint_id} sp={request.story_points}", file=sys.stderr)
print(f"[ML_PRED] schedule_risk={schedule_risk} quality_risk={quality_risk}", file=sys.stderr)
print(f"[RULE] triggered={rule_name} action={recommendation['action']}", file=sys.stderr)
```

### 5.3 Network Inspector (DevTools)
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by API calls
4. Click request → Payload tab (see sent data)
5. Click response → check returned data structure

---

## 6. Checklist for Full Integration

- [ ] **Story Point Suggestion:** Click AI button, gets prediction
- [ ] **Team Pace:** Loads team velocity from completed sprints
- [ ] **Hours Translation:** Shows "X SP (~Y Hours)" format
- [ ] **Capacity Display:** CapacityBar shows SP and hours
- [ ] **Goal Alignment:** Task description vs sprint goal (color-coded)
- [ ] **Impact Analysis:** 4 ML risk predictions display correctly
- [ ] **Recommendation Rules:** Outputs correct action (ADD/DEFER/SWAP/SPLIT)
- [ ] **Recommendation Action:** Clicking button executes action (adds/defers/swaps)
- [ ] **Per-Person-Per-Day:** Effort hours calculated from historical data
- [ ] **All Error Handling:** No console errors, API errors caught gracefully

---

## 7. Example API Responses

### Sprint Context
```json
{
  "sprint_id": "sprint_123",
  "sprint_name": "Q1 Auth Hardening",
  "sprint_status": "Active",
  "current_load": 25,
  "item_count": 5,
  "days_remaining": 5,
  "sprint_progress": 71.4,
  "team_velocity": 30,
  "free_capacity": 5
}
```

### Team Pace
```json
{
  "team_pace": 2.8,
  "hours_per_sp": 2.86,
  "sprints_analyzed": 3,
  "total_completed_sp": 84,
  "total_dev_days": 30,
  "metadata": "Based on 3 completed sprints"
}
```

### Impact Analysis
```json
{
  "schedule_risk": 15.3,
  "quality_risk": 18.7,
  "velocity_change": 1.2,
  "effort_hours": 22.9,
  "confidence": 0.87
}
```

### Recommendation
```json
{
  "recommendation_type": "SWAP",
  "reasoning": "Sprint is at capacity. Removing 'Update documentation' (3 SP) to make room for critical OAuth2 work.",
  "target_ticket": {
    "id": "task_456",
    "title": "Update documentation",
    "story_points": 3,
    "priority": "Low"
  },
  "action_plan": {
    "step_1": "Move 'Update documentation' to Backlog",
    "step_2": "Add 'Implement OAuth2' to Active Sprint"
  }
}
```

---

## Summary
This guide covers:
1. How each system (SP suggestion, pace, alignment, ML, rules) integrates
2. How to test each component independently
3. How to verify full end-to-end flow
4. How to use web search for documentation during testing
5. Debugging tips and API response formats

Use this as your checklist before marking the integration as complete.
