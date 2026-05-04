# Services Folder - Complete Explanation

## Overview
The `services/sprint_impact_service/` folder contains the complete ML-powered Agile project management system. It includes database management, ML model loading, feature engineering, impact prediction, decision-making, and user-facing explanations.

---

## 📊 File Structure & Responsibilities

### **1. DATABASE LAYER**

#### `database.py`
**Purpose**: Async MongoDB database management and helper functions for sprints, backlog items, and analytics.

**Key Responsibilities**:
- **Async MongoDB connection**: `connect_db()`, `close_db()` using `motor` (async driver)
- **Helper functions** for formatting sprint and backlog data
- **Sprint operations**: fetch sprints by ID, get items in sprint
- **Capacity calculations**: 
  - `calculate_sprint_capacity()` - estimates team capacity based on historical velocity
  - `check_sprint_capacity_status()` - monitors current sprint load vs team capacity (HEALTHY/CAUTION/CRITICAL)
- **Analytics helpers**:
  - `get_space_velocity_history()` - historical team velocity (completed SP per sprint)
  - `calculate_burndown_data()` - ideal vs actual burndown chart
  - `calculate_burnup_data()` - burnup chart data
  - `get_last_completed_sprint()` - real sprint data for calculating actual focus hours

**Why This Matters**: All features depend on real sprint data. The database layer bridges MongoDB queries into Python-friendly dicts for ML models.

---

### **2. DATA MODELS**

#### `models.py`
**Purpose**: Pydantic BaseModel definitions for API request/response validation.

**Key Models**:
- **Space** - represents a project/team with:
  - `focus_hours_per_day` (default 6.0)
  - `utilization_factor` (default 0.75 = 75% of focus hours actually used)
  - `risk_appetite` (Lenient/Standard/Strict)
  
- **Sprint** - with `assignee_count`, `team_capacity_sp`, `historical_pace`

- **BacklogItem** - with `story_points` (3-15), `priority`, `type`, `status`

- **Enums**: BacklogType, Priority, Status, SprintStatus, DurationType, RiskAppetite

**Why This Matters**: Ensures type safety and validates all incoming API data before ML models process it.

---

### **3. ML MODEL INFRASTRUCTURE**

#### `model_loader.py`
**Purpose**: Loads all 5 ML models and 4+ artifact files at startup.

**Models Loaded**:
1. **Effort Model** (3 quantile boosters):
   - `effort_model_lower.json` - pessimistic estimate
   - `effort_model_median.json` - best estimate
   - `effort_model_upper.json` - optimistic estimate
   - 105 features (5 numeric + 100 TF-IDF)

2. **Schedule Risk Model**:
   - `schedule_risk_model.pkl` - XGBClassifier (4 classes: Low/Medium/High/Critical)
   - 9 features

3. **Quality Risk Model**:
   - `tabnet_quality_model.zip` - TabNetClassifier (binary: defect yes/no)
   - 6 features
   - Special handling for PyTorch weights

4. **Productivity Model** (ensemble):
   - `model_productivity_xgb.json` - XGBoost regression
   - `model_productivity_nn.pth` - PyTorch MLP (9→64→32→1)
   - Uses both, averages outputs
   - 9 features

**Artifacts Loaded**:
- `effort_artifacts.pkl` → TF-IDF vectorizer + type encoder for effort model
- `risk_artifacts.pkl` → imputer + type/priority encoders for schedule risk
- `productivity_artifacts.pkl` → scaler + type/priority encoders for productivity
- `le_prio_quality.pkl` → priority encoder for quality model
- `model_params.json` → TabNet architecture parameters
- `tfidf_vectorizer.pkl` → standalone TF-IDF for story point suggestion & goal alignment

**Key Method**: `load_all_models()` - called at app startup via `main.py` lifespan handler

**Why This Matters**: Models must be loaded before ANY prediction request. Graceful fallback to heuristics if any model fails.

---

### **4. FEATURE ENGINEERING**

#### `feature_engineering.py`
**Purpose**: Transforms raw requirement/sprint data into ML-ready feature vectors.

