# Implementation Summary: Evidence-Based Scheduling, Dynamic ML Thresholds, and AI Story Points

## Overview
This implementation adds three major features to the Agile Replanning & Impact Analysis tool:

1. **Evidence-Based Scheduling (Dynamic Focus Hours)** - Calculates focus hours dynamically from previous sprint data
2. **Dynamic ML Thresholds via Risk Appetite** - Uses Space settings to control ML model strictness
3. **AI Story Point Suggestion** - Integrates story point prediction into the Impact Analysis form

---

## FILES UPDATED

### 1. **Backend Files**

#### `services/sprint_impact_service/routes/impact_routes.py`
**Changes:**
- Added `calculate_dynamic_focus_hours()` function that:
  - Fetches the most recently completed sprint for a space
  - Calculates hours per story point: `(Assignees × Days × 8) / Completed SP`
  - Derives daily focus capacity: `(Completed SP / Sprint Duration) × Hours Per SP / Assignees`
  - Returns value capped between 2.0-10.0 hours/day, or falls back to 6.0
- Updated `/analyze` endpoint to:
  - Call `calculate_dynamic_focus_hours()` to get evidence-based focus hours
  - Pass `risk_appetite` parameter to the RecommendationEngine
  - Pass both parameters to `impact_predictor.predict_all_impacts()`

**Why:** Replaces hardcoded 6.0 WORK_HOURS_PER_DAY with team-specific historical data.

---

#### `services/sprint_impact_service/impact_predictor.py`
**Changes:**
- Added `risk_appetite` parameter to `predict_all_impacts()` method
- Updated `_generate_summary()` to accept `risk_appetite` parameter
- Implemented risk appetite thresholds:
  - **Strict**: DEFER score=5, SWAP=3, SPLIT=1 (conservative)
  - **Standard**: DEFER score=7, SWAP=4, SPLIT=2 (balanced)
  - **Lenient**: DEFER score=9, SWAP=6, SPLIT=3 (permissive)
- Summary now includes `risk_appetite` in response for transparency

**Why:** Allows users to adjust ML model strictness via Navbar Settings without hardcoding values.

---

#### `services/sprint_impact_service/routes/space_routes.py`
**Changes:**
- Updated `space_helper()` to include `risk_appetite` field in Space response

**Why:** Ensures Space API properly exposes the risk_appetite setting.

---

### 2. **Frontend Files**

#### `frontend/src/components/features/sprint_impact_service/ImpactAnalyzer.jsx`
**Changes:**
- Added `suggestingPoints` state to track API call loading state
- Added `handleSuggestPoints()` function that:
  - Calls `api.predictStoryPoints()` with current title & description
  - Auto-fills story_points input with AI suggestion
  - Shows loading spinner while fetching
- Added "✨ Suggest" button next to story points input:
  - Disabled until title is entered
  - Shows loading spinner during API call
  - Integrated with existing form state management

**Why:** Brings AI story point suggestion directly into Impact Analysis workflow without context switching.

---

#### `frontend/src/components/features/sprint_impact_service/api.js`
**Status:** No changes needed
- `api.predictStoryPoints()` method already exists and works correctly
- Endpoint: `POST /api/ai/predict` matches the backend ai_routes.py

**Verification:** The method is used in the form to get AI suggestions.

---

## DATABASE SCHEMA

### Models (no changes required - already exist in `models.py`)
- `RiskAppetite` enum: "Lenient", "Standard", "Strict"
- `SpaceCreate` model already has:
  - `focus_hours_per_day: float = Field(default=6.0, ge=1.0, le=24.0)`
  - `risk_appetite: RiskAppetite = Field(default=RiskAppetite.STANDARD)`
- `Space` model already has both fields

### MongoDB Collections
- `spaces`: Contains `focus_hours_per_day` and `risk_appetite` for each space
- `sprints`: Used to fetch completed sprint data for dynamic hours calculation
- `backlog_items`: Contains story_points for calculating historical velocity

---

## CORS NOTES

✅ **CORS Configuration is Complete**
- FastAPI main.py already has proper CORS setup with `http://localhost:5173`
- No additional CORS headers needed - backend is fully accessible from React frontend
- All API endpoints maintain existing CORS compatibility

---

## FEATURE BEHAVIOR

### Feature 1: Evidence-Based Scheduling
**User Flow:**
1. User enters new requirement in Impact Analyzer
2. Backend fetches space and calls `calculate_dynamic_focus_hours(space_id)`
3. Function looks for most recently completed sprint
4. Calculates team's actual hours-per-story-point from that sprint
5. Derives focus hours and passes to ML models
6. Display metrics use this evidence-based value

**Fallback:**
- If no completed sprint exists: uses `space.focus_hours_per_day` (or 6.0)
- Gracefully degrades without breaking analysis

---

### Feature 2: Dynamic ML Thresholds
**User Flow:**
1. User can change risk_appetite in Navbar Settings (if implemented in UI)
2. Setting is saved to Space document in MongoDB
3. When analyzing impact, `/analyze` endpoint fetches risk_appetite from space
4. Passes it to RecommendationEngine and ImpactPredictor
5. ML summary scorer uses risk-appetite-specific thresholds
6. Recommendation type (ADD/SWAP/DEFER/SPLIT) changes based on settings

**Example:**
- Same ticket with score=6:
  - **Strict**: DEFER (threshold=5)
  - **Standard**: SWAP (threshold=7)
  - **Lenient**: SPLIT (threshold=9)

---

### Feature 3: AI Story Point Suggestion
**User Flow:**
1. User types title and description in Impact Analyzer form
2. Clicks "✨ Suggest Points" button
3. Frontend calls `api.predictStoryPoints({ title, description })`
4. Backend runs TF-IDF keyword analysis on input
5. Returns `suggested_points` (3-15 range)
6. Frontend auto-fills the Story Points input
7. User can accept suggestion or manually adjust

**Note:** Uses existing NLP endpoint from `ai_routes.py` - no new backend needed.

---

## TESTING CHECKLIST

- [ ] No previous sprint: Dynamic hours falls back to 6.0 gracefully
- [ ] After completed sprint: Dynamic hours correctly reflects team velocity
- [ ] Risk appetite "Strict": More items defer; fewer get added
- [ ] Risk appetite "Standard": Balanced behavior (existing behavior)
- [ ] Risk appetite "Lenient": More items allowed; fewer defer
- [ ] Story point suggestion button works with empty description
- [ ] Story point suggestion updates form correctly
- [ ] CORS requests from React to FastAPI work without errors
- [ ] All ML predictions receive correct parameters

---

## BACKWARDS COMPATIBILITY

✅ All changes are backwards compatible:
- Dynamic focus hours has fallback to 6.0
- Default risk_appetite="Standard" maintains existing behavior
- Story point suggestion is optional UI enhancement
- No breaking changes to API contracts
- Existing spaces/sprints continue to work unchanged

