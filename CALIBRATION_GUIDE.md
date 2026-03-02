# Model Calibration Guide

This guide explains how to fix the two flagged issues from the assessment and calibrate the ML models to your specific domain.

---

## Issue 1: Productivity Impact Log-Space Decoding

### Problem
The log-space decoding constant (`exp(raw_avg)`) for the productivity drag prediction was inferred but never verified against actual ground truth. The assessment reports `-39% drop`, but this may be systematically too high or too low.

### Solution
**File:** `services/sprint_impact_service/impact_predictor.py`  
**Constant:** `PRODUCTIVITY_LOG_SCALE` (line ~48)

#### Step 1: Collect Ground Truth
Track 3-5 tickets where you know the actual productivity drag. For example:
- Ticket: "Refactor payment module" (8 SP)
  - Actual observed velocity drop: 45%
  - Predicted by model: 39%

#### Step 2: Calculate Calibration Factor
```
Scale = Actual / Predicted
Example: 45% / 39% = 1.15
```

#### Step 3: Update the Constant
```python
# In impact_predictor.py, line ~48:
PRODUCTIVITY_LOG_SCALE = 1.15  # Adjusted: was 1.0
```

#### Step 4: Validate
- Rerun predictions on your ground truth samples
- Check if predictions now match actual drag
- Iterate if needed

---

## Issue 2: Quality Risk Underestimation for Architectural Tasks

### Problem
The TabNet-based quality risk model returns `34% defect risk` for a complex microservices migration, which the assessment deems too low. Architectural work typically has higher defect rates due to complexity.

### Solution
**File:** `services/sprint_impact_service/impact_predictor.py`  
**Constant:** `QUALITY_RISK_COMPLEXITY_MULTIPLIER` (line ~51)

#### Step 1: Identify Complexity Signals
The code now auto-detects architectural tasks by looking for keywords:
- Task type: "architecture", "refactor", "migration", "monolith", "microservice"
- Title contains: same keywords
- Story points ≥ 13 (large tickets)

#### Step 2: Measure Actual Defect Rates
For your past complex tickets, calculate:
```
Actual defect rate = (bugs found in QA + production issues) / story points completed
Example: 15 bugs / 21 SP = 71% defect likelihood
```

#### Step 3: Calculate Multiplier
```
Multiplier = Actual / Predicted (for architectural tasks only)
Example: 71% / 34% = 2.09, so round to 2.0-2.1
```

#### Step 4: Update the Constant
```python
# In impact_predictor.py, line ~51:
QUALITY_RISK_COMPLEXITY_MULTIPLIER = 2.1  # Adjusted: was 1.0
```

#### Step 5: Verify
- Rerun predictions on architectural tickets
- Check if quality risk now flags appropriately
- Fine-tune if systematic under/overestimation remains

---

## Issue 3: Recommendation Engine Thresholds (Optional Tuning)

### Background
The RecommendationEngine uses three thresholds to decide when to DEFER work:
- **SCHEDULE_RISK_THRESHOLD**: 50% (spillover probability)
- **PROD_DRAG_THRESHOLD**: -30% (productivity drop)
- **QUALITY_RISK_THRESHOLD**: 70% (defect likelihood, was relaxed from 30%)

### When to Adjust

#### If you see too many false DEFER recommendations:
- **Schedule risk:** Increase `SCHEDULE_RISK_THRESHOLD` to 60-70%
- **Productivity drag:** Increase `PROD_DRAG_THRESHOLD` (make less negative, e.g., -40%)
- **Quality risk:** Increase `QUALITY_RISK_THRESHOLD` to 75-80%

#### If you see undetected risks (missed deferrals):
- **Schedule risk:** Decrease `SCHEDULE_RISK_THRESHOLD` to 40%
- **Productivity drag:** Decrease `PROD_DRAG_THRESHOLD` to -20%
- **Quality risk:** Decrease `QUALITY_RISK_THRESHOLD` to 50-60%

### How to Update
**File:** `services/sprint_impact_service/recommendation_engine.py`  
**Lines:** 6-35 (calibration section)

```python
SCHEDULE_RISK_THRESHOLD = 50.0  # Adjust as needed
PROD_DRAG_THRESHOLD     = -30.0  # More negative = stricter
QUALITY_RISK_THRESHOLD  = 70.0  # Higher = more permissive
```

---

## Validation Workflow

1. **Collect 5-10 historical tickets** with known actual outcomes
2. **Run predictions** on those tickets using updated constants
3. **Compare predicted vs. actual** for each metric
4. **Calculate MAPE** (Mean Absolute Percentage Error)
   ```
   MAPE = avg(|predicted - actual| / actual * 100%)
   Target: < 15% MAPE
   ```
5. **Iterate** if MAPE > 15%
6. **Document** the final calibration in `CALIBRATION_SAMPLES` (commented section, line ~54)

---

## Ground Truth Template

Create a `.json` file to track calibration samples:

```json
{
  "calibration_samples": [
    {
      "ticket_id": "JIRA-1234",
      "title": "Migrate Monolith User Service to Microservices",
      "story_points": 21,
      "task_type": "architecture",
      "predicted_productivity_drag": 39,
      "measured_productivity_drag": 45,
      "predicted_quality_risk": 34,
      "measured_defect_rate": 71,
      "sprint_date": "2026-03-02"
    }
  ]
}
```

---

## Code Changes Summary

### `impact_predictor.py`
- ✅ Added `PRODUCTIVITY_LOG_SCALE` constant with detailed comments
- ✅ Updated `_predict_productivity()` to use the scaling constant
- ✅ Added `QUALITY_RISK_COMPLEXITY_MULTIPLIER` constant
- ✅ Updated `_predict_quality_risk()` to detect and adjust for architectural complexity
- ✅ Added `CALIBRATION_SAMPLES` template (commented) for ground truth tracking

### `recommendation_engine.py`
- ✅ Moved thresholds from class attributes to module-level constants
- ✅ Added detailed inline documentation on threshold tuning strategy
- ✅ Updated `_generate_recommendation()` to use module-level thresholds
- ✅ ML Safety Net logic now references calibrated constants

---

## Next Steps

1. Gather ground truth data from 5-10 past tickets
2. Calculate scale factors for productivity and quality
3. Update the constants in the code
4. Revalidate on your test set
5. Deploy and monitor new predictions
6. Revisit calibration quarterly or after major project phases