**Key Functions**:

1. **build_effort_features()** - 105 features:
   - 5 numeric: sprint_load_7d, team_velocity_14d, pressure_index, total_links, type_code
   - 100 TF-IDF from title+description

2. **build_schedule_risk_features()** - 9 features:
   - Story points, links, comments, author load
   - Density ratios, pressure index
   - Type/priority codes
   - **Key fix**: Replaced hardcoded author_load (4519) with contextual value based on sprint load
   - **Fallback**: Min-max normalization when scaler missing

3. **build_quality_features()** - 6 features:
   - Story points, pressure, days remaining, priority code, team velocity, sprint progress

4. **build_productivity_features()** - 9 features (log-space):
   - Story points, log(SP/days), log(days), team_velocity_14d
   - sprint_load_7d, normalized pressure
   - sprint_progress, type code, priority code

**Label Mapping**:
- Maps UI labels (Low/Medium/High/Critical) → training labels (Minor/Major/Critical/Blocker)
- Different label sets per model (quality model uses High/Highest/Low/Lowest/Medium)

**Why This Matters**: Features must exactly match training data. Any mismatch causes model errors. Handles missing data with imputers and encoders loaded from artifacts.

---

### **5. IMPACT PREDICTION**

#### `impact_predictor.py`
**Purpose**: Runs all 4 ML models to predict effort, schedule risk, quality risk, and productivity impact.

**Class: ImpactPredictor**

**Main Method: predict_all_impacts()**:
- Calls `_predict_effort()` → (lower, median, upper hours)
- Calls `_predict_schedule_risk()` → probability of spillover (%)
- Calls `_predict_quality_risk()` → defect probability (%)
- Calls `_predict_productivity()` → velocity drag (%)
- **Fallback to heuristics** if any model fails
- Returns confidence flag (`HIGH` if all models succeed, `LOW` if fallback used)

**Prediction Details**:

1. **Effort** (XGBoost 3-quantile):
   - Output: hours_lower/median/upper
   - Compares median to hours_remaining to determine status (critical/warning/safe)

2. **Schedule Risk** (XGBClassifier):
   - Outputs class probabilities [P(Low), P(Medium), P(High), P(Critical)]
   - **Key insight**: Raw probabilities always sum to 0% for High/Critical (model rarely predicts these)
   - **Solution**: Uses weighted class midpoints (Low→5%, Medium→30%, High→65%, Critical→90%)
   - Maps midpoints back to [0-100%] spillover probability

3. **Quality Risk** (TabNet binary):
   - Outputs P(defect). Capped to [0-99%]
   - Determines QA effort needed (double review if >60%)

4. **Productivity** (XGBoost + PyTorch ensemble):
   - Both models output in log-space (log of velocity drag %)
   - **Saturation guard**: If output > 4.5, suppress percentage, return "VOLATILE"
   - Averaged for final prediction
   - Decode from log-space: exp(output) - 1

**Context Enrichment**:
- Calculates days_remaining, days_since_sprint_start, sprint_progress from sprint dates

**Why This Matters**: All 4 models must agree for ADD decision. Single high-risk prediction can DEFER/SPLIT even if capacity available.

---

### **6. DECISION ENGINE**

#### `decision_engine.py`
**Purpose**: Unified rule engine for sprint planning decisions (ADD/DEFER/SPLIT/SWAP/ABSORB/SWARM).

**Entry Point: calculate_agile_recommendation()**
```python
def calculate_agile_recommendation(
    alignment_state: str,           # CRITICAL_BLOCKER, STRONGLY_ALIGNED, PARTIALLY_ALIGNED, etc.
    effort_sp: int | float,          # Story points
    free_capacity: int | float,      # Available capacity
    priority: str,                   # Low, Medium, High, Critical
    risk_level: str,                 # LOW, MEDIUM, HIGH
) -> DecisionResult
```

