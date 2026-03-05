# Sprint Velocity & Capacity Logic - Agile Replanning System

## Overview

Sprint capacity and velocity are fundamental metrics in Agile planning. This document explains how they are calculated, why they matter, and how the system uses them for intelligent replanning.

---

## 1. Core Definitions

### Sprint Capacity
**Definition:** The total number of story points a team commits to complete in a sprint.

**Example:**
- Team commits to complete **25 SP** in a 2-week sprint
- This is the planned work

### Velocity
**Definition:** The actual number of story points the team completes in a sprint.

**Example:**
- Team planned 25 SP but only completed 22 SP
- **Velocity = 22 SP**
- **Completion Rate = 22/25 = 88%**

### Sprint Spillover
**Definition:** Story points planned but not completed, carrying over to the next sprint.

**Example:**
- Sprint 2: Planned 30 SP, Completed 22 SP
- **Spillover = 30 - 22 = 8 SP** (moved to next sprint)

---

## 2. How Velocity is Calculated

### Multi-Sprint Average Velocity (Recommended)

**Formula:**
```
Average Velocity = (Sprint1_Completed + Sprint2_Completed + Sprint3_Completed) / Number_of_Sprints
```

**Real Example from Golden Dataset:**

```
Sprint 1 (Foundation & Auth):    25 SP planned → 25 SP completed ✓
Sprint 2 (User Profiles):         30 SP planned → 22 SP completed ✗ (8 SP spillover)
Sprint 3 (Security Audit):        20 SP planned → 20 SP completed ✓

Average Velocity = (25 + 22 + 20) / 3 = 22.33 SP per sprint
```

### Why Use Average?
- **Smooths out anomalies:** Single sprint might be skewed by emergencies or scope changes
- **Accounts for team variability:** Some sprints are more productive (holidays, training, etc.)
- **Better planning:** Using 3+ sprints provides a realistic baseline

### Initial Sprint (Sprint 4) - No History Yet

For the very first sprint when there's no historical data:

**Option 1: Team Estimation**
- Team estimates based on experience
- Common: 6-8 hours per person per day × team size × sprint days
- Example: 5 people × 6 hours/day × 10 working days = 300 hours available

**Option 2: Industry Baseline**
- Typical: 20-30 SP per sprint for small teams
- Adjust based on team size and complexity

**Option 3: Conservative Estimate**
- Use 80% of optimistic estimate to account for meetings, support work
- Safer than overcommitting

---

## 3. Work Hours Per Person Per Day

### Calculation Formula

```
Available Hours Per Person Per Day = (Total Team Hours / Number of People) / Sprint Duration Days
```

**Real Example:**

```
Scenario: 5-person team, 2-week (10 working days) sprint

Step 1: Assume 8 hours/day work capacity (industry standard)
Step 2: Reduce by 25% for meetings/admin = 6 hours/day focused work
Step 3: Calculate per person = 6 hours/day (consistent across team)

OR

Alternative calculation:
- 5 people × 6 hours/day × 10 days = 300 hours available per sprint
- If committed 22 SP average velocity
- Hours per SP = 300 / 22 = 13.6 hours per story point
```

### Key Variables

| Variable | Typical Value | Notes |
|----------|---------------|-------|
| Work Day | 8 hours | Standard workday |
| Focused Work | 6 hours | After meetings (25% overhead) |
| Sprint Days | 10 | 2 weeks minus weekends |
| Team Size | 3-8 people | Varies by organization |

---

## 4. How the System Calculates Capacity for Sprint 4

### Golden Dataset Example

**Sprint 1-3 Historical Data:**
```
Average Velocity = 22.33 SP
Team Size = 5 people (inferred from capacity)
Sprint Duration = 2 weeks (14 calendar days, 10 working days)
Hours per Person per Day = 6 hours (standard)
```

