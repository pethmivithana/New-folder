# Module 3 & 4 Implementation Summary

## Overview
This document outlines the integration of **Module 3: SP to Hours Translation** and **Module 4: Semantic Sprint Alignment** into the agile management codebase.

---

## MODULE 3: SP to Hours Translation

### Purpose
Converts abstract story points into tangible hours for stakeholder visibility without requiring developers to work in hours directly. Maintains Agile methodology while providing management transparency.

### Key Formula
```
hours_per_sp = 8 / TEAM_PACE
where TEAM_PACE = Total_Completed_SP / Total_Dev_Days (from historical data)
```

### Backend Changes

#### 1. **models.py** (Modified)
- Added `historical_pace` field to Sprint model (default 1.0)
- Stores team pace per sprint for tracking changes over time

#### 2. **analytics_routes.py** (Modified)
- **New Endpoint**: `GET /api/analytics/spaces/{space_id}/team-pace`
- Calculates TEAM_PACE from completed sprints in the space
- Returns:
  - `team_pace`: Story points per development day
  - `hours_per_sp`: Derived hours per story point (8 / team_pace)
  - `sprints_analyzed`: Number of historical sprints used
  - Metadata for transparency

#### 3. **database.py** (Modified)
- **New Function**: `get_completed_sprints(space_id, limit=20)`
- Fetches last N completed sprints with completed_sp counts
- Used by analytics service for pace calculation

#### 4. **ai_routes.py** (Modified)
- **New Helper Functions**:
  - `calculate_hours_per_sp(team_pace)`: Returns hours_per_sp from pace
  - `format_sp_to_hours(story_points, hours_per_sp)`: Returns formatted string like "5 SP (~40 Hours)"

### Frontend Changes

#### 1. **hourTranslation.js** (New Utility File)
Location: `/frontend/src/utils/hourTranslation.js`

**Exported Functions**:
- `fetchTeamPace(spaceId, apiBaseUrl)`: Fetches team pace from backend
- `formatSPWithHours(storyPoints, hoursPerSP)`: Returns "5 SP (~40 Hours)"
- `getHoursEstimate(storyPoints, hoursPerSP)`: Returns numeric hours
- `getStoryPointsFromHours(hours, hoursPerSP)`: Reverse conversion
- `translateCapacity(sprintCapacitySP, hoursPerSP)`: Full capacity translation
- `createTooltip(storyPoints, hoursPerSP)`: Tooltip text with pace info

#### 2. **ImpactAnalyzer.jsx** (Modified)
- **New State**:
  - `hoursPerSP`: Stores conversion factor fetched from analytics
  - `loadingPace`: Tracks async team pace loading

- **New useEffect**: Loads team pace on component mount
  ```javascript
  fetchTeamPace(spaceId)
    .then(data => setHoursPerSP(data.hours_per_sp || 8.0))
  ```

- **Updated CapacityBar Component**: Now displays hours alongside SP
  - Example: "5 / 10 SP (40 / 80 hrs)"
  - Shows remaining capacity in both units

- **Story Points Input**: Displays hours translation below input
  - Example: "5 SP (~40 Hours)" updates in real-time

### Usage Example
```javascript
import { formatSPWithHours, fetchTeamPace } from '../utils/hourTranslation';

// Fetch team pace from API
const { team_pace, hours_per_sp } = await fetchTeamPace(spaceId);

// Display with translation
const display = formatSPWithHours(5, hours_per_sp); // "5 SP (~40 Hours)"
```

---

## MODULE 4: Semantic Sprint Alignment

### Purpose
Automatically flags potential scope creep by checking if a new task aligns with the sprint goal using TF-IDF semantic similarity. Threshold of 0.4 (40%) indicates unaligned work.

### Alignment Levels
- **STRONGLY_ALIGNED** (score ≥ 0.5): Task directly supports sprint goal
- **PARTIALLY_ALIGNED** (0.3 ≤ score < 0.5): Related but tangential work
- **UNALIGNED** (score < 0.3): Likely scope creep

### Backend Changes

#### 1. **ai_routes.py** (Modified)
- **New Pydantic Models**:
  - `SimpleAlignmentRequest`: `{sprint_goal, task_description}`
  - `SimpleAlignmentResponse`: `{alignment_score, alignment_level, recommendation}`

- **New Endpoint**: `POST /api/ai/align-simple-goal`
  - Uses existing `tfidf_cosine_similarity()` from `tfidf_registry.py`
  - Returns alignment score (0-1) and human-readable recommendation
  - **NO external LLM calls** — pure TF-IDF (fast, deterministic, free)
  - Thresholds:
    - score ≥ 0.5 → STRONGLY_ALIGNED
    - score 0.3-0.5 → PARTIALLY_ALIGNED
    - score < 0.3 → UNALIGNED

### Frontend Changes

#### 1. **sprintAlignment.js** (New Utility File)
Location: `/frontend/src/utils/sprintAlignment.js`

**Exported Functions**:
- `checkSprintAlignment(sprintGoal, taskDescription, apiBaseUrl)`: Calls backend endpoint
- `isScopeCreep(alignmentScore, threshold=0.4)`: Boolean check
- `getAlignmentColors(alignmentLevel)`: Returns {bg, text, border, accent} colors
- `getAlignmentIcon(alignmentLevel)`: Returns emoji (🎯 / ⚠️ / 🚫)
- `formatAlignmentPercentage(score)`: Returns 0-100 percentage
- `getScopeCreepWarning(alignmentScore, taskTitle)`: Human-readable warning message
- `batchCheckAlignment(sprintGoal, tasks, apiBaseUrl)`: Checks multiple tasks

