# Sprint Impact Service - Complete System Logic Documentation

## Table of Contents
1. [Story Point Suggestion Logic](#1-story-point-suggestion-logic)
2. [Sprint Goal Alignment](#2-sprint-goal-alignment)
3. [Velocity Measurement & Team Pace](#3-velocity-measurement--team-pace)
4. [Sprint Capacity Calculation](#4-sprint-capacity-calculation)
5. [Focus Hours Per Day (One Person One Day Working)](#5-focus-hours-per-day-one-person-one-day-working)
6. [Recommendation Engine Rules](#6-recommendation-engine-rules)
7. [Impact Analysis Prediction Model](#7-impact-analysis-prediction-model)

---

## 1. Story Point Suggestion Logic

### Endpoint
`POST /api/ai/predict` → `StoryPointRequest` / `StoryPointResponse`

### Input
```python
{
  "title": str,           # Task name
  "description": str      # Detailed description
}
```

### Process

#### Step 1: Text Preprocessing
- Combine title + description into single text
- Extract features using trained TF-IDF vectorizer from `effort_artifacts.pkl`
- Generate 100-dimensional TF-IDF word importance vector

#### Step 2: Context Features (5 features)
From sprint context:
```python
sprint_load_7d       = current sprint load in last 7 days
team_velocity_14d    = average story points completed per day (14-day history)
pressure_index       = story_points / days_remaining
total_links          = count of references/dependencies in description
Type_Code            = label-encoded task type (Bug/Story/Task/Epic/Improvement)
```

#### Step 3: Feature Vector Construction
**Total: 105 features** (5 numeric + 100 TF-IDF)
```python
features = {
    'sprint_load_7d': 0,        # numeric
    'team_velocity_14d': 30,    # numeric
    'pressure_index': 1.5,      # numeric
    'total_links': 2,           # numeric
    'Type_Code': 3.0,           # label-encoded
    'txt_0': 0.25,              # TF-IDF[0]
    'txt_1': 0.18,              # TF-IDF[1]
    ...
    'txt_99': 0.05              # TF-IDF[99]
}
```

#### Step 4: ML Model Prediction
- **Model**: XGBoost regressor trained on historical issue data
- **Input**: 105-feature vector
- **Output**: Raw story points prediction (continuous value)
- **Range**: 1–21 story points

#### Step 5: Confidence Scoring
```python
# Confidence based on:
# - Consistency of prediction vs. similar historical issues
# - Complexity marker (high TF-IDF weights = complex)
# - Team velocity variance

confidence = min(1.0, 
    1.0 - (std_deviation_from_mean / max_possible_std)
)
```

#### Step 6: Reasoning Extraction
Algorithm extracts "complexity indicators" by analyzing top TF-IDF terms:
```python
complexity_indicators = {
    "database_work": 1,        # if "database" term detected
    "api_integration": 1,      # if "api" term detected  
    "ui_complexity": 0,        # if few UI terms
    "infrastructure": 0,
    "legacy_system": 1         # if "legacy" term detected
}
```

### Output
```python
{
    "suggested_points": 8,
    "confidence": 0.87,
    "reasoning": [
        "Database schema modification increases complexity",
        "External API integration required",
        "Existing code patterns suggest 8 SP baseline"
    ],
    "complexity_indicators": {
        "database_work": 1,
        "api_integration": 1,
        ...
    }
}
```

---

## 2. Sprint Goal Alignment

### Overview
Evaluates semantic and metadata alignment between new task and sprint goal using **4-layer analysis**:

### Layer 1: Critical Blocker Detection
**Keywords checked** (production issues):
```python
BLOCKER_KEYWORDS = {
    "crash", "down", "outage", "broken", "not working", 
    "emergency", "hotfix", "production", "critical", 
    "security breach", "data loss", "payment failure"
}
```

**Logic**:
- If `priority == "Critical"` OR `priority == "Blocker"` AND
- Any blocker keyword found in title/description
- → **Result: CRITICAL_BLOCKER** (always accept)

---

### Layer 2: Semantic Similarity Analysis

#### TF-IDF Cosine Similarity (Primary Method)
**Algorithm**:
1. Transform sprint goal to TF-IDF vector: `vec_goal`
2. Transform task description to TF-IDF vector: `vec_task`
3. Calculate cosine similarity: `similarity = vec_goal · vec_task / (||vec_goal|| × ||vec_task||)`

**Vectorizer Configuration**:
- **max_features**: 100 (top 100 terms by frequency)
- **ngram_range**: (1, 2) (unigrams + bigrams)
- **stop_words**: English (removes "the", "a", "is", etc.)
- **sublinear_tf**: False (raw TF scaling, not log-scaled)

#### Scoring Thresholds
```python
if cosine_similarity >= 0.50:
    category = "HIGHLY_RELEVANT"
    # Strong alignment - requirement shares substantial semantic content

elif cosine_similarity >= 0.25:
    category = "TANGENTIAL"
    # Related but indirect - partial semantic overlap

else:
    category = "UNRELATED"
    # No significant alignment
```

#### Fallback: Jaccard Similarity
If TF-IDF vectorizer unavailable:
```python
jaccard = |tokens_goal ∩ tokens_task| / |tokens_goal ∪ tokens_task|

# Same thresholds: >= 0.50 → HIGHLY_RELEVANT, >= 0.25 → TANGENTIAL
```

**Example**:
```
Sprint Goal: "Complete payment processing refactoring"
Task:        "Add Stripe webhook handler"

TF-IDF terms goal:   ["payment", "processing", "refactor", ...]
TF-IDF terms task:   ["stripe", "webhook", "payment", ...]
Shared terms:        ["payment"]  ← strong signal

Cosine similarity: 0.58 → HIGHLY_RELEVANT
```

---

### Layer 3: Metadata Alignment

#### Epic Matching
```python
epic_aligned = (
    requirement_epic != "" AND
    sprint_epic != "" AND
    requirement_epic.lower() == sprint_epic.lower()
)

# Result: boolean
```

#### Component Overlap
```python
req_components = {"API", "Database"}
sprint_components = {"API", "Backend", "Database"}

overlap = len({"API", "Database"}) = 2
overlap_ratio = 2 / 3 = 0.667

if overlap_ratio >= 0.66:      component_overlap = "high"
elif overlap_ratio >= 0.33:    component_overlap = "medium"
elif overlap > 0:              component_overlap = "low"
else:                          component_overlap = "none"
```

---

### Layer 4: Integrated Recommendation

**Decision Tree**:
```
if critical_blocker:
    → ACCEPT (always, even if unaligned)

elif semantic == "HIGHLY_RELEVANT" AND epic_aligned:
    → STRONGLY_ALIGNED (add immediately)

elif semantic == "HIGHLY_RELEVANT" AND component_overlap in ["high", "medium"]:
    → STRONGLY_ALIGNED

elif semantic == "TANGENTIAL" AND component_overlap == "high":
    → PARTIALLY_ALIGNED (review with team)

elif semantic == "TANGENTIAL" AND priority == "High":
    → PARTIALLY_ALIGNED

else:
    → UNALIGNED (likely scope creep)
```

---

## 3. Velocity Measurement & Team Pace

### Velocity Calculation (14-day rolling window)

#### Definition
**Team Velocity** = Average story points completed per day in last 14 days

#### Calculation
```python
async def get_space_velocity_history(space_id):
    # Get all completed sprints in last 14 days
    sprints = db.sprints.find({
        "space_id": space_id,
        "status": "Completed",
        "updated_at": {"$gte": now - 14 days}
    })
    
    total_sp_completed = 0
    for sprint in sprints:
        items = db.backlog_items.find({
            "sprint_id": sprint.id,
            "status": "Done"
        })
        total_sp_completed += sum(item.story_points for item in items)
    
    # Average over 14 days
    team_velocity_14d = total_sp_completed / 14
    
    # Return as "SP per day"
    return {
        "team_velocity_14d": 2.14,    # e.g., 30 SP / 14 days = 2.14 SP/day
        "total_completed_sp": 30,
        "sprint_count": 2
    }
```

### Team Pace (MODULE 3: SP to Hours Translation)

#### Definition
**Team Pace** = Story points completed per development day

#### Calculation
```python
# GET /api/analytics/spaces/{space_id}/team-pace

completed_sprints = get_completed_sprints(space_id, limit=20)

total_completed_sp = 0
total_dev_days = 0

for sprint in completed_sprints:
    # Count completed SP
    completed_sp += sum(item.story_points for item in items if status == "Done")
    
    # Count development days (calendar days between start and end)
    sprint_duration_days = (end_date - start_date).days
    total_dev_days += sprint_duration_days

# Final metric
TEAM_PACE = total_completed_sp / total_dev_days

# Example:
# - 3 sprints completed: 20 SP, 25 SP, 30 SP = 75 SP total
# - 3 sprints × 14 days = 42 development days
# TEAM_PACE = 75 / 42 = 1.79 SP per day
```

#### Conversion to Hours
```python
# Hours per story point formula
hours_per_sp = 8.0 / TEAM_PACE

# With TEAM_PACE = 1.79:
hours_per_sp = 8.0 / 1.79 = 4.47 hours per SP

# Display example
5 SP task = 5 × 4.47 = ~22.35 hours
```

#### Default Handling
- **First sprint (no history)**: Default to 8 hours/SP (assumption: 1 SP = 1 day)
- **If calculation fails**: Return 8.0 hours/SP as fallback

---

## 4. Sprint Capacity Calculation

### First Sprint (No Historical Data)

#### Default Capacity
```python
# When Sprint.status == "Active" AND no completed sprints exist:

DEFAULT_CAPACITY = 30 SP

# Assumption: Team can complete 30 SP in a 2-week sprint
# (1.5 SP per day × 20 development days)
```

#### Formula
```python
initial_capacity = DEFAULT_CAPACITY = 30 SP
```

### Subsequent Sprints (With Historical Data)

#### Dynamic Capacity Calculation

```python
async def calculate_sprint_capacity(space_id):
    # Step 1: Get the most recent COMPLETED sprint
    completed_sprint = db.sprints.find_one({
        "space_id": space_id,
        "status": "Completed"
    }).sort("updated_at", DESCENDING)
    
    # Step 2: Extract metrics from completed sprint
    num_assignees = len(completed_sprint.assignees) or 1
    sprint_duration_days = (end_date - start_date).days
    
    completed_items = db.backlog_items.find({
        "sprint_id": completed_sprint.id,
        "status": "Done"
    })
    completed_sp = sum(item.story_points for item in completed_items)
    
    # Step 3: Calculate capacity for NEXT sprint
    # Formula: (Assignees × Days × 8 hours) / Completed SP
    
    hours_per_sp = (num_assignees × sprint_duration_days × 8) / completed_sp
    
    # Step 4: Estimate next sprint capacity
    # Average SP per day from last sprint
    daily_sp = completed_sp / sprint_duration_days
    
    # Normalize to per-developer
    dynamic_capacity = daily_sp × (sprint_duration_days / num_assignees)
    
    # Step 5: Cap between reasonable bounds
    next_sprint_capacity = clamp(dynamic_capacity, min=15, max=50)
    
    return next_sprint_capacity
```

#### Example Calculation
```
Completed Sprint Data:
- Assignees: 4 people
- Duration: 14 days
- Completed SP: 40 SP

Calculation:
hours_per_sp = (4 × 14 × 8) / 40 = 448 / 40 = 11.2 hours/SP
daily_sp = 40 / 14 = 2.86 SP/day
dynamic_capacity = 2.86 × (14 / 4) = 10 SP/day → ~35 SP capacity for 2-week sprint

Next Sprint Capacity = 35 SP (clamped to [15, 50])
```

---

## 5. Focus Hours Per Day (One Person One Day Working)

### Definition
**Focus Hours Per Day** = Productive working hours per developer per calendar day

### Calculation Method 1: Dynamic Calculation (Primary)

```python
async def calculate_dynamic_focus_hours(space_id, fallback=6.0):
    """
    Derives actual productive hours from the team's historical sprint performance.
    
    Formula:
    hours_per_sp = (Assignees × Sprint_Days × 8) / Completed_SP
    
    Then normalize to per-person per-day:
    focus_hours = (hours_per_sp × completed_sp_per_day) / num_assignees
    """
    
    # Step 1: Get last completed sprint
    completed_sprint = db.sprints.find_one({
        "space_id": space_id,
        "status": "Completed"
    }).sort("updated_at", DESCENDING)
    
    if not completed_sprint:
        return fallback  # 6.0 hours/day
    
    # Step 2: Extract data
    num_assignees = len(completed_sprint.assignees) or 1
    sprint_days = (end_date - start_date).days
    
    completed_sp = sum(
        item.story_points 
        for item in db.backlog_items.find({
            "sprint_id": completed_sprint.id,
            "status": "Done"
        })
    )
    
    # Step 3: Calculate hours per SP
    hours_per_sp = (num_assignees × sprint_days × 8) / completed_sp
    
    # Step 4: Calculate daily focus hours per person
    daily_sp = completed_sp / sprint_days
    focus_hours = (daily_sp × hours_per_sp) / num_assignees
    
    # Step 5: Clamp to realistic range
    focus_hours = clamp(focus_hours, min=2.0, max=10.0)
    
    return round(focus_hours, 1)
```

#### Example
```
Sprint Data:
- 4 assignees
- 14-day sprint
- 40 SP completed

Calculation:
hours_per_sp = (4 × 14 × 8) / 40 = 11.2 hours/SP
daily_sp = 40 / 14 = 2.86 SP/day
focus_hours = (2.86 × 11.2) / 4 = 8.0 hours/day

Result: Each developer is productive for ~8 hours/day
```

### Default Fallback
- If no completed sprints exist: **6.0 hours/day** (conservative estimate)
- Used in effort/schedule predictions when dynamic calculation unavailable

### Usage in Predictions
```python
# In display metrics generation:

hours_remaining = days_remaining × focus_hours_per_day
# Example: 10 days × 6 hours = 60 hours remaining

# Then compare to predicted effort:
if predicted_hours > hours_remaining:
    status = "CRITICAL"  # Will overflow sprint
```

---

## 6. Recommendation Engine Rules

### Engine Configuration
```python
risk_appetite: str = "Standard"  # Can be: Strict | Standard | Lenient

# Thresholds by appetite level
STRICT:
    schedule_risk_threshold: 30%
    prod_drag_threshold: -20%
    quality_risk_threshold: 60%

STANDARD (default):
    schedule_risk_threshold: 50%
    prod_drag_threshold: -30%
    quality_risk_threshold: 70%

LENIENT:
    schedule_risk_threshold: 70%
    prod_drag_threshold: -40%
    quality_risk_threshold: 80%
```

### Rule Priority & Decision Tree

#### Rule 0: Sprint Almost Over
```python
MIN_DAYS_FOR_NEW_WORK = 2 days

if days_remaining < 2 AND priority NOT IN ["Critical", "Highest"]:
    action = "DEFER"
    reason = f"Sprint ends in {days_remaining} day(s). Too risky to add non-critical work."
```

#### Rule 0.5: Emergency Protocol (Critical Priority)
```python
if priority IN ["Critical", "Highest"]:
    # Bypass ALL ML risk checks
    
    # Try to make room by swapping
    swap_candidate = find_lowest_value_todo_item(active_items)
    
    if swap_candidate exists:
        action = "FORCE SWAP"
        target = swap_candidate
        reason = "EMERGENCY: Critical priority. Swapping out lowest-value item."
    else:
        action = "OVERLOAD"
        reason = "EMERGENCY: No items to swap. Accepting sprint overload."
```

#### Rule 1: Large Ticket Mid-Sprint
```python
LARGE_TICKET_SP = 13
LARGE_TICKET_DAYS = 10

if story_points >= 13 AND days_remaining < 10:
    action = "SPLIT"
    suggestion = f"Break into two: Analysis ({sp//2} SP), Implementation ({sp - sp//2} SP)"
    reason = f"Ticket too large ({story_points} SP) for {days_remaining} remaining days."
```

#### Rule 2: Multi-Signal ML Safety Net
```python
# Triggers if ANY of three ML predictions exceeds threshold
triggered_signals = []

if schedule_risk > schedule_risk_threshold:
    triggered_signals.append(f"Schedule Risk {schedule_risk:.0f}% > {threshold:.0f}%")

if velocity_change < prod_drag_threshold:
    triggered_signals.append(f"Productivity drag {abs(velocity_change):.0f}% > {abs(threshold):.0f}%")

if quality_risk > quality_risk_threshold:
    triggered_signals.append(f"Quality Risk {quality_risk:.0f}% > {threshold:.0f}%")

if len(triggered_signals) > 0:
    action = "DEFER"
    reason = f"ML Risk Signals: {'; '.join(triggered_signals)}"
```

#### Rule 3: Capacity Constraint
```python
if story_points > free_capacity:
    action = "DEFER"
    reason = f"Ticket ({story_points} SP) exceeds available capacity ({free_capacity:.0f} SP)."
```

#### Rule 4: Default ADD (All Checks Pass)
```python
else:
    action = "ADD"
    reason = "All checks passed. Safe to add to sprint."
```

---

## 7. Impact Analysis Prediction Model

### Overview
Predicts **4 independent impact dimensions**:
1. **Effort** — How long will this task take?
2. **Schedule Risk** — Will it overflow the sprint?
3. **Quality Risk** — How likely are defects?
4. **Productivity** — Will context-switching slow down the team?

---

### 7.1 Effort Prediction

#### Model Type
**XGBoost Regressor** (gradient boosting ensemble)

#### Features (105 total)
- **5 numeric features**: sprint_load_7d, team_velocity_14d, pressure_index, total_links, Type_Code
- **100 TF-IDF features**: Word importance vectors from task title + description

#### Training Data
Historical issues with manually-recorded actual hours worked

#### Prediction Output
```python
effort = {
    "hours_median": 24.5,      # Predicted hours to complete
    "hours_lower": 12.0,       # 25th percentile (optimistic)
    "hours_upper": 48.0,       # 75th percentile (pessimistic)
    "confidence": 0.82         # Variance-based confidence score
}
```

#### Display Logic
```python
hours_remaining = days_remaining × focus_hours_per_day

if predicted_hours > hours_remaining:
    label = "Sprint Overload"
    status = "critical"
    
elif predicted_hours > 0.8 × hours_remaining:
    label = "Tight Fit"
    status = "warning"
    
else:
    label = "Fits in Sprint"
    status = "safe"
```

---

### 7.2 Schedule Risk Prediction

#### Model Type
**XGBoost Classifier** (probability of spillover)

#### Features (9 features)
```python
Story_Point            # numeric
total_links            # reference count
total_comments         # discussion count
author_total_load      # assignee's current workload
link_density           # links per story point
comment_density        # comments per story point
pressure_index         # sp / days_remaining
Type_Code              # label-encoded type
Priority_Code          # label-encoded priority
```

#### Data Imputation
Missing values filled with sklearn `SimpleImputer(strategy='median')`:
```python
fill_values = [2, 0, 0, 4519, 0, 0, 0.143, 4, 3]
```

#### Prediction Output
```python
schedule = {
    "probability": 35.5,       # % chance of spillover
    "risk_category": "moderate",
    "days_at_risk": 3          # estimated days over deadline
}
```

#### Display Logic
```python
spillover_pct = prediction

if spillover_pct > 50:
    label = "Delay Imminent"
    status = "critical"
    detail = f"{spillover_pct:.0f}% chance of spillover"
    
elif spillover_pct > 30:
    label = "Moderate Risk"
    status = "warning"
    
else:
    label = "On Track"
    status = "safe"
```

---

### 7.3 Quality Risk Prediction

#### Model Type
**Logistic Regression** (probability of defects)

#### Features
Task complexity inferred from:
- Description text length and specificity
- Keywords: "refactor", "performance", "database", "api"
- Historical defect rate for similar items

#### Label Encoding
UI Priority → Quality Priority (different mapping from risk):
```python
"Low" → "Low"           (quality label)
"Medium" → "Medium"     (quality label)
"High" → "High"         (quality label)
"Critical" → "Highest"  (quality label)
```

#### Prediction Output
```python
quality = {
    "probability": 45.2,       # % chance of introducing defects
    "defect_likelihood": "elevated",
    "qa_time_multiplier": 1.5  # Extra QA effort needed
}
```

#### Display Logic
```python
defect_pct = prediction

if defect_pct > 60:
    label = "High Bug Risk"
    status = "critical"
    detail = f"{defect_pct:.0f}% defect likelihood. Double QA recommended."
    
elif defect_pct > 30:
    label = "Elevated Risk"
    status = "warning"
    
else:
    label = "Standard Risk"
    status = "safe"
```

---

### 7.4 Productivity Prediction

#### Model Type
**Hybrid XGBoost + MLP Ensemble**
- XGBoost (gradient boosting)
- MLP (multi-layer perceptron neural network)
- **Output**: Average of both model predictions

#### Features (9 features, same as Schedule Risk)
```python
story_points
log(story_points / days_remaining)     # log-space pressure (mean=-0.744)
log(1 + days_remaining)                # log-space days (mean=1.054)
team_velocity_14d
sprint_load_7d
story_points / (days_remaining × 24)   # hours-normalized pressure (mean=0.020)
sprint_progress                         # % of sprint elapsed
type_code                               # label-encoded
priority_code                           # label-encoded
```

#### Scaling
Features normalized with `StandardScaler` using fitted statistics:
```python
mean = [?, ?, ?, ?, ?, ?, ?, ?, ?]
scale = [?, ?, ?, ?, ?, ?, ?, ?, ?]
# Verified against 9-feature vector from training
```

#### Prediction Output
```python
productivity = {
    "velocity_change": -18.5,          # % slowdown expected
    "days_lost": 2.3,                  # team context-switching cost
    "drop_pct": 18.5                   # absolute productivity drop %
}
```

#### Display Logic
```python
drag_pct = abs(velocity_change)

if drag_pct > 30:
    label = "High Drag"
    status = "critical"
    detail = f"~{drag_pct:.0f}% slowdown on remaining backlog"
    
elif drag_pct > 10:
    label = "Negative"
    status = "warning"
    
else:
    label = "Minimal Impact"
    status = "safe"
```

---

### 7.5 Summary Generation

After all 4 predictions, generate executive summary:

```python
def _generate_summary(effort, schedule, quality, productivity, risk_appetite):
    signals = []
    
    # Check critical signals
    if effort['critical']:
        signals.append("EFFORT OVERLOAD")
    if schedule['probability'] > 50:
        signals.append("SCHEDULE RISK")
    if quality['probability'] > 60:
        signals.append("QUALITY RISK")
    if productivity['velocity_change'] < -30:
        signals.append("TEAM DRAG")
    
    if len(signals) == 0:
        return {
            "overall_status": "safe",
            "headline": "All metrics within acceptable range",
            "risk_signals": []
        }
    elif len(signals) >= 2:
        return {
            "overall_status": "critical",
            "headline": f"Multiple risk signals detected: {', '.join(signals)}",
            "risk_signals": signals,
            "recommendation": "DEFER or SPLIT this ticket"
        }
    else:
        return {
            "overall_status": "warning",
            "headline": f"Risk detected: {signals[0]}",
            "risk_signals": signals
        }
```

---

## Summary: Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER SUBMITS NEW TASK                        │
├──────────────────────────────────────────────────────────────────┤
│  Title, Description, Story Points, Priority, Type               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
  ┌─────────────────────┐         ┌────────────────────┐
  │   MODULE 1: AI      │         │  MODULE 4: Sprint  │
  │   Story Point       │         │  Goal Alignment    │
  │   Suggestion        │         │  (TF-IDF)          │
  │ • TF-IDF features   │         │ • Layer 1: Blocker │
  │ • XGBoost model     │         │ • Layer 2: Semantic│
  │ • 105 features      │         │ • Layer 3: Metadata│
  │ • Returns: 1-21 SP  │         │ • Result: Aligned? │
  └─────────────────────┘         └────────────────────┘
        │                                     │
        └──────────────────┬──────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │  Sprint Context Enrichment           │
        │ • Days remaining                      │
        │ • Team velocity (14-day average)      │
        │ • Focus hours per day (from history) │
        │ • Current sprint load                │
        └──────────────────┬───────────────────┘
                           │
        ┌──────────────────┴──────────────────────┐
        │                                         │
        ▼                                         ▼
  ┌────────────────┐                    ┌──────────────────┐
  │ MODULE 2:      │                    │ MODULE 3:        │
  │ 4D Impact      │                    │ SP → Hours       │
  │ Analysis       │                    │ Translation      │
  │                │                    │                  │
  │ • Effort       │                    │ • Team pace =    │
  │ • Schedule     │                    │   completed_sp /  │
  │ • Quality      │                    │   dev_days       │
  │ • Productivity │                    │                  │
  │                │                    │ • hours_per_sp = │
  │ Each with:     │                    │   8 / team_pace  │
  │ • ML prediction│                    │                  │
  │ • Risk signal  │                    │ • Returns factor │
  │ • Display text │                    │   for conversion │
  └────────────────┘                    └──────────────────┘
        │                                     │
        └──────────────────┬──────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │ Recommendation Engine                │
        │ • 5 decision rules (priority order)   │
        │ • Multi-signal ML check              │
        │ • Risk appetite thresholds           │
        │ • Returns: ADD | DEFER | SPLIT | SWAP│
        └──────────────────┬───────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │ Final Recommendation Package         │
        │ • Action: ADD / DEFER / SPLIT / SWAP │
        │ • Reason: Detailed explanation       │
        │ • Impact: Risk signals summary       │
        │ • Plan: Step-by-step guidance        │
        └──────────────────────────────────────┘
```

---

## Key Constants & Thresholds

### Capacity & Time
```python
DEFAULT_FIRST_SPRINT_CAPACITY = 30 SP
MIN_DAYS_FOR_NEW_WORK = 2 days
LARGE_TICKET_SP = 13
LARGE_TICKET_DAYS = 10
FOCUS_HOURS_FALLBACK = 6.0 hours/day
```

### Risk Thresholds (Standard Appetite)
```python
SCHEDULE_RISK_THRESHOLD = 50%
PROD_DRAG_THRESHOLD = -30%
QUALITY_RISK_THRESHOLD = 70%
```

### Alignment Scores
```python
SEMANTIC_HIGHLY_RELEVANT = >= 0.50
SEMANTIC_TANGENTIAL = >= 0.25
COMPONENT_HIGH_OVERLAP = >= 0.66
COMPONENT_MEDIUM_OVERLAP = >= 0.33
```

---

## Model Training Details

All ML models loaded from pickle artifacts:

| Model | File | Type | Features | Output |
|-------|------|------|----------|--------|
| Effort | effort_artifacts.pkl | XGBoost | 105 (numeric + TF-IDF) | Continuous hours |
| Schedule Risk | risk_artifacts.pkl | XGBoost Classifier | 9 (encoded) | Probability % |
| Quality Risk | le_prio_quality.pkl | Logistic | Task features | Probability % |
| Productivity | productivity_artifacts.pkl | Hybrid (XGBoost + MLP) | 9 (scaled) | Velocity change % |

All feature engineering happens in `feature_engineering.py` using actual fitted sklearn objects.
