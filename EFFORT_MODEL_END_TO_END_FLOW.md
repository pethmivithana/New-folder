# Effort Model End-to-End Flow: From User Input to Frontend Display

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND (React/Next.js)                                             │
│  User creates new requirement                                        │
│  - Enters title, description, story_points, type, priority           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP POST
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND (FastAPI) - Impact Prediction Route                          │
│ /api/predict/impacts  (impact_routes.py:91-150)                      │
│                                                                       │
│ 1. Receives JSON payload with requirement data                       │
│ 2. Validates input (input_validation.py)                             │
│ 3. Builds sprint context                                             │
│ 4. Calls predict_all_impacts()                                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ImpactPredictor (impact_predictor.py)                                │
│ predict_all_impacts() - Line 161                                     │
│                                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ EFFORT PREDICTION PIPELINE (_predict_effort)                    │ │
│ │ ════════════════════════════════════════════════════════════════│ │
│ │                                                                  │ │
│ │ Step 1: FEATURE ENGINEERING                                    │ │
│ │ ────────────────────────────────────────────────────────────   │ │
│ │   build_effort_features(item_data, sprint_context)             │ │
│ │   [feature_engineering.py:163-201]                             │ │
│ │                                                                  │ │
│ │   Extracts 105 features:                                        │ │
│ │   - sprint_load_7d (numeric)                                    │ │
│ │   - team_velocity_14d (numeric)                                 │ │
│ │   - pressure_index = SP / days_remaining (numeric)              │ │
│ │   - total_links (count from description)                        │ │
│ │   - Type_Code = LabelEncoder.transform(type) (numeric)          │ │
│ │   - txt_0 to txt_99 = TF-IDF vector (100 features)              │ │
│ │                                                                  │ │
│ │   TF-IDF vectorizer loaded from effort_artifacts.pkl            │ │
│ │   └─ fitted at model training time                              │ │
│ │   └─ transforms title + description into 100-D sparse vector    │ │
│ │   └─ set via model_loader._load_effort_artifacts()             │ │
│ │      (model_loader.py:164-177)                                  │ │
│ │                                                                  │ │
│ │ Step 2: XGBOOST MODEL PREDICTIONS                               │ │
│ │ ────────────────────────────────────────────────────────────   │ │
│ │   Features → pd.DataFrame([feat_dict])                          │ │
│ │   └─ Line 269 (impact_predictor.py)                             │ │
│ │                                                                  │ │
│ │   xgb.DMatrix(df) → quantile regression                         │ │
│ │   └─ Line 270                                                   │ │
│ │                                                                  │ │
│ │   Three models (loaded at startup):                             │ │
│ │   ┌─ self.models['effort_lower'].predict(dmat)  Line 272       │ │
│ │   │  └─ Lower bound (25th percentile) confidence interval       │ │
│ │   │  └─ Loaded from effort_model_lower.json                     │ │
│ │   │                                                              │ │
│ │   ├─ self.models['effort_median'].predict(dmat) Line 273       │ │
│ │   │  └─ Median estimate (50th percentile)                       │ │
│ │   │  └─ Loaded from effort_model_median.json                    │ │
│ │   │                                                              │ │
│ │   └─ self.models['effort_upper'].predict(dmat)  Line 274       │ │
│ │      └─ Upper bound (75th percentile) confidence interval       │ │
│ │      └─ Loaded from effort_model_upper.json                     │ │
│ │                                                                  │ │
│ │ Step 3: POST-PROCESSING                                         │ │
│ │ ────────────────────────────────────────────────────────────   │ │
│ │   Output: hours_lower, hours_median, hours_upper (float)        │ │
│ │   └─ Convert to hours by XGBoost (model trained on hours)       │ │
│ │   └─ Lines 276-277: ensure lower ≤ median ≤ upper              │ │
│ │                                                                  │ │
│ │   Compare against sprint capacity:                              │ │
│ │   └─ hours_remaining = days_remaining × focus_hours_per_day     │ │
│ │   └─ Lines 279-280                                              │ │
│ │   └─ Lines 282-287: determine status (safe/warning/critical)    │ │
│ │                                                                  │ │
│ │   Return dict:                                                   │ │
│ │   └─ hours_lower, hours_median, hours_upper                     │ │
│ │   └─ hours_remaining                                            │ │
│ │   └─ status (safe / warning / critical)                         │ │
│ │   └─ status_label, explanation                                  │ │
│ │   └─ Lines 289-297                                              │ │
│ │                                                                  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│ [SCHEDULE, QUALITY, PRODUCTIVITY predictions follow same pattern]    │
│                                                                       │
│ Step 4: DISPLAY METRICS GENERATION                                   │
│ ────────────────────────────────────────────────────────────────     │
│   generate_display_metrics(eff, sched, prod, qual, sprint_ctx)       │
│   [impact_predictor.py:59-152]                                       │
│                                                                       │
│   Converts raw ML outputs into human-readable cards:                 │
│   ┌─ Effort: "XXh / YYh Remaining" + "Fits in Sprint" label         │
│   ├─ Schedule: "X% Probability of Spillover" + "On Track" label     │
│   ├─ Productivity: "-X% Drop" + "Minimal Impact" label              │
│   └─ Quality: "X% Defect Risk" + "Standard Risk" label              │
│                                                                       │
│ Step 5: RETURN JSON                                                  │
│ ────────────────────────────────────────────────────────────────     │
│   return {                                                            │
│     'effort': {...},                                                 │
│     'schedule_risk': {...},                                          │
│     'quality_risk': {...},                                           │
│     'productivity': {...},                                           │
│     'summary': {...},                                                │
│     'display': {...},      ← EFFORT CARD GOES HERE                  │
│     'features': {...},                                               │
│     'model_confidence': 'HIGH' / 'LOW',                              │
│     'using_heuristic': False                                         │
│   }                                                                   │
│                                                                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP 200 JSON
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND (React/Next.js)                                             │
│                                                                       │
│ 1. Receives JSON response                                            │
│ 2. Extracts display.effort object                                    │
│ 3. Renders Impact Card Component                                     │
│                                                                       │
│    ┌──────────────────────────────────────────────┐                 │
│    │ EFFORT IMPACT CARD                           │                 │
│    │ ────────────────────────────────────────────│                 │
│    │                                              │                 │
│    │ 🎯 Label: "Fits in Sprint"  ← status_label  │                 │
│    │                                              │                 │
│    │ Value: "24h / 84h Remaining"                 │                 │
│    │        └─ median estimate / capacity         │                 │
│    │                                              │                 │
│    │ Status: ✓ SAFE (green background)            │                 │
│    │         └─ status (safe/warning/critical)    │                 │
│    │                                              │                 │
│    │ Sub-text: "Needs 24h with 84h remaining...  │                 │
│    │           Fits comfortably."                 │                 │
│    │           └─ sub_text explanation            │                 │
│    │                                              │                 │
│    │ [Confidence] Model: HIGH                     │                 │
│    │              └─ model_confidence             │                 │
│    │                                              │                 │
│    └──────────────────────────────────────────────┘                 │
│                                                                       │
│ 4. User sees confidence interval info (if visible)                   │
│    Hours: 18h - 30h (lower to upper bounds)                         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Code Flow with Line Numbers

