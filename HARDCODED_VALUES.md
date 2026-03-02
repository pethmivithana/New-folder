# Hardcoded Values in Sprint Impact Tool

This document identifies all hardcoded constants, thresholds, and magic numbers in the codebase that should be made configurable.

---

## 1. **Impact Predictor** (`impact_predictor.py`)

### Status Classification Thresholds

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `schedule_risk > 50` | 50.0 | Line 115 | Schedule risk "Critical Risk" | ✅ YES |
| `schedule_risk > 30` | 30.0 | Line 119 | Schedule risk "High Risk" | ✅ YES |
| `drag_pct > 30` | 30.0 | Line 132 | Productivity "High Drag" | ✅ YES |
| `drag_pct > 10` | 10.0 | Line 136 | Productivity "Negative" | ✅ YES |
| `defect_pct > 60` | 60.0 | Line 147 | Quality risk "High Bug Risk" | ✅ YES |
| `defect_pct > 30` | 30.0 | Line 150 | Quality risk "Elevated Risk" | ✅ YES |
| `spillover_prob > 50` | 50.0 | Line 292 | Schedule spillover warning | ✅ YES |
| `spillover_prob > 30` | 30.0 | Line 294 | Schedule spillover moderate | ✅ YES |

### Complexity Detection Thresholds

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `story_points >= 13` | 13 | Line 345 | Large ticket detection | ✅ YES |
| `pressure_ratio >= 1.0` | 1.0 | Line 345 | Sprint pressure indicator | ✅ YES |
| `complexity_score == 3` | 3 | Line 350 | Full architectural multiplier | ❌ NO (logic) |
| `complexity_score == 2` | 2 | Line 352 | High complexity multiplier | ❌ NO (logic) |
| `complexity_score == 1` | 1 | Line 354 | Moderate complexity multiplier | ❌ NO (logic) |
| Complexity multiplier (3) | 1.9 | Line 351 | Architectural tasks | ✅ YES (QUALITY_RISK_COMPLEXITY_MULTIPLIER) |
| Complexity multiplier (2) | 1.5 | Line 353 | High complexity tasks | ✅ YES (should extract) |
| Complexity multiplier (1) | 1.2 | Line 355 | Moderate complexity tasks | ✅ YES (should extract) |

### Summary Scorer Thresholds

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `score >= 7` | 7 | Line 468 | "DEFER" recommendation | ✅ YES |
| `score >= 4` | 4 | Line 469 | "SWAP" recommendation | ✅ YES |
| `score >= 2` | 2 | Line 470 | "SPLIT" recommendation | ✅ YES |
| `effort['status'] == 'critical'` points | 3 | Line 459 | Critical effort score | ✅ YES |
| `effort['status'] == 'warning'` points | 2 | Line 460 | Warning effort score | ✅ YES |
| `schedule > 50` points | 3 | Line 461 | High schedule risk score | ✅ YES |
| `schedule > 30` points | 2 | Line 462 | Moderate schedule risk score | ✅ YES |
| `quality > 60` points | 2 | Line 463 | High quality risk score | ✅ YES |
| `quality > 30` points | 1 | Line 464 | Moderate quality risk score | ✅ YES |
| `productivity > 30` points | 2 | Line 465 | High drag score | ✅ YES |
| `productivity > 10` points | 1 | Line 466 | Moderate drag score | ✅ YES |

### Fallback Values

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| Story points to hours ratio | 5 | Line 476 | Hours = SP × 5 | ✅ YES |
| Fallback quality risk | 40.0% | Line 498 | Default quality estimate | ✅ YES |
| Fallback productivity drag | -10.0% | Line 504 | Default productivity estimate | ✅ YES |
| Fallback productivity drop | 10.0% | Line 505 | Default productivity drop | ✅ YES |

---

## 2. **Recommendation Engine** (`recommendation_engine.py`)

