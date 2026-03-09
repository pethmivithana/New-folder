# Web Search & Verification Guide

## How to Search Docs While Testing

You can verify your implementation against industry standards and best practices by searching the web while running the tool.

---

## 1. Quick Reference: Key Search Terms

### Story Point Estimation & Sizing
```
"story point estimation agile" — understand SP basics
"story point sizing technique" — learn common approaches
"planning poker estimation" — industry standard method
"user story estimation best practices" — professional tips
"agile story points guidelines" — team sizing conventions
```

### Sprint Planning & Goal Alignment
```
"sprint goal scrum" — what makes a good sprint goal
"sprint goal alignment team" — how to check alignment
"scope creep agile sprint" — preventing misalignment
"sprint planning checklist" — complete process
"sprint goal examples" — real-world examples
```

### Velocity & Capacity Planning
```
"sprint velocity calculation" — how it's measured
"team velocity scrum" — using velocity for planning
"capacity planning agile" — balancing capacity
"velocity trending" — tracking progress over time
"focus factor agile estimation" — per-person capacity
```

### Risk Management in Sprints
```
"schedule risk prediction agile" — identifying risk
"quality risk assessment software" — quality factors
"productivity estimation" — team throughput
"technical debt sprint impact" — hidden costs
"risk-driven development" — managing risk
```

### Machine Learning & Prediction
```
"machine learning effort estimation" — ML for planning
"XGBoost regression prediction" — our effort model
"TF-IDF cosine similarity NLP" — our alignment model
"classification vs regression ML" — model types
"feature engineering software metrics" — our 105 features
```

---

## 2. Testing Scenarios with Web Search

### Scenario 1: Validate Story Point Range (1-21)

**Search:** `"story point estimation what range typical"`

**Expected findings:**
- Fibonacci sequence (1, 2, 3, 5, 8, 13, 21) is standard
- Range 1-21 covers small tasks to large epics
- Good for team consensus

**Your implementation:**
- Predicts 1-21 SP ✓
- Uses 105 features (5 numeric + 100 TF-IDF) ✓
- Returns confidence score ✓

**Verification:** Check if your predicted values match team intuition

---

### Scenario 2: Validate Team Velocity Calculation

**Search:** `"sprint velocity calculation formula agile"`

**Expected findings:**
- Formula: `velocity = completed_sp / sprint_duration`
- Measured over last 2-4 sprints
- Used for capacity planning

**Your implementation:**
```python
team_pace = total_completed_sp / total_dev_days
hours_per_sp = 8.0 / team_pace
```

**Verification:**
- First sprint defaults to 30 SP ✓
- Later sprints use actual velocity ✓
- Converts to hours using standard 8-hour workday ✓

---

### Scenario 3: Validate Risk Thresholds

**Search:** `"schedule risk prediction machine learning software"`

**Expected findings:**
- Schedule risk = probability of missing deadline
- Quality risk = defect/bug probability  
- Productivity drag = team slowdown

**Your thresholds:**
| Metric | Strict | Standard | Lenient |
|--------|--------|----------|---------|
| Schedule | 30% | 50% | 70% |
| Quality | 60% | 70% | 80% |
| Productivity | -20% | -30% | -40% |

**Verification:** Are these conservative/balanced/permissive?

---

### Scenario 4: Validate Goal Alignment Scoring

**Search:** `"TF-IDF cosine similarity NLP text matching"`

**Expected findings:**
- TF-IDF = Term Frequency-Inverse Document Frequency
- Cosine similarity ranges 0-1 (0=no match, 1=perfect match)
- >0.50 typically means "strong match"

**Your implementation:**
```
alignment_score = tfidf_cosine_similarity(sprint_goal, task_description)

0.50+ = STRONGLY_ALIGNED ✓
0.30-0.50 = PARTIALLY_ALIGNED ✓
<0.30 = UNALIGNED ✓
```

**Verification:** Does 0.50 feel like a reasonable "strong match" threshold?

---

### Scenario 5: Validate Per-Person-Per-Day Calculation