### 1️⃣ **MODEL LOADING AT STARTUP** (Happens Once)

**File: `model_loader.py`**

```python
class ModelLoader:
    def load_all_models(self) -> bool:
        # Line 31-32: Check if ml_models/ directory exists
        if not self.models_dir.exists():
            return False
        
        # Line 34-35: Load effort models (3 variants)
        success += self._load_effort_models()
        
    def _load_effort_models(self) -> int:
        # Line 73-83: Load 3 XGBoost Booster models
        for variant in ['lower', 'median', 'upper']:
            path = self.models_dir / f'effort_model_{variant}.json'
            m = xgb.Booster()
            m.load_model(str(path))  # Load from JSON
            self.models[f'effort_{variant}'] = m
            
    def _load_effort_artifacts(self):
        # Line 170-177: Load supporting artifacts
        path = self.models_dir / 'effort_artifacts.pkl'
        art = _joblib_load(path)
        self.artifacts['effort_tfidf']   = art['tfidf']      # TF-IDF vectorizer
        self.artifacts['effort_le_type'] = art['le_type']    # LabelEncoder for types
        
        # Inject into feature_engineering module
        from feature_engineering import set_tfidf_vectorizer, set_effort_le_type
        set_tfidf_vectorizer(art['tfidf'])
        set_effort_le_type(art['le_type'])
```