**Capacity Calculation for Sprint 4:**
```
Total Hours Available = 5 people × 6 hours × 10 days = 300 hours
Estimated Capacity = Average Velocity = 22.33 SP

Using historical velocity as baseline:
- If 22.33 SP consumed 300 hours in past sprints
- Then Sprint 4 should commit to 22-25 SP

Actual Sprint 4: 30 SP committed
Free Capacity = 30 - 24 (current) = 6 SP remaining
```

---

## 5. The Spillover Problem (Sprint 2 Pattern)

### Scenario
Sprint 2 had **flatline burndown:**
- First 6 days: Burn 14 SP (good pace)
- Last 8 days: NO PROGRESS (blocked/stuck)
- Final result: 8 SP unfinished

### Why This Happens
- Unexpected bugs discovered mid-sprint
- Dependencies blocked by other teams
- Underestimated complexity
- Team distracted by emergencies

### Impact on Next Sprint
- 8 SP spillover into Sprint 3
- Reduces capacity for new work
- Impacts velocity metrics
- Alert: System flags "high risk items"

---

## 6. Dynamic Capacity Adjustment

### Rule: How Much Can Sprint 4 Actually Take?

```
Recommended Capacity = Average Velocity (with buffer)

Sprint 4 Calculation:
- Historical Average = 22.33 SP
- Buffer Recommendation = 85-90% of average (conservative)
- Safe Capacity = 22.33 × 0.90 = 20 SP

Aggressive Capacity:
- Historical Average = 22.33 SP
- High confidence = 100% of average
- Aggressive Capacity = 22.33 SP

Actual Golden Dataset:
- Committed Capacity = 30 SP
- This is 134% of historical average (RISKY!)
- Result: Already 24/30 filled (80% utilization)
```

### Recommendations Based on Spillover History

| Scenario | Velocity | Recommendation | Confidence |
|----------|----------|-----------------|-----------|
| 100% completion all sprints | 25 SP avg | Can commit 25-27 SP | High |
| Some spillover (75-85%) | 22 SP avg | Commit 20-22 SP | Medium |
| Frequent spillover | 18 SP avg | Commit 15-18 SP | Low |
| First sprint, no data | N/A | Team estimate | Variable |

---

## 7. System Integration - How Impact Analyzer Uses This

### Velocity Chart
- **Displays:** Historical velocity trend over 3+ sprints
- **Purpose:** Show team capacity trends
- **Algorithm:**
  ```
  For each completed sprint:
    Completed = sum(items with status='Done')
    Planned = sum(all items)
    Velocity = Completed
    Plot: (Sprint_Date, Velocity)
  ```

### Burndown Chart
- **Displays:** Daily progress within a sprint
- **Purpose:** Identify mid-sprint risks
- **Red Flag:** Flatline pattern (like Sprint 2)

### Capacity Calculation
- **Uses:** Average of last 3 completed sprints
- **Formula:** `Capacity = avg(Sprint1, Sprint2, Sprint3)`
- **Applied to:** Sprint 4 planning

### Spillover Detection
- **Identifies:** Items not finished in their sprint
- **Impact:** Reduces available capacity for new work
- **Alert:** "X SP still in progress - plan accordingly"

---

## 8. Golden Dataset Breakdown

### Historical Backlog Items (13 total)

**Sprint 1: Foundation & Auth**
```
5 items × 5 SP each = 25 SP total
Status: ALL DONE ✓
Velocity: 25 SP (100% completion)

Items:
  1. Setup User Database Schema (5 SP)
  2. Create Login API Endpoint (5 SP)
  3. Implement User Registration Flow (5 SP)
  4. Setup Authentication Middleware (5 SP)
  5. Create User Profile Endpoint (5 SP)
```

**Sprint 2: User Profiles**
```
Total Planned: 30 SP
6 items total:
  
  Done (22 SP):
  1. Create User Profile Frontend (8 SP)
  2. Implement Profile Update API (5 SP)
  3. Add Profile Picture Upload (5 SP)
  4. Setup User Avatar Caching (4 SP)
  
  Unfinished (8 SP):
  5. Implement User Preferences System (5 SP) - In Progress
  6. Add Profile Analytics Dashboard (3 SP) - To Do

Velocity: 22 SP (73% completion)
Spillover: 8 SP
Pattern: FLATLINE (shows risk)
```