**Search:** `"focus factor agile estimation hours per person per day"`

**Expected findings:**
- Not all 8 hours are productive (meetings, breaks, context switch)
- "Focus factor" or "focus hours" = actual coding time
- Typically 4-6 hours per developer
- Can be calculated from sprint history

**Your formula:**
```
hours_per_sp = (assignees × days × 8) / completed_sp
focus_hours = (completed_sp / sprint_days) × hours_per_sp / assignees
Capped: 2.0 - 10.0 hours/person/day
```

**Verification:**
- Does the calculated value (2.0-10.0) match typical ranges?
- Is it based on actual sprint data?

---

## 3. Step-by-Step: How to Search While Testing

### Example: Verifying Story Point Suggestion

**Step 1: Run Your Tool**
```
npm run dev
# or pnpm dev
```

**Step 2: Open Parallel Browser Tabs**
- Tab 1: Your local app (`http://localhost:3000`)
- Tab 2: Google/Search engine

**Step 3: Test a Case**
In Tab 1:
- Enter task: "Implement two-factor authentication"
- Description: "Add TOTP and SMS 2FA options, update API, add UI"
- Click AI → gets suggestion "8 SP"

**Step 4: Research in Tab 2**
Search: `"two factor authentication feature development story points"`

**Step 5: Compare**
- Industry examples suggest 8-13 SP for 2FA
- Your prediction of 8 SP is reasonable ✓

**Step 6: Continue Testing**
Back to Tab 1: Try more examples, verify consistency

---

## 4. Real Testing Examples

### Test Case 1: High Alignment Task

**Setup:**
- Sprint Goal: "Improve API security"
- Task: "Add OAuth2 social login for Google/GitHub"
- Expected: HIGH ALIGNMENT (>0.50)

**Search:** `"OAuth2 authentication security best practices"`
- Confirms OAuth2 is security-focused
- Confirms this is highly aligned with "improve API security"

**Verify in app:**
- Alignment score should be ≥0.50 ✓
- Color should be green ✓

---

### Test Case 2: Low Alignment Task

**Setup:**
- Sprint Goal: "Improve API security"
- Task: "Update user dashboard design colors"
- Expected: LOW ALIGNMENT (<0.30)

**Search:** `"UI design color update security implications"`
- Confirms this is UI/design focused
- Not security-related

**Verify in app:**
- Alignment score should be <0.30 ✓
- Color should be red ✓
- Recommendation should DEFER or caution ✓

---

### Test Case 3: Risk Validation

**Setup:**
- Sprint: 3 days remaining, 28/30 SP loaded
- Task: 8 SP, High priority, complex feature

**Calculations:**
- Free capacity = 30 - 28 = 2 SP
- New task 8 SP > free 2 SP
- Schedule risk should be HIGH (less than 3 days to complete 8 SP)

**Search:** `"sprint completion risk estimation 3 days"`

**Verify in app:**
- Schedule risk > 50% (default threshold) ✓
- Recommendation = DEFER or SWAP ✓

---

## 5. API Testing with Web Search

You can also verify API responses match expected formats:

### Using Browser DevTools

**Step 1:** Open DevTools (F12)
**Step 2:** Go to Network tab
**Step 3:** Interact with app
**Step 4:** Look at API calls:

**POST /api/analyze-impact response:**
```json
{
  "schedule_risk": 15.3,
  "quality_risk": 18.7,
  "velocity_change": 1.2,
  "effort_hours": 22.9
}
```

**Search:** `"ML model regression output validation"`
- Confirms ranges make sense
- Values are percentages/numbers as expected

**POST /api/recommend response:**
```json
{
  "recommendation_type": "SWAP",
  "reasoning": "Sprint at capacity...",
  "target_ticket": {...},
  "impact_analysis": {...}
}
```

**Search:** `"recommendation engine output format"`
- Confirms structure is logical
- All fields are populated

---

## 6. Checklist: Complete Verification

Use this checklist while searching and testing:

### Story Point Suggestion
- [ ] Predictions are in 1-21 range
- [ ] Web search confirms range is standard (Fibonacci)
- [ ] Confidence scores are reasonable (50-95%)
- [ ] Different tasks get different predictions
- [ ] Similar descriptions get similar predictions

### Velocity & Team Pace
- [ ] First sprint defaults to 30 SP
- [ ] Later sprints use actual velocity
- [ ] Hours conversion uses 8-hour workday
- [ ] Hours per SP makes sense (typically 2-6)
- [ ] Web search confirms 8-hour day standard

### Per-Person-Per-Day
- [ ] Calculated from last sprint data
- [ ] Falls in 2.0-10.0 range
- [ ] Web search confirms typical is 4-6 hours
- [ ] Used in effort prediction
- [ ] Matches team's actual productivity

### Sprint Goal Alignment
- [ ] Scoring is 0-1 (TF-IDF)
- [ ] 0.50+ = GREEN (strongly aligned)
- [ ] 0.30-0.50 = YELLOW (partial)
- [ ] <0.30 = RED (not aligned)
- [ ] Web search confirms 0.50 is good threshold

### ML Risk Predictions
- [ ] Schedule risk 0-100%
- [ ] Quality risk 0-100%
- [ ] Productivity -50% to +50%
- [ ] Effort in hours
- [ ] All values within reasonable bounds
- [ ] Web search confirms thresholds match industry

### Recommendations
- [ ] Correct action (ADD/DEFER/SWAP/SPLIT)
- [ ] Reasoning is clear
- [ ] Includes alignment context
- [ ] Action plan has concrete steps
- [ ] Swap targets are valid

---

## 7. Common Search Queries by System

### For Story Point Suggestion
```
"story points agile" 
"story point estimation technique"
"machine learning effort estimation"
"XGBoost regression examples"
"feature extraction software metrics"
```

### For Velocity & Hours
```
"sprint velocity calculation formula"
"team velocity agile"
"focus factor productivity"
"work capacity planning"
"8 hour workday productivity"
```

### For Alignment
```
"sprint goal definition"
"scope creep prevention"
"task alignment metrics"
"TF-IDF text similarity"
"NLP cosine similarity"
```

### For Risk & Quality
```
"schedule risk software projects"
"defect prediction machine learning"
"quality risk assessment"
"productivity metrics agile"
"technical debt impact"
```

### For Rule-Based Recommendations
```
"decision tree recommendation engine"
"rule-based system software"
"priority matrix decision making"
"capacity-driven planning"
"sprint commit best practices"
```

---

## 8. Tools for Verification

While testing, you can use these tools to verify data:

### Browser Tools
- **DevTools Network Tab** — Check API responses
- **DevTools Console** — Log variables, test functions
- **DevTools Performance** — Check slow operations

### External Tools
- **Postman** — Test APIs directly
- **curl** — Command-line API testing
- **Regex tools** — Validate date formats
- **JSON validators** — Check API response structure

### Search & Documentation
- **Google** — General questions
- **GitHub** — Code examples, libraries
- **Stack Overflow** — Specific technical issues
- **Official docs** — Framework/library reference

---

## 9. Example Search Journey

**Goal:** Verify that your recommendation system makes logical sense

**Search 1:**
```
"agile sprint planning best practices"
```
Learn about sprint structure, capacity planning, priority

**Search 2:**
```
"schedule risk prediction software project management"
```
Understand how to identify scheduling risks

**Search 3:**
```
"machine learning task prioritization"
```
See how ML is used in similar systems

**Search 4:**
```
"recommendation engine design patterns"
```
Compare your rule-based approach to alternatives

**Search 5:**
```
"sprint goal alignment definition"
```
Verify your alignment scoring makes sense

**Result:**
You've now verified that your implementation approach is sound and matches industry best practices.

---

## Summary

**To test with web search:**
1. Run app in one browser tab
2. Open search in another tab
3. As you test a feature, search for related documentation
4. Compare your implementation against best practices
5. Use the checklists to verify all systems work correctly

This approach ensures your implementation is not just functional, but also aligned with industry standards and proven practices.