**Result:** Models stored in `model_loader.models` dictionary, globally accessible.

---

### 2️⃣ **FRONTEND CALLS API** (User Submits Requirement)

**Example Request:**
```json
{
  "title": "Implement distributed caching layer with Redis",
  "description": "Add Redis integration for API response caching. Must support TTL, invalidation patterns, and metrics. Integrate with Prometheus for monitoring.",
  "story_points": 8,
  "type": "Story",
  "priority": "High"
}
```

---

### 3️⃣ **BACKEND RECEIVES & VALIDATES**

**File: `impact_routes.py` (lines 91-150)**

```python
@router.post("/impacts")
async def predict_impacts(req: PredictImpactRequest) -> dict:
    # Line 100: Validate input (gibberish detection, required fields)
    validation_error = validate_requirement_input(req.title, req.description)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)
    
    # Line 110-120: Build sprint context from database
    sprint = await db.get_sprint(space_id, sprint_id)
    sprint_context = {
        'start_date': sprint['start_date'],
        'end_date': sprint['end_date'],
        'team_velocity_14d': calculate_velocity(space),
        'sprint_load_7d': sum_story_points_of_items(sprint, days=7),
        'days_remaining': (sprint['end_date'] - datetime.now()).days,
        'assignee_count': len(sprint['assignees']),
        'focus_hours_per_day': space['focus_hours_per_day'],  # Default 6h
    }
    
    # Line 130: Call ImpactPredictor
    item_data = {
        'title': req.title,
        'description': req.description,
        'story_points': req.story_points,
        'type': req.type,
        'priority': req.priority,
    }
    
    predictor = ImpactPredictor()
    result = predictor.predict_all_impacts(
        item_data=item_data,
        sprint_context=sprint_context,
        focus_hours_per_day=space['focus_hours_per_day']
    )
    
    # Line 145: Return JSON
    return result
```

---

### 4️⃣ **FEATURE ENGINEERING**

**File: `feature_engineering.py` (lines 163-201)**

```python
def build_effort_features(item_data: dict, sprint_context: dict) -> dict:
    # Line 169-172: Extract input fields
    title        = item_data.get('title', '')
    description  = item_data.get('description', '')
    story_points = float(item_data.get('story_points', 5))
    ui_type      = item_data.get('type', 'Task')
    
    # Line 174-176: Extract sprint context
    sprint_load    = float(sprint_context.get('sprint_load_7d', 0))
    team_velocity  = float(sprint_context.get('team_velocity_14d', 30))
    days_remaining = float(sprint_context.get('days_remaining', 14))
    
    # Line 178-179: Compute pressure_index
    pressure_index = story_points / max(1.0, days_remaining)
    # Example: 8 SP / 7 days = 1.14 (high pressure)
    
    # Line 180-181: Count links from description
    total_links = float(
        description.lower().count('http') + len(description.split(',')) // 3
    )
    # Example: 2 URLs + some commas = 3 links
    
    # Line 183-184: Encode type to numeric
    type_label = _ui_type_to_effort(ui_type)  # 'Story' → 'Story'
    type_code = float(_safe_le_transform(_effort_le_type_ref, type_label))
    # Example: LabelEncoder.transform(['Story']) → [1.0]
    
    # Line 186: TF-IDF vectorization (THE CRITICAL STEP)
    tfidf = _get_tfidf_vector(f"{title} {description}", n_components=100)
    # Line 145-154: _get_tfidf_vector() calls the pre-fitted vectorizer
    #   "Implement distributed caching layer with Redis. Add Redis integration
    #    for API response caching. Must support TTL, invalidation patterns,
    #    and metrics. Integrate with Prometheus for monitoring."
    #   ↓
    #   [0.15, 0.08, 0.12, 0.0, ..., 0.09]  ← 100-D sparse vector
    
    # Line 188-196: Build feature dictionary
    features = {
        'sprint_load_7d':    23.0,
        'team_velocity_14d': 40.0,
        'pressure_index':    1.14,
        'total_links':       3.0,
        'Type_Code':         1.0,
        'txt_0':  0.15,
        'txt_1':  0.08,
        'txt_2':  0.12,
        # ... txt_3 through txt_99
    }
    
    return features  # 105 keys total
```

