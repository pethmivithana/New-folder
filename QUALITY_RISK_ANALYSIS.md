# Quality Risk Model Analysis

## Executive Summary

The quality risk model **IS working and differentiating** between tasks, but it shows **counterintuitive behavior**: larger, more critical tasks have *lower* defect risk than smaller tasks. This is backwards from typical Agile expectations.

---

## Debug Output Results

### Test Case 1: 5 SP + Medium Priority
```
INPUT: 5 SP, Medium Priority, 10 days remaining
NORMALIZED FEATURES:
  [0] prio_norm = 4.0 / 4.0 = 1.0000      (Medium = highest normalized value)
  [1] desc_complexity = 0.2420
  [2] pressure_norm = 0.0357
  [3] days_norm = 0.7143
  [4] sp_norm = 0.3333
  [5] sprint_progress = 0.2143

OUTPUT: 40.5% Defect Risk
```

### Test Case 2: 13 SP + Critical Priority
```
INPUT: 13 SP, Critical Priority, 10 days remaining
NORMALIZED FEATURES:
  [0] prio_norm = 1.0 / 4.0 = 0.2500      (Critical = LOWEST normalized value)
  [1] desc_complexity = 0.2420
  [2] pressure_norm = 0.0929
  [3] days_norm = 0.7143
  [4] sp_norm = 1.0000                    (13 SP = max)
  [5] sprint_progress = 0.2143

OUTPUT: 32.0% Defect Risk  ← LOWER than 5 SP!
```

### Test Case 3: 3 SP + Low Priority
```
INPUT: 3 SP, Low Priority, 10 days remaining
NORMALIZED FEATURES:
  [0] prio_norm = 2.0 / 4.0 = 0.5000
  [1] desc_complexity = 0.2420
  [2] pressure_norm = 0.0214
  [3] days_norm = 0.7143
  [4] sp_norm = 0.1667
  [5] sprint_progress = 0.2143

OUTPUT: 39.9% Defect Risk
```

---

## Key Finding: The Counterintuitive Pattern

| Story Points | Priority  | Pressure | Defect Risk |
|:---:|:---:|:---:|:---:|
| 3  | Low       | 0.021 | 39.9% |
| 5  | Medium    | 0.036 | 40.5% |
| 13 | Critical  | 0.093 | 32.0% |

**Expected behavior:** 13 SP Critical → High defect risk (45%+)  
**Actual behavior:** 13 SP Critical → Low defect risk (32%)

---

## Root Cause Analysis

### Issue 1: Priority Encoding is Inverted
```python
# Current encoding in feature_engineering.py
"Critical" → code=1.0 → prio_norm = 1.0 / 4.0 = 0.25   (LOWEST normalized value)
"Medium"   → code=4.0 → prio_norm = 4.0 / 4.0 = 1.00   (HIGHEST normalized value)
"Low"      → code=2.0 → prio_norm = 2.0 / 4.0 = 0.50
```

**Problem:** The normalization makes Critical priority (1.0) the SMALLEST value (0.25), which signals to the model that critical tasks are "low severity", not "high severity".

### Issue 2: Model Training Likely Had This Inverted Pattern
The TabNet model learned: **Lower priority_norm → Lower defect risk**

If the training data had this pattern (e.g., more defects in low-priority tasks which got less code review), the model is correctly predicting that pattern, but it doesn't match real-world expectations.

---

## Why This Happens

### Feature Normalization Problem

1. **Priority codes:** 1 (Critical) to 4 (Low)
2. **Normalization:** Divides by 4.0
3. **Result:** 
   - Critical (1) → 0.25 (smallest)
   - Low (4) → 1.00 (largest)
4. **TabNet interprets:** "Small number = less important"

### What Should Happen

The model should learn: **Critical priority + Large story points = HIGH defect risk**

But the feature encoding makes it learn: **High prio_norm (Medium/Low) + Moderate SP = Higher defect risk**

---

## Solutions

### Option A: Flip Priority Encoding (Recommended)
Change feature engineering to encode priority in reverse:
- Critical → 1.0 (highest)
- Medium → 0.5
- Low → 0.0 (lowest)

**Code change:**
```python
# Instead of: prio_norm = prio_code / 4.0
# Use: prio_norm = (5.0 - prio_code) / 4.0  # Invert so Critical=1.0, Low=0.0
```

### Option B: Retrain the Model
With fixed priority encoding, the model would learn:
- Critical + Large SP = High defect risk
- Low + Small SP = Low defect risk

### Option C: Use Pressure as Primary Signal
Focus on `pressure_norm` which does increase with SP:
- 3 SP: pressure = 0.021
- 13 SP: pressure = 0.093

Larger tasks naturally have higher pressure, which should correlate with defect risk.

---

## Model Performance Assessment

**Current State:**
- ✓ Model is running without errors (fixed sys import)
- ✓ Features are properly shaped and normalized
- ✓ TabNet is producing probabilistic outputs
- ✗ Feature encoding makes priority signals backwards
- ✗ Results contradict Agile best practices

**Conclusion:** The model is **technically working but semantically incorrect**. Priority normalization needs to be fixed before the quality risk predictions will be reliable.

---

## Recommended Next Steps

1. **Fix priority encoding** in `build_quality_features()` to make Critical=high, Low=low
2. **Retrain TabNet model** with corrected features
3. **Verify with test cases** that larger, critical tasks now show higher defect risk
4. **Update all other models** to use consistent priority encoding
