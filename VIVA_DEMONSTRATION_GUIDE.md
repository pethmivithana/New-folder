# VIVA DEMONSTRATION GUIDE

## System Overview for Examiners

This document provides a complete guide for demonstrating the Sprint Impact Service during the viva. The system implements an intelligent agile sprint planning assistant that helps teams make better decisions about adding tasks to sprints.

---

## Part 1: System Architecture Overview (2 minutes)

### What the System Does
```
Input: New task to add to sprint
↓
Analysis:
  1. Suggest story points using ML
  2. Check alignment with sprint goal
  3. Analyze impact on timeline and quality
  4. Evaluate team capacity and velocity
↓
Output: Recommendation (ADD / DEFER / SWAP / SPLIT)
```

### Technology Stack
- **Frontend**: React with JavaScript
- **Backend**: Python (FastAPI) with machine learning models
- **Database**: MongoDB for data persistence
- **ML**: XGBoost, scikit-learn, TF-IDF for NLP

---

## Part 2: Data Setup (1 minute)

### Running Test Data Population

```bash
# Terminal 1: Start Backend
cd services/sprint_impact_service
python main.py

# Terminal 2: Populate Test Data
cd services/sprint_impact_service
python test_data.py
```

**Expected Output:**
```
TEST DATA POPULATION COMPLETE
============================================================
Spaces created: 2
Sprints created: 9
Backlog items created: 47

Spaces:
  1. E-Commerce Platform Enhancement
  2. Real-Time Analytics Dashboard
============================================================
```

### Data Structure Overview
- **2 Spaces** (projects) with realistic contexts
- **4 Completed Sprints** per space (for velocity/burndown visualization)
- **1 Active Sprint** per space (mid-sprint with items in progress)
- **5-6 Backlog Items** per sprint with realistic story points
- **Item Statuses**: To Do, In Progress, In Review, Done

---

## Part 3: Demonstration Scenarios

### Scenario 1: Story Point Suggestion Logic (3 minutes)

**Demonstrate**: How ML predicts effort required for a new task

**Steps**:
1. Navigate to active sprint in "E-Commerce Platform Enhancement"
2. Click "Add New Task"
3. Fill in task details:
   ```
   Title: "Implement OAuth2 single sign-on with Google and GitHub"
   Description: "Add OAuth2 authentication provider support, handle token refresh, 
   manage user profile synchronization from OAuth providers, and add account linking."
   Priority: High
   Type: Story
   ```
4. **Click "AI Suggest Points" button**
5. System shows: "Suggested: 8-10 SP (87% confidence)"

**Explanation to Examiners**:
- **Model Used**: XGBoost Regressor trained on historical data
- **Features**: 5 numeric features + 100 TF-IDF text features
- **Output Range**: 1-21 story points
- **Confidence**: Based on model uncertainty estimation
- **Formula**: Predicts complexity from task description and historical patterns

**Expected Result**: Should suggest 8-10 SP (authentication is complex)

---

### Scenario 2: Hours Translation & Team Pace (2 minutes)

**Demonstrate**: How team velocity converts story points to hours

**Steps**:
1. Look at capacity bar below the form
2. Shows: "25 / 30 SP (71 / 86 Hours)" with hours calculation
3. Note the breakdown:
   ```
   Team Pace: From last 20 completed sprints
   - Average: 1.25 SP / day
   - Conversion: 8 hours / 1.25 SP/day = 6.4 hours/SP
   - Task 8 SP × 6.4 hours/SP = 51.2 hours
   ```

**Explanation to Examiners**:
- **Team Pace Formula**: `completed_sp / dev_days` from historical sprints
- **Hours Per SP**: `8.0 / TEAM_PACE`
- **First Sprint**: Defaults to 8 hours/SP if no historical data
- **Dynamic**: Adjusts as team completes more sprints

**Why This Matters**:
- Converts abstract story points to real hours
- Helps estimate actual time investment
- Shows team's actual productivity level
- More accurate than blindly assuming 8 hours/SP