**Feature Mapping to Training:**
```
Training data had these exact 105 features:
- sprint_load_7d (numeric, mean=23.4)
- team_velocity_14d (numeric, mean=38.2)
- pressure_index (numeric, mean=0.8)
- total_links (numeric, mean=2.1)
- Type_Code (int, mapped from LabelEncoder['Story', 'Bug', ...])
- txt_0 to txt_99 (TF-IDF sparse vectors)

The TF-IDF vectorizer was fitted on thousands of historical
requirement titles+descriptions and learned which terms matter.
```

---

### 5️⃣ **EFFORT MODEL PREDICTION**

**File: `impact_predictor.py` (lines 263-302)**

```python
def _predict_effort(
    self, item_data: dict, sprint_context: dict,
    focus_hours_per_day: float = 6.0,
) -> dict:
    try:
        # Line 268: Call feature engineering
        feat_dict = build_effort_features(item_data, sprint_context)
        
        # Line 269: Convert to pandas DataFrame
        df = pd.DataFrame([feat_dict])
        # ┌─────────────────────────────────────┐
        # │ sprint_load_7d │ team_velocity_14d │ ... │ txt_99 │
        # │ 23.0           │ 40.0              │     │ 0.05   │
        # └─────────────────────────────────────┘
        
        # Line 270: Convert to XGBoost DMatrix
        dmat = xgb.DMatrix(df)
        
        # Lines 272-274: RUN 3 MODELS
        lower  = float(self.models['effort_lower'].predict(dmat)[0])
        # Returns single float: ~16.3 hours
        
        median = float(self.models['effort_median'].predict(dmat)[0])
        # Returns single float: ~24.1 hours
        
        upper  = float(self.models['effort_upper'].predict(dmat)[0])
        # Returns single float: ~31.8 hours
        
        # Lines 277: Ensure ordering
        lower, upper = min(lower, median), max(upper, median)
        
        # Lines 279-280: Calculate sprint capacity
        days_remaining  = max(1, sprint_context.get('days_remaining', 14))
        hours_remaining = days_remaining * focus_hours_per_day
        # Example: 7 days * 6h/day = 42 hours remaining
        
        # Lines 282-287: Determine status
        if median > hours_remaining:
            status, label = 'critical', 'Sprint Overload'
        elif median > hours_remaining * 0.8:
            status, label = 'warning', 'Tight Fit'
        else:
            status, label = 'safe', 'Fits in Sprint'
        # Example: 24.1h < 42h → 'safe', 'Fits in Sprint'
        
        # Lines 289-297: Return prediction
        return {
            'hours_lower':     16.3,
            'hours_median':    24.1,
            'hours_upper':     31.8,
            'hours_remaining': 42.0,
            'status':          'safe',
            'status_label':    'Fits in Sprint',
            'explanation':     'Predicted 24.1h vs 42.0h remaining.',
        }
        
    except Exception as e:
        # Line 301-302: Fallback to heuristic if ML fails
        return self._heuristic_effort(item_data, sprint_context, focus_hours_per_day)
```

**What XGBoost Does Internally:**
```
Feature vector:
[23.0, 40.0, 1.14, 3.0, 1.0, 0.15, 0.08, ..., 0.05]
     ↓
Decision trees traverse splits:
- if sprint_load_7d ≤ 20:  → go left
- else:  → go right
- if txt_5 ≤ 0.10:  → go left
- ...
     ↓
Leaf node outputs:
- Lower quantile (q=0.25) tree: prediction=16.3h
- Median quantile (q=0.50) tree: prediction=24.1h
- Upper quantile (q=0.75) tree: prediction=31.8h
     ↓
Returns all 3 values (confidence interval)
```

