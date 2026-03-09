# Quick Start Guide — Testing & Verification

## 5-Minute Setup

### 1. Start the Application
```bash
npm run dev
# or
pnpm dev
```

Application opens at: `http://localhost:3000`

### 2. Open the Impact Analyzer
Navigate to the sprint impact service page where you'll see:
- Sprint selector
- Task input form
- Capacity bar
- Results panel

### 3. Quick Test

**Enter a task:**
```
Title: "Add payment processing with Stripe"
Description: "Integrate Stripe API, update payment flow, add webhook handlers"
Story Points: (click "AI" to suggest)
Priority: High
```

**Click "AI" button** → Get suggested story points

**Click "Analyze Impact"** → See:
- Hours translation
- Goal alignment
- 4 risk metrics
- Recommendation with reasoning

---

## Understanding the Output

### Capacity Bar
```
25 / 30 SP (71 / 86 hours)
[████████░░] 83% used | 5 days remaining
```
**Meaning:** Using 25 of 30 story points (71 of 86 hours), 83% full

### Goal Alignment
```
✅ STRONGLY_ALIGNED (68%)
Task closely matches sprint goal
```
**Meanings:**
- ✅ Green (0.50+) = Safe to add
- 🔍 Yellow (0.30-0.50) = Review with team
- ⏸ Red (<0.30) = Likely scope creep

### Risk Cards (Click to expand)
```
SCHEDULE RISK: 15% [NOMINAL]
QUALITY RISK: 18% [NOMINAL]
PRODUCTIVITY: +1.2% [NOMINAL]
EFFORT: 22.9 hours [NOMINAL]
```
**Status levels:**
- NOMINAL = Safe ✓
- CAUTION = Review ⚠️
- ALERT = High risk ❌

### Recommendation
```
🔄 SWAP
Sprint at capacity. Removing 'Update docs' to make room.
[APPLY SWAP] [ADD] [DEFER] [SPLIT]
```
**Actions:**
- **ADD** = Safe to add to sprint
- **DEFER** = Add to backlog instead
- **SWAP** = Replace lower-priority item
- **SPLIT** = Break into smaller pieces

---

## Testing Each System

### Test 1: Story Point Suggestion (2 minutes)
1. Enter task description
2. Click "AI" button next to Story Points
3. See suggested value (1-21)
4. Try different tasks → predictions vary

**Verify:** Predictions make sense for task complexity

**XGBoost Model Details:**
- Uses 105 features (5 numeric + 100 TF-IDF)
- Predicts 1-21 SP
- Returns confidence score (50-95%)

---

### Test 2: Hours Translation (1 minute)
1. Change story points (e.g., to 5)
2. See hours display: "5 SP (~14 Hours)"
3. Hours = story_points × hours_per_sp

**Verify:** Hours increase proportionally with SP

**Team Pace Logic:**
- Calculated from last 20 completed sprints
- Formula: `team_pace = completed_sp / dev_days`
- Conversion: `hours_per_sp = 8.0 / team_pace`

---

### Test 3: Goal Alignment (2 minutes)
1. Select sprint with defined goal
2. Enter task well-aligned with goal (e.g., goal="improve auth", task="add 2FA")
3. See green alignment strip (0.50+)
4. Try misaligned task
5. See red strip (<0.30)

**Verify:** Alignment score matches task relevance

**TF-IDF Scoring:**
- Cosine similarity (0-1)
- 0.50+ = STRONGLY_ALIGNED ✅
- 0.30-0.50 = PARTIALLY_ALIGNED 🔍
- <0.30 = UNALIGNED ⏸

---

### Test 4: Impact Analysis (2 minutes)
1. Fill form completely
2. Click "Analyze Impact"
3. See 4 risk cards appear
4. Click cards to expand explanations

**Verify:** Risk values are reasonable (0-100% for risk, hours > 0)

**4 ML Models:**
1. **Effort** (XGBoost Regressor) → hours needed
2. **Schedule Risk** (XGBoost Classifier) → deadline probability (%)
3. **Quality Risk** (Logistic Regression) → defect probability (%)
4. **Productivity** (XGBoost+MLP) → velocity change (%)

---

### Test 5: Recommendation Engine (3 minutes)
**Scenario A: Safe to Add**
- Current load: 20/30 SP
- New task: 5 SP, High priority, strongly aligned
- Recommendation: **ADD** ✓

**Scenario B: Over Capacity**
- Current load: 28/30 SP  
- New task: 8 SP, Medium priority
- Recommendation: **SWAP** (find lower-priority item)

**Scenario C: Misaligned**
- Sprint goal: "Improve performance"
- New task: "Update dashboard colors"
- Recommendation: **DEFER** (scope creep)

**Scenario D: Large + Time Pressure**
- Days remaining: 5
- New task: 13 SP
- Recommendation: **SPLIT** (too large for time)

**Rule-Based Engine:**
- Rule 0: Sprint almost over → DEFER
- Rule 0.5: Critical priority → FORCE SWAP or OVERLOAD
- Rule 1: Large item late in sprint → SPLIT
- Rule 2: ML safety net → DEFER (with alignment boost)
- Rule 3: Enough capacity → ADD (with alignment sentiment)
- Rule 4: Sprint full → SWAP
- Rule 5: No option → DEFER