---

### Scenario 3: Sprint Goal Alignment Check (3 minutes)

**Demonstrate**: How semantic analysis ensures scope alignment

**Test Case A - Strongly Aligned Task**:
```
Sprint Goal: "Improve security and authentication mechanisms"

New Task: "Implement OAuth2 single sign-on with Google and GitHub"
           (as described above)

Expected: ✅ STRONGLY_ALIGNED (70%+)
Reason: Task directly implements authentication improvement
```

**Test Case B - Poorly Aligned Task**:
```
Same Sprint Goal: "Improve security and authentication mechanisms"

New Task: "Update company blog design to match new brand guidelines"

Expected: ⏸ UNALIGNED (20%)
Reason: Blog design doesn't contribute to security goals
```

**How It Works**:
1. Extract text features from sprint goal and task description
2. Compute TF-IDF vectors
3. Calculate cosine similarity (0-1 range)
4. Classify: ≥0.50 = Aligned, 0.30-0.50 = Partial, <0.30 = Unaligned

**Explanation to Examiners**:
- **Algorithm**: TF-IDF cosine similarity (no LLM, deterministic)
- **Benefits**: Fast, no API calls, fully explainable
- **Use Case**: Prevents scope creep into sprint
- **Integration**: Feeds into recommendation engine

---

### Scenario 4: Impact Analysis with ML Predictions (5 minutes)

**Demonstrate**: Complete risk analysis before adding a task

**Steps**:
1. Fill in a comprehensive task:
   ```
   Title: "Implement Redis caching layer for product recommendations"
   Description: "Add Redis cluster for caching user recommendations, implement cache invalidation strategy, 
   handle cache misses, and add monitoring for cache hit rates."
   Story Points: (Let AI suggest, expect ~13)
   Priority: High
   ```
2. **Click "Analyze Impact" button**
3. System shows 4 risk cards:

**Risk Card 1: Schedule Risk**
```
Schedule Risk: 28% [NOMINAL ✓]
─────────────────────────────
Days Remaining: 7 days
Task Effort: 104 hours
Team Capacity: 120 hours
Conclusion: Should complete within timeline
```

**Risk Card 2: Quality Risk**
```
Quality Risk: 22% [NOMINAL ✓]
─────────────────────────────
Complexity: Medium-High (caching + monitoring)
Test Coverage Required: High
Integration Points: 3 (API, product service, recommendations)
Conclusion: Manageable with proper testing
```

**Risk Card 3: Productivity Impact**
```
Productivity Change: +0.8% [NOMINAL ✓]
─────────────────────────────
Focus on backend: Minimal context switching
Team Experience: Moderate (caching is familiar)
Conclusion: Slight productivity improvement from familiarity
```

**Risk Card 4: Effort Estimate**
```
Estimated Effort: 104.2 hours
─────────────────────────────
Raw Prediction: 108 hours
Adjustment Factor: 0.96x (team expertise)
Confidence: 78%
```

**ML Models Explained**:
1. **Effort Model**: XGBoost Regressor
   - Predicts actual hours needed
   - Trained on historical time tracking data
   - Uses task features (complexity, type, etc.)

2. **Schedule Risk Model**: XGBoost Classifier
   - Predicts probability of missing deadline
   - Based on days remaining vs estimated hours
   - Accounts for dependencies and blockers

3. **Quality Risk Model**: Logistic Regression
   - Predicts defect probability post-release
   - Considers complexity, testing effort, integration points
   - Learns from bug history

4. **Productivity Model**: XGBoost + Neural Network Ensemble
   - Predicts velocity change (%)
   - Accounts for context switching, learning curve
   - Ensemble provides robustness

---

### Scenario 5: Recommendation Engine Logic (4 minutes)

**Demonstrate**: How all signals combine into a recommendation