---

### 6️⃣ **DISPLAY METRICS GENERATION**

**File: `impact_predictor.py` (lines 59-152)**

```python
def generate_display_metrics(
    eff: dict, sched: dict, prod: dict, qual: dict,
    sprint_context: dict,
    focus_hours_per_day: float = 6.0,
) -> dict:
    # Lines 68-81: Process effort output
    predicted_hours = eff.get('hours_median', 0.0)  # 24.1
    days_remaining  = max(1, sprint_context.get('days_remaining', 14))  # 7
    hours_remaining = days_remaining * focus_hours_per_day  # 42.0
    
    if predicted_hours > hours_remaining:
        eff_status, eff_label = 'critical', 'Sprint Overload'
    elif predicted_hours > hours_remaining * 0.8:
        eff_status, eff_label = 'warning', 'Tight Fit'
    else:
        eff_status, eff_label = 'safe', 'Fits in Sprint'
    # 24.1 < 42, so: status='safe', label='Fits in Sprint'
    
    eff_sub = (f"Needs {predicted_hours:.0f}h with {hours_remaining:.0f}h remaining "
               f"({focus_hours_per_day:.0f}h/day). Fits comfortably.")
    # "Needs 24h with 42h remaining (6h/day). Fits comfortably."
    
    # Lines 127-132: Build effort card
    return {
        'effort': {
            'value':    f"{predicted_hours:.0f}h / {hours_remaining:.0f}h Remaining",
            # "24h / 42h Remaining"
            'label':    eff_label,
            # "Fits in Sprint"
            'status':   eff_status,
            # "safe"
            'sub_text': eff_sub,
            # "Needs 24h with 42h remaining (6h/day). Fits comfortably."
        },
        # ... schedule, productivity, quality cards similarly ...
    }
```

---

### 7️⃣ **RETURN COMPLETE RESPONSE**

**File: `impact_predictor.py` (lines 230-240)**

```python
return {
    'effort': {
        'value': '24h / 42h Remaining',
        'label': 'Fits in Sprint',
        'status': 'safe',
        'sub_text': 'Needs 24h with 42h remaining (6h/day). Fits comfortably.',
    },
    'schedule_risk': { ... },
    'quality_risk': { ... },
    'productivity': { ... },
    'summary': { ... },
    'display': {
        'effort': {...},
        'schedule': {...},
        'productivity': {...},
        'quality': {...},
    },
    'features': { ... },
    'model_confidence': 'HIGH',
    'using_heuristic': False,
}
```

---

### 8️⃣ **FRONTEND RENDERS**

**Frontend Component (Pseudo-code):**

```jsx
function RequirementImpactCard({ prediction }) {
  const effortCard = prediction.display.effort;
  
  return (
    <div className={`status-${effortCard.status}`}>
      {/* effort.status = 'safe' → green background */}
      
      <h3>{effortCard.label}</h3>
      {/* "Fits in Sprint" */}
      
      <p className="value">{effortCard.value}</p>
      {/* "24h / 42h Remaining" */}
      
      <p className="sub-text">{effortCard.sub_text}</p>
      {/* "Needs 24h with 42h remaining (6h/day). Fits comfortably." */}
      
      <Badge confidence={prediction.model_confidence}>
        {/* Model: HIGH (or LOW if using_heuristic=true) */}
      </Badge>
    </div>
  );
}
```

**Rendered Output:**
```
┌────────────────────────────────────────┐
│ ✓ FITS IN SPRINT                       │
│                                        │
│ 24h / 42h Remaining                    │
│                                        │
│ Needs 24h with 42h remaining (6h/day). │
│ Fits comfortably.                      │
│                                        │
│ Confidence: HIGH                       │
└────────────────────────────────────────┘
```

---

