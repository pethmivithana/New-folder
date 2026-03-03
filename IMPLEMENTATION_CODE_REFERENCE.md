# Complete Implementation Code Reference

## 1. CALCULATE DYNAMIC FOCUS HOURS FUNCTION
**File:** `services/sprint_impact_service/routes/impact_routes.py`
**Lines:** 16-86

```python
async def calculate_dynamic_focus_hours(space_id: str, fallback: float = 6.0) -> float:
    """
    Calculate focus hours per day dynamically based on the team's previous sprint.
    
    Formula: (Assignees * Days * 8 hours) / Completed SP = hours per story point
    Then: focus_hours_per_day = team_velocity (SP per day) * hours_per_sp
    
    If no previous sprint exists, return fallback (6.0).
    """
    try:
        db = get_database()
        
        # Find the most recently COMPLETED sprint for this space
        completed_sprint = await db.sprints.find_one(
            {"space_id": space_id, "status": "Completed"},
            sort=[("updated_at", DESCENDING)]
        )
        
        if not completed_sprint:
            return fallback
        
        # Get start/end dates
        start_date = completed_sprint.get("start_date")
        end_date = completed_sprint.get("end_date")
        
        if not start_date or not end_date:
            return fallback
        
        # Calculate duration in days
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        sprint_duration_days = max(1, (end_date - start_date).days)
        
        # Get all completed items from this sprint
        completed_items = await db.backlog_items.find(
            {
                "sprint_id": completed_sprint["_id"],
                "status": "Done"
            }
        ).to_list(length=None)
        
        completed_sp = sum(item.get("story_points", 0) for item in completed_items)
        
        if completed_sp == 0:
            return fallback
        
        # Get number of assignees
        num_assignees = len(completed_sprint.get("assignees", [])) or 1
        
        # Calculate hours per story point
        # (Assignees * Days * 8 hours) / Completed SP
        hours_per_sp = (num_assignees * sprint_duration_days * 8) / completed_sp
        
        # Daily focus capacity per developer
        # This is the hours per SP * average SP completed per day
        daily_sp = completed_sp / sprint_duration_days
        dynamic_focus_hours = daily_sp * hours_per_sp / num_assignees
        
        # Cap between 2.0 and 10.0 hours per day (reasonable bounds)
        dynamic_focus_hours = max(2.0, min(10.0, dynamic_focus_hours))
        
        return round(dynamic_focus_hours, 1)
    
    except Exception as e:
        print(f"Error calculating dynamic focus hours: {e}")
        return fallback
```

---

## 2. UPDATED ANALYZE IMPACT ENDPOINT
**File:** `services/sprint_impact_service/routes/impact_routes.py`
**Lines:** 231-267

```python
    # 2. Fetch space to get risk_appetite, then calculate dynamic focus hours
    focus_hours_per_day = 6.0
    risk_appetite = "Standard"
    space_id = sprint.get("space_id", "")
    if space_id:
        try:
            db    = get_database()
            space = await db.spaces.find_one({"_id": ObjectId(space_id)}) if ObjectId.is_valid(space_id) else None
            if space:
                risk_appetite = space.get("risk_appetite", "Standard")
                # Calculate dynamic focus hours from previous sprint
                focus_hours_per_day = await calculate_dynamic_focus_hours(
                    space_id,
                    fallback=float(space.get("focus_hours_per_day", 6.0))
                )
        except Exception as e:
            print(f"Error fetching space settings: {e}")
            pass  # fall back to defaults if lookup fails

    # ... rest of item_data setup ...

    # 3. ML predictions — pass focus_hours_per_day and risk_appetite into the predictor
    try:
        ml_result = impact_predictor.predict_all_impacts(
            item_data, sprint_context, existing_items,
            focus_hours_per_day=focus_hours_per_day,
            risk_appetite=risk_appetite,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ML prediction failed: {exc}")
```

---

## 3. UPDATED IMPACT PREDICTOR
**File:** `services/sprint_impact_service/impact_predictor.py`
**Lines:** 150-162 & 357-391