**Test Case A - Recommended to ADD**:
```
Context:
- Sprint Capacity: 25/30 SP used (5 SP free)
- Days Remaining: 10 days
- New Task: 5 SP, High priority, Goal-aligned (80%)
- Schedule Risk: 15%
- Quality Risk: 20%
- Productivity Impact: +1.2%

Decision Engine:
✓ Rule 0: Sprint not ending soon (10 days) → Continue
✓ Rule 0.5: High priority but within capacity → Check other signals
✓ Rule 1: Not large late in sprint (5 SP, 10 days) → Continue
✓ Rule 2: ML signals nominal (all <threshold) → Continue
✓ Rule 3: Free capacity (5 >= 5) → ADD

Result: 🟢 ADD
Recommendation: "Safe to add. Sprint has 5 SP free, all ML signals are nominal 
(Schedule: 15%, Quality: 20%), and task is strongly aligned with sprint goal (80%)."
```

**Test Case B - Recommended to SWAP**:
```
Context:
- Sprint Capacity: 29/30 SP used (1 SP free)
- Days Remaining: 5 days
- New Task: 8 SP, High priority, Goal-aligned (75%)
- Schedule Risk: 45%
- Quality Risk: 35%
- Productivity Impact: -2.1%

Decision Engine:
✓ Rule 0: Sprint ending soon (5 days) → High caution
✗ Rule 3: Not enough free capacity (1 < 8)

Result: 🔄 SWAP
Recommendation: "Sprint at capacity and time pressure increasing. Remove lower-priority 
item and add this instead. Suggested: Remove 'Update documentation' (3 SP) to make room. 
Risk is manageable at 45% schedule risk with proper prioritization."
```

**Test Case C - Recommended to DEFER**:
```
Context:
- Sprint Capacity: 28/30 SP (2 SP free)
- Days Remaining: 2 days
- New Task: 13 SP, Medium priority, Poorly aligned (25%)
- Schedule Risk: 82%
- Quality Risk: 65%
- Goal Alignment: Misaligned (25%) ← Critical signal

Decision Engine:
✗ Rule 0: Sprint almost over (2 days) → DEFER
✗ Rule 1: Large task late in sprint (13 SP, 2 days) → DEFER
✗ Rule 2: ML safety net (Schedule 82% > 50%, Quality 65% > 50%) → DEFER
✗ Goal Alignment: Task poorly aligned (25% < 30%) → Additional caution

Result: 🏹 DEFER
Recommendation: "Not recommended at this time. Sprint ending in 2 days with heavy deadline 
pressure (82% schedule risk). Task is poorly aligned with sprint goal (25%). Add to backlog 
for Sprint 6 when there's proper time allocation and focus."
```

**Test Case D - Recommended to SPLIT**:
```
Context:
- Sprint Capacity: 22/30 SP (8 SP free)
- Days Remaining: 3 days
- New Task: 13 SP, High priority, Goal-aligned (85%)
- Schedule Risk: 72%
- Quality Risk: 38%

Decision Engine:
✗ Rule 1: Large task late in sprint (13 SP > 8 free, 3 days remaining) → SPLIT

Result: ✂️ SPLIT
Recommendation: "Task too large for remaining sprint time. Recommend splitting into 2 parts:
  1. Part A: Core feature (8 SP) - Add to current sprint ✓
  2. Part B: Polish and integration (5 SP) - Defer to Sprint 6

This keeps sprint commitment realistic while capturing the value-add quickly."
```

**Rule Engine Priority**:
```
Rule 0:   Sprint < 1 day left             → DEFER
Rule 0.5: Critical/Emergency priority     → FORCE or SWAP
Rule 1:   Large (>8 SP) + <3 days left    → SPLIT
Rule 2:   ML signals exceed thresholds    → DEFER (with alignment boost)
Rule 3:   Enough free capacity            → ADD
Rule 4:   Sprint at capacity              → SWAP
Rule 5:   No option available             → DEFER
```

**Enhanced with Goal Alignment**:
- Well-aligned (≥0.50): Lower risk thresholds by 5% (easier to add)
- Misaligned (<0.30): Raise risk thresholds by 10% (easier to defer)