## Error Handling & Fallback

**If ML prediction fails:**

1. **Catch exception** (impact_predictor.py:298-302)
   ```python
   except Exception as e:
       print(f"\n[EFFORT PREDICTION ERROR] {type(e).__name__}: {e}")
       return self._heuristic_effort(item_data, sprint_context, focus_hours_per_day)
   ```

2. **Use heuristic estimate:**
   ```python
   def _heuristic_effort(self, item_data, sprint_context, focus_hours_per_day):
       story_points = float(item_data.get('story_points', 5))
       hours_per_sp = 6.0  # Fallback assumption
       median = story_points * hours_per_sp
       return {
           'hours_lower': median * 0.8,
           'hours_median': median,
           'hours_upper': median * 1.2,
           'status': 'safe' if median < hours_remaining else 'critical',
           'error_flag': 'ML_FAILED_USING_HEURISTIC',
       }
   ```

3. **Frontend still gets valid response**, but with `model_confidence='LOW'` and `using_heuristic=True`.

---

## Key Technical Decisions Explained

### Why 3 Quantile Models?

The effort model uses **quantile regression** (3 variants: lower, median, upper) instead of a single point prediction because:

1. **Uncertainty Quantification**: A single estimate (e.g., "24h") hides uncertainty. The range [16h, 24h, 32h] shows the model's confidence.
2. **User Decision-Making**: The team can use the upper bound (32h) for conservative capacity planning vs. the median (24h) for optimistic estimates.
3. **Built-in Confidence Interval**: The spread (upper - lower = 16h) indicates model uncertainty. Wide spreads trigger lower confidence scores.

### Why TF-IDF + Numeric Features?

The 105-feature vector mixes:
- **5 numeric features** (sprint_load, velocity, pressure, links, type_code) capture scheduling context
- **100 TF-IDF features** capture what the requirement is actually about (e.g., "Redis integration" vs. "UI styling")

The model learned: "Requirements mentioning 'distributed', 'caching', 'integration' tend to take longer." TF-IDF captures this semantic signal.

### Why Label Encoding for Type?

The model never sees the string `"Story"` or `"Bug"`. Instead:

```python
LabelEncoder fits on: ['Bug', 'Story', 'Technical task', ...]
Transform: 'Story' → 1.0
```

This lets XGBoost treat type as an ordinal feature (though type isn't truly ordinal, it's just a category). The model learns: "Bugs and Stories behave differently in terms of effort."

---

## Code Checklist for Viva

**Q: "Walk us through the effort prediction flow."**

A:
1. ✅ **Startup (once)**: `model_loader.load_all_models()` loads 3 XGBoost models + TF-IDF vectorizer
2. ✅ **API receives** requirement JSON from frontend
3. ✅ **Input validation** checks for gibberish
4. ✅ **Feature engineering** builds 105-D feature vector
   - TF-IDF transforms title+description
   - Numeric features encode sprint state
   - Type/priority are label-encoded
5. ✅ **XGBoost prediction** runs on DMatrix → 3 outputs (lower, median, upper)
6. ✅ **Display metrics** convert to user-friendly card (value, label, status, explanation)
7. ✅ **JSON response** sent to frontend with confidence score
8. ✅ **Frontend renders** impact card with color-coding

**Q: "What happens if the model fails?"**

A: The try-except catches the error and falls back to a heuristic: `hours = story_points × 6h/SP`. The response still works, but includes `error_flag='ML_FAILED_USING_HEURISTIC'` and sets confidence to LOW.

**Q: "Why load models at startup instead of every request?"**

A: **Performance**: Loading 3 XGBoost models + artifacts takes ~2-3 seconds. Doing this per request would make each prediction take 2-3 seconds. At startup, we pay the cost once, then predictions are instant (~50ms each).

**Q: "How does the TF-IDF vectorizer know about your requirements?"**

A: It was fitted during training on historical Jira tickets. The vectorizer learned which terms are common, and the XGBoost models learned how TF-IDF vectors correlate with actual effort. New requirements are transformed using the same fitted vectorizer, so the model can apply learned patterns.