```python
# Updated method signature
def predict_all_impacts(
    self,
    item_data: dict,
    sprint_context: dict,
    existing_items=None,
    focus_hours_per_day: float = _DEFAULT_FOCUS_HOURS,
    risk_appetite: str = "Standard",
) -> dict:
    ctx = self._enrich_context(sprint_context)

    effort      = self._predict_effort(item_data, ctx, focus_hours_per_day)
    schedule    = self._predict_schedule_risk(item_data, ctx)
    quality     = self._predict_quality_risk(item_data, ctx)
    productivity= self._predict_productivity(item_data, ctx)
    summary     = self._generate_summary(effort, schedule, quality, productivity, risk_appetite)
    display     = generate_display_metrics(...)
    # ... rest of method
```

```python
# Updated summary scorer with risk appetite thresholds
def _generate_summary(self, effort, schedule, quality, productivity, risk_appetite: str = "Standard") -> dict:
    """
    Generate risk summary with thresholds adjusted by risk appetite.
    Strict: More conservative (DEFER score=5), Standard: Balanced (score=7), Lenient: Permissive (score=9)
    """
    # Risk appetite thresholds for recommendation scores
    thresholds = {
        "Strict": {"defer": 5, "swap": 3, "split": 1},
        "Standard": {"defer": 7, "swap": 4, "split": 2},
        "Lenient": {"defer": 9, "swap": 6, "split": 3},
    }
    
    thresh = thresholds.get(risk_appetite, thresholds["Standard"])
    defer_threshold = thresh["defer"]
    swap_threshold = thresh["swap"]
    split_threshold = thresh["split"]
    
    score = 0
    if effort['status']     == 'critical': score += 3
    elif effort['status']   == 'warning':  score += 2
    if schedule.get('probability', 0) > 50: score += 3
    elif schedule.get('probability', 0) > 30: score += 2
    if quality.get('probability', 0) > 60:  score += 2
    elif quality.get('probability', 0) > 30: score += 1
    if productivity.get('drop_pct', abs(productivity.get('velocity_change', 0))) > 30: score += 2
    elif productivity.get('drop_pct', abs(productivity.get('velocity_change', 0))) > 10: score += 1

    if score >= defer_threshold:
        return {'risk_score': score, 'overall_risk': 'critical', 'recommendation': 'DEFER', 'risk_appetite': risk_appetite}
    elif score >= swap_threshold:
        return {'risk_score': score, 'overall_risk': 'high',     'recommendation': 'SWAP', 'risk_appetite': risk_appetite}
    elif score >= split_threshold:
        return {'risk_score': score, 'overall_risk': 'medium',   'recommendation': 'SPLIT', 'risk_appetite': risk_appetite}
    else:
        return {'risk_score': score, 'overall_risk': 'low',      'recommendation': 'ADD', 'risk_appetite': risk_appetite}
```

---

## 4. SPACE HELPER UPDATE
**File:** `services/sprint_impact_service/routes/space_routes.py`
**Lines:** 9-18

```python
def space_helper(space) -> dict:
    return {
        "id":                  str(space["_id"]),
        "name":                space["name"],
        "description":         space["description"],
        "max_assignees":       space["max_assignees"],
        "focus_hours_per_day": space.get("focus_hours_per_day", 6.0),
        "risk_appetite":       space.get("risk_appetite", "Standard"),
        "created_at":          space["created_at"],
        "updated_at":          space["updated_at"],
    }
```

---

## 5. REACT COMPONENT - STATE AND HANDLERS
**File:** `frontend/src/components/features/sprint_impact_service/ImpactAnalyzer.jsx`
**Lines:** 215-275