**Rules** (first match wins):
1. **Emergency** → ADD if fits, SWAP if not (CRITICAL_BLOCKER)
2. **Scope creep** → DEFER (UNALIGNED)
3. **High risk + low priority** → DEFER (ML now blocks ADD)
4. **High risk + high priority + aligned** → SPLIT (new: forces ML predictions to matter)
5. **Aligned but >8 SP** → SPLIT (elephant protocol)
6. **Partial/weak + exceeds capacity** → SPLIT
7. **Strongly aligned + exceeds capacity** → SWAP (trade lower-priority items)
8. **Perfect fit** → ADD (aligned + fits + acceptable risk)
9. **Catch-all** → DEFER

**Key Changes from Old System**:
- ML risk is checked BEFORE capacity (was after)
- HIGH risk now forces SPLIT/DEFER regardless of capacity
- High risk + high priority = SPLIT not ADD

**Result**: DecisionResult class with action, rule_triggered, reasoning, extra metadata

**Why This Matters**: Single decision engine replaces 2 conflicting engines. Ensures ML predictions actually influence decisions.

---

### **7. SPRINT GOAL ALIGNMENT**

#### `sprint_goal_alignment.py`
**Purpose**: Evaluates if a requirement aligns with sprint goal using 4-layer analysis.

**4-Layer Analysis**:

**Layer 1: Critical Blocker Detection**
- Checks priority (Critical/Blocker only)
- Scans for keywords: "crash", "down", "outage", "production", "security breach", etc.
- If found → immediately return `CRITICAL_BLOCKER` alignment

**Layer 2: Semantic Similarity**
- Uses TF-IDF cosine similarity (via `tfidf_registry.py`)
- Fallback to Jaccard token overlap if TF-IDF unavailable
- Thresholds:
  - ≥0.50 cosine → HIGHLY_RELEVANT
  - ≥0.25 cosine → TANGENTIAL
  - <0.25 cosine → UNRELATED

**Layer 3: Metadata Traceability**
- Compares epic names (exact match?)
- Overlaps components (>66% → high, >33% → medium, >0% → low, 0% → none)

**Layer 4: Integrated Recommendation**
Combines all layers:
- **CRITICAL_BLOCKER** → ACCEPT (override all checks)
- **HIGHLY_RELEVANT** → ACCEPT
- **TANGENTIAL + epic match or high component overlap** → CONSIDER
- **TANGENTIAL + no epic/components** → EVALUATE
- **UNRELATED** → DEFER

**Output**:
```python
{
    "final_recommendation": "ACCEPT",  # or CONSIDER, EVALUATE, DEFER
    "recommendation_reason": "...",
    "next_steps": "...",
    "alignment_details": {
        "critical_blocker": False,
        "semantic_category": "HIGHLY_RELEVANT",
        "epic_aligned": True,
        "component_overlap": "high"
    }
}
```

**Why This Matters**: Feeds into decision engine's alignment_state parameter. Prevents unrelated work diluting sprint focus.

---

### **8. INPUT VALIDATION**

#### `input_validation.py`
**Purpose**: Detects gibberish/junk text before ML processing.

**Heuristics**:
1. **Length check** - minimum 5 characters
2. **Keyboard smash** - long strings with no spaces (excluding paths/URLs)
3. **Vowel ratio** - <10% vowels in 12+ char text = gibberish
4. **Consecutive consonants** - >10 in a row = likely gibberish
5. **Character repetition** - >50% same character = junk
6. **Valid English words** - at least one meaningful word or tech term

**Smart Features**:
- Recognizes CamelCase (XGBClassifier) and tech patterns (OAuth2)
- Excludes these from vowel/consonant checks
- Allows technical jargon that would fail linguistic tests

**Function**: `validate_requirement(title, description)` → (is_valid, error_message)

**Why This Matters**: Prevents ML models from wasting inference on garbage input. Provides user-friendly error messages.

---

### **9. STORY POINT SUGGESTION**

#### `sp_suggester.py`
**Purpose**: Recommends story points for new requirements using similarity matching + complexity heuristics.