**Sprint 3: Security Audit**
```
4 items × 5 SP each = 20 SP total
Status: ALL DONE ✓
Velocity: 20 SP (100% completion)

Items:
  1. Audit Authentication Security (5 SP)
  2. Implement HTTPS and TLS (5 SP)
  3. Add Input Validation & Sanitization (5 SP)
  4. Setup Security Logging (5 SP)
```

**Sprint 4: Stripe Integration (ACTIVE)**
```
Committed Capacity: 30 SP
Current Allocation: 24 SP
Free Capacity: 6 SP remaining

4 items currently:
  1. Setup Stripe account and API keys (5 SP) - In Progress
  2. Implement Stripe payment form component (8 SP) - To Do
  3. Create payment processing API endpoint (8 SP) - To Do
  4. Integrate webhook handling for payment events (3 SP) - To Do
```

---

## 9. Real-World Application

### Scenario: Adding New Items to Sprint 4

**Can we add Item A (5 SP)?**
```
Current: 24 SP
Remaining: 6 SP
Item A: 5 SP

✓ YES! Fits in free capacity
New Total: 29/30 SP (97% utilization)
```

**Can we add Item C (13 SP)?**
```
Current: 24 SP
Remaining: 6 SP
Item C: 13 SP

✗ NO! Exceeds capacity by 7 SP
Recommendation: 
  - SPLIT item into smaller pieces (SPLIT rule)
  - OR DEFER to Sprint 5
```

**Can we add Item B (8 SP Critical bug)?**
```
Current: 24 SP
Remaining: 6 SP
Item B: 8 SP (Critical)

⚠ BLOCKED! Needs capacity
Action:
  - SWAP: Remove lower-priority item from sprint
  - ADD: Item B replaces something else
  - Result: Move lower-priority work to backlog
```

---

## 10. Key Takeaways

### For Sprint Capacity:
1. **Use historical average:** Most reliable for established teams
2. **Buffer for risk:** Add 15-20% buffer for unknowns
3. **Track spillover:** Identify patterns and adjust
4. **First sprint:** Use team estimation + industry baseline

### For Velocity:
1. **Calculate average:** Not single sprint
2. **Track trends:** Are teams getting faster or slower?
3. **Identify patterns:** Flatlines indicate risk
4. **Plan conservatively:** Use 85-90% of average for capacity

### For Work Hours:
1. **6 hours/day:** Most realistic (not 8)
2. **Varies by role:** Managers ≠ Developers
3. **Include overhead:** Meetings, support, admin work
4. **Team size matters:** Large teams = more coordination overhead

---

## 11. System Configuration (Golden Dataset)

```python
# Team Parameters
TEAM_SIZE = 5
HOURS_PER_DAY = 6.0  # Focused work time
SPRINT_DURATION_DAYS = 10  # 2 weeks minus weekends

# Historical Velocity
SPRINT_1_VELOCITY = 25 SP
SPRINT_2_VELOCITY = 22 SP
SPRINT_3_VELOCITY = 20 SP
AVERAGE_VELOCITY = 22.33 SP

# Sprint 4 Capacity
COMMITTED_CAPACITY = 30 SP
CURRENT_ALLOCATION = 24 SP
FREE_CAPACITY = 6 SP
UTILIZATION = 80%
```

---

## Documentation Summary

This explains **how velocity establishes the baseline for sprint capacity**, especially the critical difference between:

- **Initial Sprint:** Team estimates + experience
- **Subsequent Sprints:** Historical average velocity
- **Sprint 2 Pattern:** Demonstrates how spillover impacts metrics
- **System Logic:** How ADD, SWAP, SPLIT rules use capacity constraints

The Golden Dataset seeds all 13 historical items so your impact analyzer can calculate real velocity metrics!