---

## Part 4: System Validation Checklist

### ✅ Feature 1: Story Point Suggestion
- [ ] Navigate to active sprint
- [ ] Add new task with complex description
- [ ] Click "AI Suggest Points"
- [ ] See reasonable suggestion (1-21 range)
- [ ] Click on task multiple times → consistent results
- [ ] Try different complexities → values scale appropriately

**Expected**: 8-15 SP for authentication task, 3-5 for simple UI task

### ✅ Feature 2: Hours Translation
- [ ] Check capacity bar shows both SP and Hours
- [ ] Format: "X SP (~Y Hours)"
- [ ] Change story points → hours update proportionally
- [ ] Formula: hours = SP × (8 / team_pace)

**Expected**: If team_pace = 1.0, then 5 SP = ~40 hours; if team_pace = 1.6, then 5 SP = ~25 hours

### ✅ Feature 3: Velocity Measurement
- [ ] View completed sprint details
- [ ] Check sprint statistics
- [ ] Calculate: total_completed_sp / sprint_days = velocity
- [ ] Verify consistency across multiple sprints

**Expected**: Velocity between 1.0-2.0 SP/day (typical for 6-8 hour days)

### ✅ Feature 4: Sprint Capacity
- [ ] First sprint: Default 30 SP
- [ ] Subsequent sprints: Dynamic based on history
- [ ] Calculate: (assignees × days × 8) / completed_sp_from_previous

**Expected**: 25-35 SP depending on team size and velocity

### ✅ Feature 5: Goal Alignment
- [ ] Add task aligned with sprint goal → green indicator (70%+)
- [ ] Add task misaligned with sprint goal → red indicator (<30%)
- [ ] Add task partially aligned → yellow indicator (30-50%)

**Test Goal**: "Improve payment system reliability"
- Aligned: "Add transaction retry logic with exponential backoff"
- Misaligned: "Redesign team onboarding process"

### ✅ Feature 6: ML Impact Analysis
- [ ] Click "Analyze Impact" for task
- [ ] See 4 risk cards appear
- [ ] Each card shows realistic values:
  - Schedule Risk: 10-80% (lower is better)
  - Quality Risk: 5-75% (lower is better)
  - Productivity: -5% to +3% (higher is better)
  - Effort: >0 hours (realistic for story points)

**Expected**: Schedule + Quality risk moderate (20-40%), small productivity change

### ✅ Feature 7: Recommendation Engine
- [ ] For each test case (ADD, DEFER, SWAP, SPLIT)
- [ ] Recommendation matches scenario
- [ ] Reasoning is clear and data-driven
- [ ] Alternative actions shown

**Test Scenarios**: Use ones provided in Scenario 5

### ✅ Feature 8: Burndown Charts
- [ ] View completed sprint details
- [ ] See burndown chart showing:
  - X-axis: Days (0 to sprint duration)
  - Y-axis: Remaining SP
  - Ideal line: Linear decrease
  - Actual line: Sprint team's progress
- [ ] Chart shows completion by end

**Expected**: Actual line follows ideal roughly, ends at ~0 SP

### ✅ Feature 9: Velocity Chart
- [ ] View space statistics
- [ ] See velocity trend over 4+ sprints
- [ ] X-axis: Sprint number
- [ ] Y-axis: Completed SP
- [ ] Shows team's trending velocity

**Expected**: 4 sprints of data showing consistent 25-35 SP completion

### ✅ Feature 10: Per-Person-Per-Day Capacity
- [ ] Calculate from team composition
- [ ] Formula: (completed_sp / days / assignees) × (8 hours / focus_hours)
- [ ] Verify between 2-10 hours/person/day

**Expected**: 4-8 hours/person/day for well-performing team

---

## Part 5: Data Interpretation Guide

### Understanding Completed Sprints