**Approach**:
1. **Historical similarity** - finds similar items from backlog using cosine similarity
2. **Complexity heuristics**:
   - Title complexity: "add", "create", "fix" (simple) vs "redesign", "rewrite" (complex)
   - Description complexity: length, dependency keywords, edge cases
   - Combines both: 0.0-1.0 score

3. **Fibonacci constraint** - enforces valid Fibonacci numbers (1, 2, 3, 5, 8, 13, 21)

**Algorithm**:
- If historical match found (>30% similarity): adjust historical SP by complexity ratio
- If no match: estimate SP from complexity alone
- Confidence score: 0.2-0.85 (higher if good historical match)

**Complexity → SP Mapping**:
```
0.0-0.2  →  1 SP   (trivial)
0.2-0.35 →  2 SP   (very simple)
0.35-0.5 →  3 SP   (simple)
0.5-0.65 →  5 SP   (moderate)
0.65-0.8 →  8 SP   (complex)
0.8-0.95 → 13 SP   (very complex)
0.95-1.0 → 21 SP   (extremely complex)
```

**Output**:
```python
{
    "suggested_sp": 5,
    "confidence": 0.75,
    "reasoning": "Similar to X (8 SP), but simpler (~60% complexity)",
    "historical_match": {
        "title": "...",
        "story_points": 8,
        "similarity": 0.65
    }
}
```

**Why This Matters**: Users don't blindly guess SP. System learns from completed items and suggests based on similar work.

---

### **10. EXPLANATION GENERATOR**

#### `explanation_generator.py`
**Purpose**: Converts raw decision engine output into polished, user-facing explanations.

**Supported Actions**: ADD, SWAP, DEFER, SPLIT

**Per-Action Explanations**:

1. **ADD** (`_explain_add()`):
   - Summary: "✅ Safe to Add to Sprint"
   - Details: capacity available, risks low
   - Icon: ✅

2. **SWAP** (`_explain_swap()`):
   - Summary: "🔄 Swap with '{target_title}'"
   - Details: which item to remove, why trade-off justified
   - Icon: 🔄

3. **DEFER** (`_explain_defer()`):
   - Summary: "⏸ Defer to Next Sprint"
   - Details: identifies primary risk (schedule/quality/velocity)
   - Icon: ⏸

4. **SPLIT** (`_explain_split()`) - Elephant Protocol:
   - Splits large items (≥8 SP) into:
     - Analysis slice (30%, this sprint) - spike, research, acceptance criteria
     - Implementation slice (70%, next sprint) - full development
   - Icon: ✂️

**Result Type**:
```python
{
    "short_title": "✅ Safe to Add to Sprint",  # ≤60 chars
    "detailed_explanation": "...",               # full paragraph
    "confidence_color": "green",                 # or "yellow", "red"
    "action_verb": "Add to Sprint",              # CTA button text
    "icon": "✅",                                # emoji
    "risk_summary": "Schedule: 15% · Quality: 20% · Velocity: -5%"
}
```

**Confidence Color Logic**:
- **Red** (critical): schedule_risk > 55% OR quality_risk > 60% OR velocity < -30%
- **Yellow** (warning): schedule_risk > 30% OR quality_risk > 30% OR velocity < -10%
- **Green** (safe): everything else

**Why This Matters**: User-friendly. Shows reasoning not just action. Educates team on why decisions made.

---

### **11. TF-IDF REGISTRY**

#### `tfidf_registry.py`
**Purpose**: Shared singleton registry for standalone TF-IDF vectorizer.

**Used By**:
- `ai_routes.py` - story point prediction
- `sprint_goal_alignment.py` - semantic similarity calculation

**Key Functions**:
- `set_standalone_tfidf(vec)` - called by model_loader at startup
- `get_standalone_tfidf()` - retrieve vectorizer
- `tfidf_transform(texts)` - transform list of texts → dense array
- `tfidf_cosine_similarity(text_a, text_b)` - cosine similarity in [0, 1]
- `is_tfidf_available()` - check if loaded

**Error Handling**:
- Returns -1.0 from cosine_similarity if vectorizer unavailable
- Caller can fall back to Jaccard similarity

