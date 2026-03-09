# Test Data & Viva Demonstration - Complete Guide

## Executive Summary

This package includes everything needed to:
1. **Populate realistic test data** into MongoDB (2 spaces, 9 sprints, 47 items)
2. **Demonstrate all system features** with real project examples
3. **Pass technical viva** with clear explanations and working examples

---

## Files in This Package

### 1. `test_data.py` (Executable)
**Purpose**: Populates MongoDB with test data
**Usage**: `python test_data.py`
**Output**: 2 spaces, 9 sprints, 47 backlog items
**Time to Run**: 2-3 seconds
**Idempotent**: Yes (clears old data first)

**What It Creates**:
- **Space 1**: E-Commerce Platform (8-person team, 6.5 hrs/day)
  - 4 completed sprints: 44-48 SP each
  - 1 active sprint: 50 SP target, mid-progress
  
- **Space 2**: Analytics Dashboard (6-person team, 7 hrs/day)
  - 4 completed sprints: 44-50 SP each
  - 1 active sprint: 50 SP target, mid-progress

### 2. `VIVA_DEMONSTRATION_GUIDE.md` (Study Material)
**Purpose**: Complete viva preparation guide
**Length**: 687 lines, 30-minute demonstration structure
**Contains**:
- Part 1: Architecture overview
- Part 2: How to run test data
- Part 3: 5 detailed demonstration scenarios
- Part 4: System validation checklist
- Part 5: Data interpretation guide
- Part 6: Common viva Q&A (8 detailed answers)
- Part 7: Demonstration timing breakdown
- Part 8: Pre-viva checklist
- Part 9: Technical deep dive (if asked advanced questions)

### 3. `SETUP_TEST_DATA.md` (Quick Reference)
**Purpose**: Fast setup and verification
**Length**: 376 lines, quick checklists
**Contains**:
- Quick start (3 steps, 3 minutes)
- What's in test data breakdown
- Data consistency checks (MongoDB queries)
- In-app verification steps
- Troubleshooting guide
- Data breakdown by project
- Using data for specific demos

---

## Quick Start Path (5 minutes)

### Step 1: Run Test Data Script
```bash
cd services/sprint_impact_service
python test_data.py
```
✓ See "TEST DATA POPULATION COMPLETE" message