### Configuration Thresholds (Module Level)

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `SCHEDULE_RISK_THRESHOLD` | 50.0 | Line 33 | DEFER trigger for schedule | ✅ YES |
| `PROD_DRAG_THRESHOLD` | -30.0 | Line 34 | DEFER trigger for productivity | ✅ YES |
| `QUALITY_RISK_THRESHOLD` | 70.0 | Line 35 | DEFER trigger for quality | ✅ YES |
| `MIN_DAYS_FOR_NEW_WORK` | 2 | Line 40 | Minimum sprint days remaining | ✅ YES |
| `LARGE_TICKET_SP` | 13 | Line 41 | Story point threshold for large | ✅ YES |
| `LARGE_TICKET_DAYS` | 10 | Line 42 | Days threshold for large tickets | ✅ YES |

### Quality Risk Logic

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `quality_risk > 50` | 50 | recommendation_engine.py:191 | Quality gate check | ✅ YES |

---

## 3. **Explanation Generator** (`explanation_generator.py`)

### Confidence Color Thresholds

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `schedule_risk > 55` | 55.0 | Line 46 | Red confidence threshold | ✅ YES |
| `quality_risk > 60` | 60.0 | Line 46 | Red confidence threshold | ✅ YES |
| `velocity_change < -30` | -30.0 | Line 46 | Red confidence threshold | ✅ YES |
| `schedule_risk > 30` | 30.0 | Line 48 | Yellow confidence threshold | ✅ YES |
| `quality_risk > 30` | 30.0 | Line 48 | Yellow confidence threshold | ✅ YES |
| `velocity_change < -10` | -10.0 | Line 48 | Yellow confidence threshold | ✅ YES |

### Split (Elephant Protocol) Ratio

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| Analysis split ratio | 0.30 (30%) | Line 179 | Analysis vs Implementation split | ✅ YES |
| Implementation split ratio | 0.70 (70%) | Line 180 (derived) | Analysis vs Implementation split | ✅ YES |
| Minimum SP per slice | 1 | Line 180 | Minimum story points | ✅ YES |

---

## 4. **Routes & API** (`routes/`)

### Sprint Routes (`impact_routes.py`)

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `days_remaining` | 14 (fallback) | Line 35 | Default sprint length | ✅ YES |
| `sprint_progress` | 0.0 (fallback) | Line 37 | Default progress | ✅ YES |
| `focus_hours_per_day` | 6.0 (fallback) | Line 161 | Default work hours | ✅ YES |
| `schedule_risk > 0.55` | 0.55 | Line 69 | Priority change threshold | ✅ YES |
| `quality_risk > 0.60` | 0.60 | Line 69 | Priority change threshold | ✅ YES |
| `schedule_risk > 0.35` | 0.35 | Line 71 | Priority change threshold | ✅ YES |
| `quality_risk > 0.40` | 0.40 | Line 71 | Priority change threshold | ✅ YES |
| `schedule_risk > 0.20` | 0.20 | Line 73 | Priority change threshold | ✅ YES |
| `quality_risk > 0.25` | 0.25 | Line 73 | Priority change threshold | ✅ YES |

### Simulate Routes (`simulate_routes.py`)

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `WORK_HOURS_PER_DAY` | 6 | Line 142 | Simulation work hours | ✅ YES |
| `days_remaining` | 14 (fallback) | Line 150 | Default sprint length | ✅ YES |
| `sprint_progress` | 0.0 (fallback) | Line 151 | Default progress | ✅ YES |

### AI Routes (`ai_routes.py`)

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `total_interfaces > 3` | 3 | Line 142 | High interface count | ✅ YES |
| `total_interfaces > 1` | 1 | Line 144 | Moderate interface count | ✅ YES |
| `total_tech > 2` | 2 | Line 148 | High tech stack count | ✅ YES |
| `total_tech > 0` | 0 | Line 150 | Any tech stack present | ✅ YES |
| Min suggested points | 3 | Line 159 | Story point floor | ✅ YES |
| Max suggested points | 15 | Line 161 | Story point ceiling | ✅ YES |
| `avg_length > 30` | 30 | Line 184 | Long description threshold | ✅ YES |
| `avg_length < 10` | 10 | Line 186 | Short description threshold | ✅ YES |

### AI Routes - Story Point Keywords (`ai_routes.py`)