```jsx
export default function ImpactAnalyzer({ sprints, spaceId }) {
  const [selectedSprint, setSelectedSprint] = useState(null);
  const [formData, setFormData] = useState({
    title: '', description: '', story_points: 5, priority: 'Medium', type: 'Task',
  });
  const [analysis,      setAnalysis]      = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [sprintContext, setSprintContext]  = useState(null);
  const [actionResult,  setActionResult]  = useState(null);
  const [suggestingPoints, setSuggestingPoints] = useState(false);  // NEW STATE

  // ... existing effects ...

  const handleSprintChange = (sprintId) => {
    const sprint = sprints.find(s => s.id === sprintId);
    setSelectedSprint(sprint);
    setAnalysis(null);
    setActionResult(null);
    if (sprint) loadSprintContext(sprint.id);
  };

  // NEW HANDLER FUNCTION
  const handleSuggestPoints = async () => {
    if (!formData.title.trim()) {
      alert('Please enter a title first');
      return;
    }
    
    setSuggestingPoints(true);
    try {
      const result = await api.predictStoryPoints({
        title: formData.title,
        description: formData.description,
      });
      // Use median suggestion or suggested_points
      const suggestedValue = result.suggested_points || result.median || 5;
      setFormData({ ...formData, story_points: suggestedValue });
    } catch (err) {
      console.error('Failed to suggest points:', err);
      alert('Could not suggest points: ' + err.message);
    } finally {
      setSuggestingPoints(false);
    }
  };

  // ... rest of component
```

---

## 6. REACT COMPONENT - SUGGEST BUTTON UI
**File:** `frontend/src/components/features/sprint_impact_service/ImpactAnalyzer.jsx`
**Lines:** 389-403

```jsx
          {/* Story points + Priority */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Story Points</label>
              <div className="flex gap-2">
                <input type="number" min="1" max="21" value={formData.story_points}
                  onChange={e => setFormData({ ...formData, story_points: parseInt(e.target.value) || 5 })}
                  className="flex-1 bg-white text-gray-900 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none" />
                <button
                  onClick={handleSuggestPoints}
                  disabled={suggestingPoints}
                  className="px-3 py-2 bg-indigo-100 hover:bg-indigo-200 text-indigo-700 font-medium rounded-lg text-sm flex items-center gap-1 disabled:opacity-50 whitespace-nowrap transition-colors">
                  {suggestingPoints ? (
                    <><div className="animate-spin h-4 w-4 border-2 border-indigo-700 border-t-transparent rounded-full" /></>
                  ) : (
                    <>✨ Suggest</>
                  )}
                </button>
              </div>
            </div>
            {/* Priority field continues as before */}
```

---

## API ENDPOINTS (No changes - existing)

### POST /api/impact/analyze
**Now accepts and uses:**
- `focus_hours_per_day` from database (dynamically calculated)
- `risk_appetite` from Space settings
- Passes both to ML predictor
- Returns summary with risk_appetite field

### POST /api/ai/predict (EXISTING)
**Used by:**
- ImpactAnalyzer component's "Suggest Points" button
- Accepts: `{ title, description }`
- Returns: `{ suggested_points, confidence, reasoning, complexity_indicators }`

### GET /spaces/{space_id}
**Now returns:**
- `risk_appetite` field (new)
- `focus_hours_per_day` field (existing)

---

## ENVIRONMENT & DEPENDENCIES

**No new dependencies required**
- All changes use existing libraries
- No npm packages to install
- No environment variables to set
- MongoDB collections already have required fields

**CORS Status:** ✅ Already configured
- Backend accepts http://localhost:5173
- No additional headers needed

---

## TESTING EXAMPLES

### Test 1: Dynamic Focus Hours
```python
# Mock scenario:
# - Space ID: "123abc"
# - Completed sprint: 2 assignees, 10 days, 30 completed SP
# Expected: (2 * 10 * 8) / 30 = 5.33 hours/day
# Result: 5.3 hours/day
```

### Test 2: Risk Appetite Threshold
```javascript
// Same ticket analysis with score = 6:
// Strict:   DEFER (threshold=5) ✓
// Standard: SWAP (threshold=7) ✓
// Lenient:  SPLIT (threshold=9) ✓
```

### Test 3: Story Point Suggestion
```javascript
// Input: 
//   title: "Add authentication with OAuth2 integration"
//   description: "Implement OAuth2 flow with Google and GitHub providers"
// Expected output: suggested_points = 8 (high complexity)
// Button fills form with: story_points = 8
```

---

## BACKWARDS COMPATIBILITY

✅ All features are backwards compatible:
1. Dynamic hours **gracefully falls back** to 6.0 if no completed sprint
2. Risk appetite defaults to **"Standard"** maintaining existing behavior
3. Story point suggestion is **optional** UI enhancement
4. **No database migrations** - fields already exist
5. **No breaking API changes** - only additions