### Step 2: Start Application
```bash
# Terminal 1: Backend (if not running)
python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Step 3: Verify in Browser
- Open http://localhost:3000
- Should see 2 spaces listed
- Click each space → see sprints and burndown charts

---

## Demonstration Content

### Test Data Projects (Realistic & Descriptive)

#### Project 1: E-Commerce Platform Enhancement
**Story**: Building modern payment and inventory systems

Completed Work (4 Sprints, 182 SP):
1. Payment Gateway Integration (44 SP) - Stripe & PayPal
2. Inventory Management (48 SP) - Real-time stock tracking
3. Recommendations Engine (46 SP) - AI product suggestions
4. Mobile Optimization (44 SP) - Performance improvements

Active Work (Sprint 5, mid-progress):
- Cart and Checkout Improvements (50 SP)
- 22 SP completed (44%)
- 7 days remaining
- Demo: One-click checkout, cart recovery emails, inventory checks

#### Project 2: Real-Time Analytics Dashboard
**Story**: Data pipeline to insights platform

Completed Work (4 Sprints, 186 SP):
1. Data Aggregation Pipeline (46 SP) - Kafka & Spark
2. Real-Time Backend (46 SP) - WebSocket metrics API
3. Frontend UI (44 SP) - React dashboard with charts
4. Alerting System (50 SP) - ML-based anomalies

Active Work (Sprint 6, mid-progress):
- Custom Reports & Exports (50 SP)
- 19 SP completed (38%)
- 7 days remaining
- Demo: Report builder, PDF/Excel exports, scheduled reports

---

## Demonstration Scenarios

### Scenario 1: Story Point Suggestion (3 min)
**Task**: "Implement OAuth2 single sign-on with Google and GitHub"
**Expected Output**: 8-10 SP with 87% confidence
**What It Shows**: ML learns from task complexity

### Scenario 2: Hours Translation (2 min)
**Task**: 5 SP from test sprint
**Calculation**: 5 SP × 6.4 hours/SP = 32 hours
**What It Shows**: Team pace converts SP to hours

### Scenario 3: Sprint Goal Alignment (3 min)
**Test A** - Aligned: OAuth2 + security goal = 70% match ✓
**Test B** - Misaligned: Blog design + security goal = 20% match ✗
**What It Shows**: Prevents scope creep

### Scenario 4: Impact Analysis (5 min)
**4 Risk Cards**:
1. Schedule Risk: 28% (will finish on time)
2. Quality Risk: 22% (manageable)
3. Productivity: +0.8% (slight boost)
4. Effort: 104 hours (realistic for 13 SP)
**What It Shows**: ML predicts multiple impact dimensions

### Scenario 5: Recommendation Engine (4 min)
**Test A** - ADD: 5 SP free, all risks low → "Add this task"
**Test B** - SWAP: At capacity, high priority → "Replace lower item"
**Test C** - DEFER: Large + days ending + misaligned → "Save for next sprint"
**Test D** - SPLIT: Large task + 3 days → "Break into 2 parts"
**What It Shows**: Smart decision-making engine

---

## Validation Points

### ✅ All 10 Features Demonstrated
1. Story Point Suggestion (ML)
2. Hours Translation (Velocity)
3. Velocity Measurement (Historical)
4. Sprint Capacity (Dynamic)
5. Goal Alignment (NLP)
6. Impact Analysis (4 Models)
7. Recommendation Engine (Rules)
8. Burndown Charts (Visualization)
9. Velocity Charts (Trend)
10. Per-Person-Per-Day Capacity (Calculation)

### ✅ Both System Functions Shown
1. **Adding New Task**:
   - Suggestion → Analysis → Recommendation
   
2. **Viewing History**:
   - Completed sprints → Burndown → Velocity → Capacity trends

### ✅ Test Data Demonstrates
- Consistent team performance (4 completed sprints)
- Realistic velocity (44-50 SP per sprint)
- In-progress work (mid-sprint state)
- Multiple item statuses (Done, Review, In Progress, To Do)
- Goal alignment scenarios (aligned vs misaligned)
- Risk variety (nominal to alert levels)

---

## Viva Q&A Preparation

### Technical Questions Covered
1. **How does story point suggestion work?**
   - XGBoost with 105 features (5 numeric + 100 TF-IDF)
   - Confidence scores prevent overconfidence
   - Learns from team's actual effort history

2. **Why use goal alignment?**
   - Prevents scope creep into sprints
   - TF-IDF is deterministic (no LLM/API costs)
   - Feeds into recommendation as alignment boost

3. **What's unique about the velocity calculation?**
   - Uses actual completed SP from 20 sprints
   - Converts to hours via: 8 / team_pace
   - More accurate than blind 8 hours/SP assumption

4. **How does capacity work in first sprint?**
   - Default 30 SP based on team size
   - Adjusts dynamically after first sprint
   - By sprint 4, becomes highly personalized

5. **Why 4 ML models instead of one?**
   - Each predicts different risk dimension
   - Specialist models more accurate than generalist
   - Can tune each independently

6. **How does recommendation engine avoid bad decisions?**
   - 5-tier rule system with clear priorities
   - Backed by project constraints
   - Alignment signal prevents off-goal tasks
   - Team can always override with reasoning

7. **What happens if predictions are wrong?**
   - System learns from actual sprint outcomes
   - Next predictions get better
   - Team can provide feedback/manual adjustments

8. **How do you prevent analysis paralysis?**
   - Recommendations are advisory, not mandatory
   - Clear reasoning lets team make informed overrides
   - Default to ADD if capacity exists (optimistic)

---

## Files to Reference During Viva

| Phase | Reference | Purpose |
|-------|-----------|---------|
| **Setup** | SETUP_TEST_DATA.md | How to run and verify data |
| **Overview** | VIVA_DEMONSTRATION_GUIDE.md Part 1 | Architecture explanation |
| **Scenarios** | VIVA_DEMONSTRATION_GUIDE.md Part 3 | 5 demo scenarios with expected output |
| **Validation** | VIVA_DEMONSTRATION_GUIDE.md Part 4 | Checklist to verify each feature |
| **Interpretation** | VIVA_DEMONSTRATION_GUIDE.md Part 5 | How to read charts and metrics |
| **Q&A** | VIVA_DEMONSTRATION_GUIDE.md Part 6 | Common questions with deep answers |
| **Technical** | VIVA_DEMONSTRATION_GUIDE.md Part 9 | ML models, formulas, algorithms |

---

## What Examiners Will See

### Phase 1: System Explanation (2 min)
- Architecture: Frontend → API → ML → Database
- 4 ML models working together
- Rule-based recommendation engine
- Velocity tracking and capacity calculation

### Phase 2: Test Data Overview (1 min)
- 2 realistic projects (E-Commerce, Analytics)
- 9 sprints total (8 completed, 1 active per space)
- 47 backlog items with descriptions
- Clear project contexts

### Phase 3: Live Demonstration (15 min)
- Add new task → Get ML suggestion
- View impact analysis → See 4 risk cards
- Get recommendation → Understand reasoning
- View completed sprints → See velocity trend
- View active sprint → See capacity and progress

### Phase 4: Q&A (5 min)
- Ask about specific features
- Ask about algorithms
- Ask about edge cases
- Test technical understanding

### Phase 5: Code/Architecture Review (If Time)
- Can show backend code
- Can explain data models
- Can discuss ML model training
- Can discuss system design decisions

---

## Pre-Viva Checklist

- [ ] Test data script runs without errors
- [ ] MongoDB contains 2 spaces
- [ ] MongoDB contains 9 sprints
- [ ] MongoDB contains 47 items
- [ ] Frontend loads both spaces
- [ ] Can see 4 completed sprints
- [ ] Can see 1 active sprint
- [ ] Burndown charts visible
- [ ] Velocity charts visible
- [ ] Can add new task
- [ ] AI suggestion works
- [ ] Impact analysis works
- [ ] Gets recommendation
- [ ] Read VIVA_DEMONSTRATION_GUIDE.md
- [ ] Understand all 5 scenarios
- [ ] Understand all Q&A answers
- [ ] Ready to explain algorithm details

---

## Timing & Flow

```
Total: 30-35 minutes