**Sprint 1: Payment Gateway Integration**
```
Status: Completed ✓
Duration: 2 weeks (14 days)
Team Size: 3 people
Goal: Integrate Stripe and PayPal payment processors
Completed SP: 44 (all items marked DONE)
Velocity: 44 SP / 14 days = 3.14 SP/day
```

**Sprint 5: Cart and Checkout (ACTIVE - Mid-Sprint)**
```
Status: Active 🔄
Duration: 2 weeks (started 7 days ago, 7 days remaining)
Team Size: 4 people
Goal: Reduce checkout abandonment
Current Progress:
  - Done: 14 SP (28%)
  - In Review: 13 SP (26%)
  - In Progress: 8 SP (16%)
  - To Do: 10 SP (20%)
Velocity (so far): 14 SP / 7 days = 2.0 SP/day
On Track: Yes (ideal would be 25 SP done, at 22 SP done+review)
```

### Interpreting Risk Metrics

**Schedule Risk Interpretation**:
- < 20%: Safe, plenty of buffer
- 20-40%: Normal, manageable
- 40-60%: Tight, focus required
- 60%+: High risk, likely to miss deadline

**Quality Risk Interpretation**:
- < 20%: High confidence in quality
- 20-40%: Normal risk level
- 40-60%: Extra testing needed
- 60%+: High defect risk, needs architectural review

**Productivity Impact Interpretation**:
- +2% to +3%: Strong boost (highly relevant task)
- 0% to +2%: Slight boost
- -2% to 0%: Neutral or slight drag
- < -2%: Significant drag (context switching, complexity)

---

## Part 6: Common Viva Questions & Answers

### Q1: Why use ML for story point estimation?
**Answer**: 
- Traditional estimation is biased and inconsistent
- ML learns from historical data specific to your team
- Multiple data points (105 features) reduce variance
- XGBoost handles non-linear complexity relationships
- Provides confidence intervals, not just point estimates

### Q2: How do you ensure the recommendation is correct?
**Answer**:
- 5-tier rule-based system with clear priorities
- Rules backed by project constraints (capacity, time, risk)
- Alignment signal prevents scope creep
- All recommendations include reasoning and alternatives
- Team can override if domain knowledge suggests otherwise

### Q3: What happens in the first sprint when there's no velocity data?
**Answer**:
- Default capacity: 30 SP (reasonable for 6-8 person team)
- Default pace: 1.0 SP/day = 8 hours/SP
- As sprints complete, system learns team's actual pace
- By Sprint 4, system becomes highly accurate
- Recommendations improve as more data accumulates

### Q4: How does goal alignment prevent scope creep?
**Answer**:
- Sprint goal defines single focus area
- TF-IDF similarity checks task relevance
- Poorly aligned tasks (< 0.30) get recommendation to defer
- Misalignment raises risk thresholds by 10%
- Helps team say "no" to attractive but off-goal work

### Q5: Why 4 separate ML models instead of one?
**Answer**:
- Each predicts different aspect of risk
- Effort: How many hours
- Schedule: Will we finish on time?
- Quality: How reliable will it be?
- Productivity: How will it affect team velocity?
- Specialist models more accurate than generalist
- Can tune each independently for business priorities

### Q6: What's the difference between hours/SP calculation here vs simple estimation?
**Answer**:
- Simple: Assume all SP = 8 hours (incorrect)
- Our system: Learn actual team pace from history
- Example: If team completes 20 SP in 14 days:
  - Pace = 20 SP / 14 days = 1.43 SP/day
  - Hours/SP = 8 / 1.43 = 5.6 hours/SP
  - So 8 SP really means 44.8 hours, not 64 hours
- Much more accurate for planning

### Q7: How do you handle the uncertainty in ML predictions?
**Answer**:
- Confidence scores show model uncertainty
- Confidence range 50-95% for point suggestions
- Risk metrics are probabilities (0-100%)
- Multiple signals reduce reliance on any single prediction
- Always present alternatives and allow team override