**Why This Matters**: Decouples TF-IDF management from feature engineering. Allows goal alignment and SP suggestion to use same vectorizer without duplication.

---

### **12. APPLICATION SETUP**

#### `main.py`
**Purpose**: FastAPI app initialization and lifespan management.

**Lifespan Hooks**:
- **Startup**: `connect_db()` → `model_loader.load_all_models()`
- **Shutdown**: `close_db()`

**Middleware**: CORS for localhost:5173 (frontend)

**Routes Registered**:
- `/api/spaces/` - space management
- `/api/sprints/` - sprint CRUD
- `/api/backlog/` - item management
- `/api/analytics/` - velocity, burndown, burnup
- `/api/ai/` - story point suggestion, decision engine
- `/api/impact/` - impact predictions

**Health Check**: `/health` endpoint returns model load status

**Why This Matters**: Entry point for entire system. Ensures models loaded before any request arrives.

---

### **13. DATA SEEDING**

#### `seed_fintrack.py` & `seed_current_dataset.py`
**Purpose**: Populate MongoDB with test/demo data.

**Includes**:
- 1 Space (project setup)
- Multiple Sprints (5+ historical + 1 active)
- Backlog items with realistic story points, priorities, types
- Varied item statuses (Done, In Progress, To Do)

**Why This Matters**: Testing and demos need realistic data. Models trained on similar patterns should work well.

---

## 🔄 Data Flow Example

**User adds requirement to active sprint:**

1. **Input Validation** → `input_validation.py` validates title/description
2. **Story Point Suggestion** → `sp_suggester.py` suggests SP (using TF-IDF from `tfidf_registry.py`)
3. **Sprint Goal Alignment** → `sprint_goal_alignment.py` scores alignment (4-layer analysis)
4. **Impact Prediction** → `impact_predictor.py` runs 4 ML models:
   - **Feature Engineering** → `feature_engineering.py` builds feature vectors
   - **Model Loader** artifacts → apply encoders, scalers
   - **Effort, Schedule, Quality, Productivity models** → predictions
5. **Decision Engine** → `decision_engine.py` decides ADD/DEFER/SPLIT/SWAP based on:
   - Alignment state (from goal alignment)
   - Effort (from effort model)
   - Free capacity (from database)
   - Priority + ML risk level
6. **Explanation Generator** → `explanation_generator.py` polishes decision into user-friendly text
7. **Response** → frontend shows decision card with icon, title, detailed reasoning, action button

---

## ⚠️ Critical Design Principles

1. **ML is not decorative** - High risk blocks ADD even if capacity exists
2. **Fallback to heuristics** - If any model fails, use simple formulas (not garbage)
3. **Confidence tracking** - Tell user if we used ML or fallback
4. **Isolation of concerns** - Each file does ONE thing well
5. **Artifact-driven** - No hardcoded label maps; everything from training artifacts
6. **Elastic capacity** - Sprint capacity adjusts based on team velocity + new headcount
7. **Elephant protocol** - Large items (≥8 SP) split to preserve sprint integrity

---

## 🎓 Viva Questions You'll Get

1. **Why 3-quantile effort model?** → Provides confidence intervals (lower/median/upper)
2. **Why weighted class midpoints for schedule risk?** → Raw probabilities always ~0% for High/Critical
3. **Why separate TF-IDF for story points vs effort features?** → Effort TF-IDF trained on specific corpus; standalone used for similarity
4. **Why ensemble (XGBoost + MLP) for productivity?** → Diversity reduces overfitting; average output more robust
5. **Why validate input before ML?** → Prevents garbage in → garbage out; saves inference compute
6. **Why "contextual author load" instead of constant 4519?** → Constant made feature useless; contextual value lets trees split correctly
7. **Why Elephant Protocol?** → Large items have disproportionate risk; splitting preserves commitments

---

This system is **production-grade**, with proper error handling, fallbacks, confidence tracking, and user-friendly explanations. Every file has a clear responsibility; every design decision is justified.