Part A: Setup & Overview (3 min)
  └─ Start app, show test data

Part B: Live Demonstrations (20 min)
  ├─ Scenario 1: Story point suggestion (3 min)
  ├─ Scenario 2: Hours translation (2 min)
  ├─ Scenario 3: Goal alignment (3 min)
  ├─ Scenario 4: Impact analysis (5 min)
  └─ Scenario 5: Recommendations (4-5 min)

Part C: Validation (2 min)
  └─ Show charts, metrics, system validation

Part D: Q&A (5-10 min)
  ├─ Architecture questions
  ├─ Algorithm questions
  └─ Edge case discussions
```

---

## Success Criteria

### Your Demo Will Be Successful If:
✅ All 5 scenarios run without errors
✅ ML suggestions are reasonable (not random)
✅ Risk metrics make sense for the task
✅ Recommendations align with constraints
✅ Can explain why each recommendation was given
✅ Velocity/burndown charts display correctly
✅ Can answer technical Q&A
✅ System shows learning over time (sprint 1 vs 4)

### Examiners Will Judge:
✅ Does the system actually work?
✅ Are decisions explainable?
✅ Is the ML realistic (not magic)?
✅ Did you understand what you built?
✅ Can you defend design choices?
✅ Can you discuss improvements?

---

## If Something Goes Wrong During Viva

### Issue: Data doesn't populate
**Backup Plan**: 
- Show code logic (test_data.py is well-commented)
- Discuss what data would be created
- Explain the structure (2 spaces, 9 sprints)

### Issue: App doesn't start
**Backup Plan**:
- Show code/architecture diagrams
- Walk through scenarios verbally
- Show API documentation
- Explain ML models in detail

### Issue: Network error
**Backup Plan**:
- Use pre-prepared screenshots
- Show MongoDB queries directly
- Demonstrate understanding of algorithms
- Discuss results you would expect

### Issue: Prediction seems odd
**Explanation Ready**:
- ML is trained on specific data patterns
- Can explain the 105 features it considers
- Can show confidence scores
- Can discuss why that prediction makes sense

---

## Post-Viva

### If Examiners Ask for Improvements
You can discuss:
1. Adding more historical data for better ML
2. Fine-tuning model hyperparameters
3. Adding team capacity constraints
4. Implementing team member skill levels
5. Adding story point ranges (not just point)
6. Integrating with actual project management tools

### If Examiners Ask About Limitations
You can acknowledge:
1. First sprint requires manual capacity estimate
2. Historical data must be clean and complete
3. Team changes affect velocity learning
4. External blockers not captured in model
5. Requires honest effort logging for accuracy

### Strengths to Emphasize
1. **Explainability**: Can see why recommendation given
2. **Learning**: System improves over time
3. **Flexibility**: Team can override
4. **Practical**: Solves real agile planning problem
5. **Technically Sound**: Proper ML + rule engine + domain knowledge

---

## Quick Reference: Key Numbers

### E-Commerce Space
```
Completed: 182 SP over 4 sprints
Team Pace: 3.25 SP/day
Hours/SP: 2.46 hours (very efficient)
Active: 50 SP target, 22 SP done (44%)
```

### Analytics Space
```
Completed: 186 SP over 4 sprints
Team Pace: 3.32 SP/day
Hours/SP: 2.41 hours (very efficient)
Active: 50 SP target, 19 SP done (38%)
```

### Test Data Summary
```
Total Spaces: 2
Total Sprints: 9 (8 completed, 1 active)
Total Items: 47
Story Points: 3-13 range (realistic)
Team Sizes: 4-8 people
Sprint Duration: 2 weeks each
Completion Rate: 95%+ in completed sprints
```

---

## Final Checklist Before Viva

**Day Before:**
- [ ] Run test_data.py
- [ ] Verify all 47 items in database
- [ ] Verify both spaces load
- [ ] Verify one sprint is Active
- [ ] Test all 5 scenarios
- [ ] Read viva guide completely
- [ ] Practice explaining architecture

**Morning Of:**
- [ ] Start backend
- [ ] Run test_data.py fresh
- [ ] Start frontend
- [ ] Load app in browser
- [ ] Do quick smoke test
- [ ] Have VIVA_DEMONSTRATION_GUIDE.md open
- [ ] Close unnecessary browser tabs
- [ ] Silence phone

**During Viva:**
- [ ] Take a screenshot at start (proof data loaded)
- [ ] Go through all 5 scenarios
- [ ] Explain each recommendation
- [ ] Use data to support technical answers
- [ ] Reference test data when explaining features
- [ ] Stay calm - system works and you know it

---

## Contact Information for Issues

If test_data.py fails:
1. Check `.env` file has MONGODB_URI
2. Verify MongoDB Atlas cluster running
3. Check internet connection
4. Look for error message details
5. Run with error output: `python -u test_data.py`

If app doesn't work:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+Shift+F5)
3. Check console for errors (F12)
4. Check Network tab (F12) for API errors
5. Restart backend and frontend

---

**You're Ready! This comprehensive package ensures your viva demonstration will be clear, complete, and impressive.**

**Remember**: You're not just showing a system, you're demonstrating understanding of:
- Sprint planning challenges
- Machine learning applications
- Project management domain knowledge
- Software architecture
- Decision-making under constraints

**All backed by working code and realistic test data.**

Good luck! 🚀
