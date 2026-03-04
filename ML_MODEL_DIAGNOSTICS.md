# ML Model Diagnostics Guide

## Quick Diagnosis: "Schedule Risk is Always 0%"

If schedule risk is showing 0% for all items, this indicates one of these problems:

### 1. **Classes Not Found (Most Likely)**
The model's `classes_` might not be the string labels we expect.

**Check with:**
```bash
python scripts/debug_ml_models.py
```

Look for the "Classes" section in the output. You'll see something like:
```
Classes (4 total):
    [0] Critical Risk (type: str)
    [1] High Risk (type: str)
    [2] Low Risk (type: str)
    [3] Medium Risk (type: str)
```

If classes are **integers** (0, 1, 2, 3) instead of strings, that's the problem!

### 2. **Features Being Built Incorrectly**
The feature DataFrame might have the wrong shape or column names.

**Check the debug output for:**
- `Features built successfully` - confirms shape is (1, 9)
- Column names - should match training schema exactly

### 3. **Model Input Format Issue**
The model expects a DataFrame with specific column names (from training), but you're passing something else.

---

## Understanding the Schedule Risk Model

### Model Structure
- **Type:** XGBClassifier (Multi-class classification)
- **Classes:** 4 (Critical Risk, High Risk, Low Risk, Medium Risk)
- **Input Features:** 9
- **Output:** Probability distribution over 4 classes

### Feature Schema (Must Match Exactly)
```python
['Story_Point', 'total_links', 'total_comments', 'author_total_load',
 'link_density', 'comment_density', 'pressure_index', 'Type_Code', 'Priority_Code']
```

### How Schedule Risk Probability Works

1. **Model predicts** probability of each class
   ```
   P(Critical Risk) = 0.05
   P(High Risk)     = 0.15
   P(Low Risk)      = 0.70
   P(Medium Risk)   = 0.10
   ```

2. **Spillover probability** = P(Critical) + P(High)
   ```
   Spillover = 0.05 + 0.15 = 0.20 = 20%
   ```

3. **Dominant class** = class with highest probability
   ```
   Dominant = Low Risk (70%)
   ```

4. **Status thresholds:**
   - > 50% spillover → "critical" status, "High Risk" label
   - > 30% spillover → "warning" status, "Moderate Risk" label
   - ≤ 30% spillover → "safe" status, "Low Risk" label

---

## Debugging Checklist

### ✓ Step 1: Run the Debug Script
```bash
cd /vercel/share/v0-project
python scripts/debug_ml_models.py 2>&1 | tee debug_output.txt
```

### ✓ Step 2: Check Console Output
Look for:
1. **"✓ Model loaded successfully"** - model file is readable
2. **Classes section** - what are the actual class labels?
3. **Features built successfully** - can build features from test data
4. **Predictions section** - what do raw predictions look like?

### ✓ Step 3: Verify Feature Building
The feature_engineering.py file has debug logging:
- `[BUILD_SCHEDULE_RISK_FEATURES] Shape: (1, 9)`
- `[BUILD_SCHEDULE_RISK_FEATURES] Values: {...}`

Check the actual app logs when making predictions.

### ✓ Step 4: Add Debug Logging to Your API
The impact_predictor.py now has debug statements:
```python
print(f"[v0] Model classes_: {model.classes_}", file=sys.stderr)
print(f"[v0] Probabilities: {proba}", file=sys.stderr)
print(f"[v0] Spillover prob value: {spillover_prob_value}", file=sys.stderr)
```

Monitor these when making actual predictions.

---

## Binary vs Multi-Class Models

### Current Schedule Risk Model: **Multi-Class (4 classes)**
```
Output: Probability distribution
Format: Array of 4 probabilities that sum to 1.0
Display: "X% chance of spillover"
```

If the model were binary (0 or 1):
```
Output: Single probability
Format: Single value between 0 and 1
Display: "X% chance of spillover" OR just "0" or "1"
```

The user mentioned: *"if schedule risk is a binary number like 0 or 1 add that like that without percentage"*

This suggests you might want to check if the actual trained model is binary instead of multi-class. If so, the display logic needs adjustment.

---

## Common Issues & Fixes

### Issue: "Classes are integers [0, 1, 2, 3] not strings"
**Fix:** Update the comparison in impact_predictor.py:
```python
# Instead of:
if class_label == 'Critical Risk':

# Use:
if class_label == 0:  # or whatever index represents high risk
```

### Issue: "Model always predicts class 0 (100% confidence)"
**Fix:** Check if:
1. Features are NaN or all zeros
2. Feature scaling/imputation is wrong
3. Model file is corrupted

### Issue: "Spillover probability is always 0%"
**Fix:** The indices for 'Critical Risk' and 'High Risk' are None
- Classes probably aren't strings
- Use debug script to see actual class labels

### Issue: "Prediction succeeds but values look wrong"
**Fix:** 
1. Verify feature values make sense (debug output)
2. Check that imputation is working
3. Verify type/priority label encoding

---

## How to Monitor ML Model Health

### 1. **Consistency Checks**
- All predictions on same item should be identical
- Probabilities should always sum to ~1.0
- No NaN or Inf values

### 2. **Sanity Checks**
- High story point + short sprint = higher spillover risk ✓
- Complex items (many links/comments) = higher risk ✓
- Simple items = lower risk ✓

### 3. **Production Monitoring**
Add these metrics:
```python
# Log prediction stats
print(f"Model: schedule_risk | Classes: {len(proba)} | Spillover: {spillover_prob}%")

# Track dominant class distribution
print(f"Dominant: {dominant_label} | Confidence: {max(proba)*100:.1f}%")

# Alert if prediction is extreme
if spillover_prob < 1 and max(proba) > 0.95:
    print("⚠️  WARNING: Very confident prediction on new data")
```

---

## If Schedule Risk Should Be Binary (0 or 1)

If the trained model is actually binary:

**Update the code:**
```python
# Instead of:
proba = model.predict_proba(X)[0]  # Returns [P(0), P(1)]
spillover_prob = (proba[0] + proba[1]) * 100  # Wrong!

# Use:
prediction = model.predict(X)[0]  # Returns 0 or 1
spillover_prob = float(prediction)  # Just 0 or 1, no percentage

# Or if you want to keep percentage:
proba = model.predict_proba(X)[0]  # Returns [P(0), P(1)]
risk_probability = proba[1] * 100  # P(risk) = 1 as percentage
```

**Update display:**
```python
return {
    'probability': float(prediction),  # 0 or 1
    'status': 'critical' if prediction == 1 else 'safe',
    'status_label': 'High Risk' if prediction == 1 else 'Low Risk',
}
```

---

## Next Steps

1. Run `python scripts/debug_ml_models.py` and share the output
2. Check what the actual class labels/types are
3. Update the comparison logic if needed
4. Monitor the debug logs in your app
5. Verify predictions make intuitive sense