---

## Using Web Search While Testing

### While Testing Alignment
Open new tab → Search: `"sprint goal definition agile"`
- Verify your goal is specific enough
- Compare to examples

### While Testing Risk
Open new tab → Search: `"schedule risk prediction software"`
- Learn what causes schedule risk
- Verify thresholds make sense

### While Testing Velocity
Open new tab → Search: `"team velocity agile calculation"`
- Understand your velocity number
- See how it's typically used

### While Testing Hours/Capacity
Open new tab → Search: `"focus factor agile hours per person per day"`
- Verify 2-10 hours/person/day is reasonable
- Learn about context switching costs

---

## Debugging Tips

### Check Console (F12 → Console)
```javascript
// Log task data
console.log(form)

// Log analysis results
console.log(analysis)

// Log recommendation
console.log(recommendation)

// Log hours per SP
console.log(hoursPerSP)
```

### Check Network (F12 → Network)
1. Click "Analyze Impact"
2. Watch Network tab
3. See API calls:
   - `POST /api/ai/suggest-points` → Story points
   - `GET /api/sprints/{id}/context` → Sprint capacity
   - `GET /api/analytics/spaces/{id}/team-pace` → Team pace
   - `POST /api/analyze-impact` → ML predictions
   - `POST /api/ai/align-sprint-goal` → Goal alignment
   - `POST /api/recommend` → Recommendation
4. Click each → Check Payload and Response

### Common Issues

**Issue: "No sprint selected"**
- Select a sprint from dropdown first

**Issue: Analysis takes long**
- ML models are processing (normal)
- Check Network tab for slow requests

**Issue: Recommendation seems wrong**
- Check: capacity available? (free_capacity >= new_sp)
- Check: risk scores (schedule, quality, productivity)
- Check: days remaining (<2 days → DEFER)
- Check: alignment score (affects thresholds)

**Issue: Hours don't match estimate**
- Uses team's historical pace, not personal estimate
- Formula: `story_points × hours_per_sp = hours`
- If you estimate differently, discuss with team

---

## Data You Should Know

### Default Values
- First sprint capacity: 30 SP
- Hours per workday: 8 hours
- Min days for new work: 2 days
- Large ticket threshold: 13 SP
- Alignment threshold: 0.50+ = strongly aligned

### ML Thresholds (Standard Risk Appetite)
- Schedule risk DEFER: >50%
- Quality risk DEFER: >70%
- Productivity drag DEFER: <-30%
- (Strict/Lenient variants available)

### Alignment Boost (Enhanced Rules)
- Well-aligned (≥0.50): Lower thresholds by 5%
- Misaligned (<0.30): Raise thresholds by 10%
- Example: Schedule threshold drops from 50% to 45% if aligned

### Per-Person-Per-Day Formula
```
hours_per_sp = (assignees × days × 8) / completed_sp
focus_hours = (completed_sp / days) × hours_per_sp / assignees
Capped: 2.0 - 10.0 hours/person/day
```

---

## Common Questions

**Q: Why did it recommend DEFER instead of ADD?**
A: Check the reasoning. Usually:
- Not enough capacity
- Risk too high (schedule, quality, or productivity)
- Not aligned with sprint goal (<0.30)
- Days remaining too low (<2 days)

**Q: Why are hours different from my estimate?**
A: Uses team's historical pace. If you estimate 4 hours but team pace shows 6 hours/SP, use 6.

**Q: How is alignment calculated?**
A: TF-IDF cosine similarity compares sprint goal text to task description.
Example:
- Goal: "improve security"
- Task: "add OAuth2 authentication"  
- Similarity: 0.78 (STRONGLY_ALIGNED)

**Q: Can I override recommendations?**
A: Yes! You can click [ADD] [DEFER] [SWAP] [SPLIT] buttons to override.

**Q: How do I improve predictions?**
A: Complete more sprints. System learns from historical data.

**Q: What if the first sprint shows 30 SP default?**
A: Correct. First sprint uses 30 SP default until historical data exists.

---

## Next Steps

1. **Test all 5 scenarios** (Story Points, Hours, Alignment, Analysis, Recommendation)
2. **Try edge cases** (empty sprint, full sprint, critical priority)
3. **Compare to web** (search related agile concepts)
4. **Gather team feedback** (do recommendations make sense?)
5. **Monitor accuracy** (do real sprints match predictions?)

---

## Complete Documentation

For detailed information:
- **FINAL_IMPLEMENTATION_STATUS.md** — Full architecture & components
- **TESTING_AND_INTEGRATION_GUIDE.md** — Comprehensive testing guide
- **WEB_SEARCH_AND_VERIFICATION_GUIDE.md** — How to verify with web search
- **SYSTEM_LOGIC_DOCUMENTATION.md** — Technical implementation details
- **INTEGRATION_IMPROVEMENTS_SUMMARY.md** — Recent enhancements

---

## Support

For issues:
1. Check the relevant guide (see above)
2. Search documentation for your issue
3. Review console (F12) for errors
4. Check Network tab (F12) for API failures
5. Compare implementation to TESTING_AND_INTEGRATION_GUIDE.md

---

**Ready to test? Start with "Test 1" above!**
