# ML Model Backend Bug Fixes - Summary

## Overview
Fixed three critical bugs in the Agile Replanning Decision Support System that were causing the schedule_risk prediction to almost always return 99% probability of spillover.

## Bugs Fixed

### 1. **Feature Faking Bug** ✓
**File:** `services/sprint_impact_service/feature_engineering.py`
**Function:** `build_schedule_risk_features()`
**Line:** Changed `total_comments = float(len(description.split('.')))`

**Problem:**
- `total_comments` was calculated by counting periods (`.`) in the description
- A simple 10-sentence ticket has 10 periods, which the model interpreted as 10 comments
- The model learned that high comment counts indicate highly delayed, controversial tickets
- New tickets without actual comments were getting the wrong signal

**Solution:**
- Default `total_comments` to `0.0` for new tickets
- This prevents false signals about ticket controversy

**Code Change:**
```python
# BEFORE:
total_comments  = float(len(description.split('.')))

# AFTER:
total_comments  = 0.0  # BUG FIX: Default to 0.0 for new tickets instead of counting periods
```

---

### 2. **Feature Names Bug** ✓
**File:** `services/sprint_impact_service/feature_engineering.py`
**Function:** `build_schedule_risk_features()`
**Return Type:** Changed from `np.ndarray` to `pd.DataFrame`

**Problem:**
- Features were returned as a raw NumPy array without column names
- XGBoost model was trained on a Pandas DataFrame with explicit column names
- XGBoost couldn't map feature indices correctly without explicit column alignment
- This caused features to be passed to the model in wrong order or with wrong interpretation

**Solution:**
- Return a Pandas DataFrame with explicit column names matching the training schema
- Column order: `['Story_Point', 'total_links', 'total_comments', 'author_total_load', 'link_density', 'comment_density', 'pressure_index', 'Type_Code', 'Priority_Code']`

**Code Change:**
```python
# BEFORE:
X = np.array([[...]])
if _risk_imputer is not None:
    X = _risk_imputer.transform(X)
return X  # Raw numpy array

# AFTER:
X = np.array([[...]])
if _risk_imputer is not None:
    X = _risk_imputer.transform(X)

# BUG FIX: Return DataFrame with explicit column names
feature_names = ['Story_Point', 'total_links', 'total_comments', 'author_total_load',
                 'link_density', 'comment_density', 'pressure_index', 'Type_Code', 'Priority_Code']
df = pd.DataFrame(X, columns=feature_names)
return df  # DataFrame with column names
```

---

### 3. **Probability Indexing Bug** ✓
**File:** `services/sprint_impact_service/impact_predictor.py`
**Function:** `_predict_schedule_risk()`
**Line:** Changed hardcoded indices to dynamic class mapping

**Problem:**
- Code used hardcoded indices: `proba[0] + proba[1]` to extract spillover probability
- Assumed class 0 = Critical Risk, class 1 = High Risk
- If model's class order changed or was trained differently, this would silently produce wrong results
- No defensive checking against actual model.classes_

**Solution:**
- Dynamically check `model.classes_` to find correct indices for 'Critical Risk' and 'High Risk'
- Sum probabilities only for the correct class indices
- Handles any class ordering from the trained model

**Code Change:**
```python
# BEFORE:
proba = self.models['schedule_risk'].predict_proba(X)[0]
# Classes: 0=Critical Risk, 1=High Risk, 2=Low Risk, 3=Medium Risk
# Spillover probability = P(Critical) + P(High)
spillover_prob = _cap(float((proba[0] + proba[1]) * 100))

# AFTER:
model = self.models['schedule_risk']
proba = model.predict_proba(X)[0]

# BUG FIX: Dynamically check model.classes_ instead of hardcoded indices
classes = model.classes_
critical_idx = None
high_idx = None

for idx, class_label in enumerate(classes):
    if class_label == 'Critical Risk':
        critical_idx = idx
    elif class_label == 'High Risk':
        high_idx = idx

# Spillover probability = P(Critical Risk) + P(High Risk)
spillover_prob_value = 0.0
if critical_idx is not None:
    spillover_prob_value += float(proba[critical_idx])
if high_idx is not None:
    spillover_prob_value += float(proba[high_idx])

spillover_prob = _cap(spillover_prob_value * 100)
```

---

## Files Modified

1. **services/sprint_impact_service/feature_engineering.py**
   - Added `import pandas as pd` 
   - Fixed `build_schedule_risk_features()` function (3 changes):
     - Set `total_comments = 0.0` instead of counting periods
     - Changed return type from `np.ndarray` to `pd.DataFrame`
     - Added explicit column names to DataFrame

2. **services/sprint_impact_service/impact_predictor.py**
   - Fixed `_predict_schedule_risk()` method:
     - Replaced hardcoded indices with dynamic `model.classes_` lookup
     - Added defensive null checks for critical_idx and high_idx

## Expected Results

- **Before:** Schedule risk prediction returns ~99% spillover probability for most tickets
- **After:** Schedule risk prediction returns realistic probabilities based on actual ticket complexity and sprint timeline

## Testing Recommendations

1. Test with new tickets (empty description) → should not return 99% risk
2. Test with simple tickets → should return low risk
3. Test with complex, high-priority tickets → should return high risk
4. Verify probability values fall within realistic ranges (0-100%)

## No Other Changes

All other implemented functions remain unchanged:
- Effort prediction (XGBoost)
- Quality risk prediction (TabNet)
- Productivity prediction (hybrid XGBoost + MLP)
- Sprint goal alignment