### Q8: What happens if new team joins mid-way?
**Answer**:
- System adjusts velocity and pace calculations
- Historical data weighted by recency
- New team members' learning curve is considered
- Can manually adjust focus_hours_per_day if needed
- Takes 1-2 sprints to recalibrate to new team

---

## Part 7: Demonstration Timing

```
Total Time: 30 minutes

0:00-2:00    - System Overview & Setup (2 min)
2:00-5:00    - Story Point Suggestion (3 min)
5:00-7:00    - Hours Translation (2 min)
7:00-10:00   - Sprint Goal Alignment (3 min)
10:00-15:00  - Impact Analysis (5 min)
15:00-19:00  - Recommendation Engine (4 min)
19:00-25:00  - System Validation (6 min)
25:00-30:00  - Q&A (5 min)
```

---

## Part 8: Pre-Viva Checklist

- [ ] Test data populated successfully
- [ ] Both spaces created with sprints
- [ ] All 4 completed sprints visible
- [ ] Active sprint in mid-progress state
- [ ] Burndown charts show proper trends
- [ ] Velocity charts visible for space
- [ ] Can add new tasks and get suggestions
- [ ] Impact analysis works for sample task
- [ ] All 4 recommendation types demonstrated
- [ ] Browser console clear (no errors)
- [ ] Network calls working (check F12 Network tab)
- [ ] MongoDB connection stable
- [ ] Ready for Q&A on technical details

---

## Part 9: Technical Deep Dive (If Asked)

### Q: How is team velocity actually calculated?
**Code Logic**:
```python
# From last 20 completed sprints
completed_sprints = get_completed_sprints(space_id, limit=20)

total_sp = sum(sprint.completed_sp)
total_days = sum(sprint.duration_in_days)

team_pace = total_sp / total_days  # SP per day
hours_per_sp = 8.0 / team_pace      # Hours per SP

# Example: 400 SP over 280 days
# pace = 1.43 SP/day
# hours = 5.6 hours/SP
```

### Q: What features does the ML model use?
**Story Point Model Features**:
```
Numeric (5):
- Word count of description (complexity proxy)
- Number of mentioned technologies
- Number of integrations needed
- Estimated test cases
- Historical similar tasks

Text (100):
- TF-IDF vectors of task description
- Captures terminology, technical depth
- Learns patterns specific to your domain
```

### Q: How is alignment score calculated?
**Algorithm**:
```python
# TF-IDF Cosine Similarity
goal_vector = tfidf_vectorizer.transform([sprint_goal])
task_vector = tfidf_vectorizer.transform([task_description])

similarity = cosine_similarity(goal_vector, task_vector)[0][0]
# Range: 0.0 to 1.0

# Classification
if similarity >= 0.50:
    level = "STRONGLY_ALIGNED"
elif similarity >= 0.30:
    level = "PARTIALLY_ALIGNED"
else:
    level = "UNALIGNED"
```

### Q: How are risk thresholds adjusted for alignment?
**Rule Logic**:
```python
# Alignment boost adjusts thresholds
if alignment_score >= 0.50:
    alignment_boost = 5.0  # Lower thresholds, easier to ADD
elif alignment_score < 0.30:
    alignment_boost = -10.0  # Raise thresholds, easier to DEFER

# Applied to risk calculations
adjusted_schedule_threshold = max(20, 50 + alignment_boost)
# If aligned: 50 + 5 = 55% (slightly more lenient)
# If misaligned: 50 - 10 = 40% (stricter)
```

---

## Conclusion

This system demonstrates:
1. **Intelligent Estimation** - ML learns from team history
2. **Holistic Analysis** - Multiple risk dimensions
3. **Explainability** - Clear reasoning for recommendations
4. **Flexibility** - Team can override but has guidance
5. **Continuous Learning** - Improves over time with more data

The test data provides a realistic foundation to show all these capabilities working together in a realistic project context.

---

**Last Updated**: Current Implementation
**Data Version**: test_data.py generated
**Status**: Ready for Viva Demonstration