| Keyword Type | Examples | Weights | Location | Should Be Configurable |
|--------------|----------|---------|----------|----------------------|
| High complexity keywords | migration, refactor, architecture, security, scalability | 5-8 | Lines 13-29 | ✅ YES |
| Medium complexity keywords | implement, create, update, enhance, service | 3-5 | Lines 32-46 | ✅ YES |
| Low complexity keywords | fix, bug, styling, css, ui | 1-3 | Lines 49-62 | ✅ YES |
| Interface keywords | frontend, backend, api, endpoint, graphql, microservice | - | Lines 65-73 | ✅ YES |
| Tech keywords | react, node, python, mongodb, docker, kubernetes, aws | - | Lines 75-82 | ✅ YES |

---

## 5. **Feature Engineering** (`feature_engineering.py`)

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `_AUTHOR_LOAD_MEDIAN` | 4519.0 | Line 199 | Historical author load imputation | ✅ YES |
| Scaler divide-by-zero safety | 1.0 | Line 306 | Prevent division by zero | ❌ NO (safety) |
| Default sprint progress | 0.0 | Line 385 | Division safety check | ❌ NO (logic) |

---

## 6. **Models** (`models.py`)

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `focus_hours_per_day` | 6.0 (default) | Line 53 | Space model default | ✅ YES |

---

## 7. **Database** (`database.py`)

| Variable | Value | Location | Used For | Should Be Configurable |
|----------|-------|----------|----------|----------------------|
| `total_points` | 0 (init) | Various | Accumulator init | ❌ NO (initialization) |
| `done_points` | 0 (init) | Various | Accumulator init | ❌ NO (initialization) |

---

## Recommendations

### HIGH PRIORITY (Impact Model Accuracy)

1. **Extract Complexity Multipliers** (Line 1.5, 1.2 hardcodes)
   - Create `QUALITY_RISK_HIGH_MULTIPLIER = 1.5`
   - Create `QUALITY_RISK_MODERATE_MULTIPLIER = 1.2`

2. **Extract Status Classification Thresholds** (Lines 50, 30, 60, 30, 10 hardcodes)
   - Create config for schedule/quality/productivity risk boundaries
   - Allow tuning per domain/team

3. **Extract Summary Scorer Points** (3, 2, 1 hardcodes)
   - Create `SCORE_POINTS_*` constants for each signal
   - Allow weighting adjustment per team

### MEDIUM PRIORITY (Explanation & Recommendations)

4. **Extract Confidence Color Thresholds** (Lines 55, 60, -30, 30, 30, -10)
   - Create `CONFIDENCE_*_THRESHOLD` constants
   - Allow UI customization

5. **Extract Split Protocol Ratio** (30/70 split)
   - Create `SPLIT_ANALYSIS_RATIO = 0.30`
   - Create `SPLIT_MIN_SP = 1`

### LOW PRIORITY (Supporting Data)

6. **Extract Complexity Keywords** (ai_routes.py)
   - Move `COMPLEXITY_KEYWORDS` to a configuration file
   - Allow domain-specific keyword customization
   - Support dynamic keyword loading

7. **Extract Default Assumptions** (focus_hours, days_remaining)
   - Create `DEFAULT_*` constants
   - Document where these should come from (Space model)

---

## Configuration Priority Matrix

| Item | Impact | Difficulty | Priority |
|------|--------|-----------|----------|
| Summary scorer points (7, 4, 2) | High | Easy | **P0** |
| Status thresholds (50, 30, 60, 30, 10) | High | Easy | **P0** |
| Complexity multipliers (1.9, 1.5, 1.2) | High | Easy | **P0** |
| Confidence color thresholds | Medium | Easy | **P1** |
| Split protocol ratio | Medium | Easy | **P1** |
| Complexity keywords | Medium | Medium | **P1** |
| Default values (hours, days) | Low | Easy | **P2** |
| Historical author load | Low | Medium | **P2** |

---

## Next Steps

1. Create `config/ml_thresholds.yaml` for all hard thresholds
2. Create `config/complexity_keywords.yaml` for NLP features
3. Create environment variable overrides for critical values
4. Update `CALIBRATION_GUIDE.md` with configuration file format
5. Add configuration validation on startup