#### 2. **ImpactAnalyzer.jsx** (Modified)
- **New Component**: `ScopeCreepWarning({ alignmentScore, taskTitle, onDismiss })`
  - Displays red warning if alignment score < 0.4
  - Shows percentage and recommendation
  - Can be dismissed by user

- **New State**:
  - `simpleAlignment`: Stores alignment check result
  - `checkingAlignment`: Tracks async alignment check

- **New Function**: `checkSimpleAlignment()`
  - Calls `checkSprintAlignment()` from utility
  - Combines form title + description as task_description
  - Updates `simpleAlignment` state

- **New Button**: "⚠️ Check Scope Creep"
  - Positioned above "Analyze Impact" button
  - Quick, non-blocking alignment check
  - Shows loading spinner while fetching

- **New Display**: Shows warning if alignment < 0.4
  - Red background (#fef2f2)
  - Clear explanation of why task might be scope creep
  - Dismissible by user

### Usage Example
```javascript
import { checkSprintAlignment, getScopeCreepWarning } from '../utils/sprintAlignment';

// Check if task aligns with sprint goal
const alignment = await checkSprintAlignment(
  "Implement payment system",
  "Add support for credit card checkout via Stripe"
);

// alignment.alignment_score → 0.78 (STRONGLY_ALIGNED)
// alignment.alignment_level → "STRONGLY_ALIGNED"
// alignment.recommendation → "Task is strongly aligned..."

// Check for scope creep
if (alignment.alignment_score < 0.4) {
  const warning = getScopeCreepWarning(alignment.alignment_score, "Add dark mode");
  // "⚠️ SCOPE CREEP ALERT: Task has only 15% alignment..."
}
```

---

## Integration Points

### Data Flow

```
MODULE 3 (Hours Translation):
┌─────────────────────────────────┐
│ Completed Sprints (MongoDB)      │
└────────────┬────────────────────┘
             │ (get_completed_sprints)
             ↓
┌─────────────────────────────────┐
│ /api/analytics/team-pace         │
│ Returns: hours_per_sp            │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│ ImpactAnalyzer.jsx              │
│ - hoursPerSP state              │
│ - Displays "5 SP (~40 Hours)"    │
│ - CapacityBar shows hours        │
└─────────────────────────────────┘

MODULE 4 (Sprint Alignment):
┌─────────────────────────────────┐
│ Sprint Goal (from Sprint model)  │
│ + Task Description (form input)  │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│ /api/ai/align-simple-goal       │
│ (TF-IDF cosine_similarity)       │
│ Returns: alignment_score (0-1)   │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│ ImpactAnalyzer.jsx              │
│ - simpleAlignment state         │
│ - Shows ScopeCreepWarning if <0.4│
└─────────────────────────────────┘
```

### API Contracts

**MODULE 3 - Team Pace Endpoint**
```
GET /api/analytics/spaces/{space_id}/team-pace
Response: {
  "team_pace": 1.5,
  "hours_per_sp": 5.33,
  "sprints_analyzed": 5,
  "total_completed_sp": 150,
  "total_dev_days": 100,
  "metadata": "Based on 5 completed sprints"
}
```

**MODULE 4 - Simple Alignment Endpoint**
```
POST /api/ai/align-simple-goal
Request: {
  "sprint_goal": "Complete payment integration",
  "task_description": "Add support for Apple Pay checkout"
}
Response: {
  "alignment_score": 0.72,
  "alignment_level": "STRONGLY_ALIGNED",
  "recommendation": "Task is strongly aligned with sprint goal (score: 0.72). Safe to add to sprint."
}
```

---

## Files Changed / Created

### Section A: Modified Files
1. **models.py** — Added `historical_pace` to Sprint
2. **analytics_routes.py** — Added team-pace endpoint + import
3. **database.py** — Added `get_completed_sprints()` function
4. **ai_routes.py** — Added helpers, Pydantic models, `/align-simple-goal` endpoint
5. **ImpactAnalyzer.jsx** — Integrated MODULE 3 & 4 UI components

### Section B: New Files
1. **hourTranslation.js** — MODULE 3 utility functions
2. **sprintAlignment.js** — MODULE 4 utility functions

### Section C: Removed Files
None. All changes are additive.

---

## Testing Checklist

- [ ] Team pace endpoint returns correct `hours_per_sp` from historical sprints
- [ ] Story points display shows hours translation (e.g., "5 SP (~40 Hours)")
- [ ] Sprint capacity bar shows both SP and hours
- [ ] Simple alignment endpoint returns scores between 0-1
- [ ] Scope creep warning appears when alignment < 0.4
- [ ] Warning disappears when user dismisses it
- [ ] Team pace loads on component mount
- [ ] Team pace defaults to 8.0 hours/SP if no data available

---

## Performance Notes

- **MODULE 3**: Single backend call per space load (cached in state)
- **MODULE 4**: Single backend call per alignment check (on-demand, fast TF-IDF)
- Both use existing, proven systems (MongoDB, scikit-learn)
- No new external API keys or dependencies required

---

## Future Enhancements

1. **Module 3**: Track historical pace trends, flag when pace drops
2. **Module 4**: Integrate with ST-based alignment as alternative model
3. **Both**: Cache results in localStorage for offline mode
4. **Both**: Batch operations (check alignment for all backlog items)

---

## Questions?

Refer to:
- `/frontend/src/utils/hourTranslation.js` for MODULE 3 implementation
- `/frontend/src/utils/sprintAlignment.js` for MODULE 4 implementation
- Backend code in `/services/sprint_impact_service/` for API details
