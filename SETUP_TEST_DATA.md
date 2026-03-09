# Test Data Setup Guide

## Quick Start (3 minutes)

### Step 1: Ensure Backend is Running
```bash
# Terminal 1
cd services/sprint_impact_service
python main.py
```

Expected output:
```
Uvicorn running on http://0.0.0.0:8000
Connected to MongoDB
```

### Step 2: Populate Test Data
```bash
# Terminal 2 (new terminal)
cd services/sprint_impact_service
python test_data.py
```

Expected output:
```
✓ Connected to MongoDB
✓ Cleared existing data
✓ Creating spaces...
✓ E-Commerce Platform Enhancement
✓ Real-Time Analytics Dashboard

✓ Populating E-Commerce Platform sprints...
  ✓ Sprint 1: Payment Gateway Integration (6 items)
  ✓ Sprint 2: Inventory Management System (5 items)
  ✓ Sprint 3: User Recommendation Engine (5 items)
  ✓ Sprint 4: Mobile App Optimization (5 items)
  ✓ Sprint 5: Cart and Checkout Improvements (6 items)

✓ Populating Analytics Dashboard sprints...
  ✓ Sprint 1: Data Aggregation Pipeline (5 items)
  ✓ Sprint 2: Real-Time Dashboard Backend (5 items)
  ✓ Sprint 3: Frontend Dashboard UI (5 items)
  ✓ Sprint 4: Alerting and Notifications (5 items)
  ✓ Sprint 6: Custom Reports and Exports (6 items)

============================================================
TEST DATA POPULATION COMPLETE
============================================================
Spaces created: 2
Sprints created: 9
Backlog items created: 47

Spaces:
  1. E-Commerce Platform Enhancement
  2. Real-Time Analytics Dashboard
============================================================
```

### Step 3: Start Frontend
```bash
# Terminal 3 (new terminal)
cd frontend
npm run dev
```

Open browser: http://localhost:3000 (or shown port)

---

## What's in the Test Data

### Space 1: E-Commerce Platform Enhancement
- **Context**: Building and enhancing e-commerce platform
- **Team**: 8 people max
- **Focus Hours/Day**: 6.5 hours
- **Sprints**: 5 (4 completed, 1 active)

#### Completed Sprints
1. **Sprint 1**: Payment Gateway Integration (44 SP)
   - 6 items (all DONE)
   - Stripe & PayPal integration
   
2. **Sprint 2**: Inventory Management System (48 SP)
   - 5 items (all DONE)
   - Real-time stock tracking
   
3. **Sprint 3**: User Recommendation Engine (46 SP)
   - 5 items (all DONE)
   - AI-powered recommendations
   
4. **Sprint 4**: Mobile App Optimization (44 SP)
   - 5 items (all DONE)
   - Performance improvements

#### Active Sprint
5. **Sprint 5**: Cart and Checkout Improvements (50 SP target)
   - 6 items in various states:
     - 14 SP DONE
     - 13 SP IN REVIEW
     - 8 SP IN PROGRESS
     - 10 SP TO DO
   - Days Remaining: 7 days
   - Status: Mid-sprint

### Space 2: Real-Time Analytics Dashboard
- **Context**: Analytics and data visualization platform
- **Team**: 6 people max
- **Focus Hours/Day**: 7.0 hours
- **Sprints**: 5 (4 completed, 1 active)

#### Completed Sprints
1. **Sprint 1**: Data Aggregation Pipeline (46 SP)
   - 5 items (all DONE)
   - Kafka, Spark pipeline setup
   
2. **Sprint 2**: Real-Time Dashboard Backend (46 SP)
   - 5 items (all DONE)
   - WebSocket API for metrics
   
3. **Sprint 3**: Frontend Dashboard UI (44 SP)
   - 5 items (all DONE)
   - React components, charts
   
4. **Sprint 4**: Alerting and Notifications (50 SP)
   - 5 items (all DONE)
   - Alert rules and ML anomaly detection

#### Active Sprint
5. **Sprint 6**: Custom Reports and Exports (50 SP target)
   - 6 items in various states:
     - 11 SP DONE
     - 8 SP IN REVIEW
     - 5 SP IN PROGRESS
     - 10 SP TO DO
     - 3 SP (bug, high priority) DONE
   - Days Remaining: 7 days
   - Status: Mid-sprint

---

## Data Consistency Checks

After running test_data.py, verify:

### MongoDB Query 1: Count Spaces
```javascript
// In MongoDB Compass or mongosh
db.spaces.countDocuments()
// Expected: 2
```

### MongoDB Query 2: Count Sprints
```javascript
db.sprints.countDocuments()
// Expected: 9
```

### MongoDB Query 3: Count Items
```javascript
db.backlog_items.countDocuments()
// Expected: 47
```

### MongoDB Query 4: Verify Active Sprints
```javascript
db.sprints.find({status: "Active"})
// Expected: 2 documents (one per space)
```

### MongoDB Query 5: Check Sprint Statuses
```javascript
db.sprints.aggregate([
  { $group: { _id: "$status", count: { $sum: 1 } } }
])
// Expected:
// { _id: "Completed", count: 8 }
// { _id: "Active", count: 1 }
```

---

## Verifying in Application

### Check 1: View Both Spaces
1. Open http://localhost:3000
2. Should see "E-Commerce Platform Enhancement" and "Real-Time Analytics Dashboard" in spaces list
3. Click each space → should load successfully

### Check 2: View Completed Sprints
1. In E-Commerce space, click "View Analytics"
2. Should see 4 completed sprints with:
   - Burndown charts showing completion
   - Velocity trend (should be around 44-48 SP per sprint)
   - Team members in assignees

### Check 3: View Active Sprint
1. Click "Start New Sprint" or select active sprint
2. Should show "Sprint 5: Cart and Checkout Improvements" as ACTIVE
3. Visible items: 6 items with states
   - 14 SP in DONE
   - 13 SP in IN REVIEW
   - 8 SP in IN PROGRESS
   - 10 SP in TO DO
4. Capacity bar shows progress

### Check 4: Test ML Features
1. In active sprint, click "Add Task"
2. Enter task title and description
3. Click "AI Suggest Points" → should get suggestion
4. Click "Analyze Impact" → should see 4 risk cards
5. System should show recommendation (ADD/DEFER/SWAP)

### Check 5: Velocity Visualization
1. View space analytics
2. Velocity chart shows 4+ sprints
3. X-axis: Sprint names
4. Y-axis: Completed SP (44-50 range)
5. Should show trend (steady or improving)

---

## Troubleshooting

### Issue: "Connected to MongoDB" not shown
**Solution**:
- Verify MONGODB_URI is set in .env
- Check MongoDB Atlas credentials
- Ensure database "agile-tool" exists

### Issue: test_data.py script errors
**Solution**:
```bash
# Check Python dependencies
pip install -r requirements.txt

# Or run with error output
python test_data.py --verbose
```

### Issue: Data not appearing in app
**Solution**:
1. Restart backend (Ctrl+C, then python main.py)
2. Refresh browser (Ctrl+F5)
3. Check MongoDB: `db.spaces.countDocuments()`

### Issue: Only 1 space visible
**Solution**:
- Run test_data.py again
- Check for errors in MongoDB connection
- Verify database name is correct

### Issue: Items all marked DONE in active sprint
**Solution**:
- Correct - active sprint is mid-progress
- Some items are intentionally in TO DO state
- Check item statuses: DONE, IN REVIEW, IN PROGRESS, TO DO

---

## Detailed Data Breakdown

### Data by Project

#### E-Commerce Platform
```
Total Completed SP: 182 (4 sprints)
Average per Sprint: 45.5 SP
Team Pace: ~3.25 SP/day
Hours per SP: ~2.46 hours (high team efficiency)

Completed Sprints Distribution:
- Sprint 1: 44 SP - Payment integration
- Sprint 2: 48 SP - Inventory system
- Sprint 3: 46 SP - Recommendations
- Sprint 4: 44 SP - Mobile optimization

Active Sprint: 50 SP target
- Progress: 22 SP (44%)
- Remaining: 28 SP
- Days left: 7
- On track for 28 SP more = 56 SP total
```

#### Analytics Dashboard
```
Total Completed SP: 186 (4 sprints)
Average per Sprint: 46.5 SP
Team Pace: ~3.32 SP/day
Hours per SP: ~2.41 hours (high team efficiency)

Completed Sprints Distribution:
- Sprint 1: 46 SP - Data pipeline
- Sprint 2: 46 SP - Backend API
- Sprint 3: 44 SP - Frontend UI
- Sprint 4: 50 SP - Alerting system

Active Sprint: 50 SP target
- Progress: 19 SP (38%)
- Remaining: 31 SP
- Days left: 7
- Needs ~4.4 SP/day to finish
```

---

## Using Test Data for Demonstrations

### For Velocity Chart Demo
- Navigate to Space → Analytics → Velocity Chart
- Shows: Sprint 1-4 with 44-50 SP completed each
- Demonstrates: Consistent team productivity

### For Burndown Chart Demo
- Select completed sprint → View Details → Burndown
- Shows: Items completed over sprint duration
- Demonstrates: Sprint progress tracking

### For Story Point Suggestion Demo
- Open active sprint → Add new task
- Fill in realistic task description
- Click "AI Suggest" → Get 8-15 SP
- Demonstrates: ML estimation works

### For Impact Analysis Demo
- Use one of the incomplete tasks in active sprint
- Click "Analyze Impact"
- See 4 risk cards with realistic values
- Demonstrates: Risk assessment

### For Recommendation Engine Demo
- Test 4 scenarios:
  1. Add low-effort, aligned task (expect ADD)
  2. Add large task late in sprint (expect SPLIT)
  3. Add misaligned task (expect DEFER)
  4. Sprint full, add high-priority (expect SWAP)

---

## Next Steps After Setup

1. **Review Test Data**: Navigate through both spaces, examine sprints and items
2. **Run Through Scenarios**: Use VIVA_DEMONSTRATION_GUIDE.md test cases
3. **Validate Features**: Check all 10 features from validation checklist
4. **Prepare Q&A**: Review common questions in demonstration guide
5. **Ready for Viva**: You're now prepared to demonstrate the system

---

## Quick Reference: Actual Story Points in Test Data

### High Complexity (13 SP)
- "Implement Stripe API integration"
- "Build metric calculation engine"
- "Develop recommendation algorithm"
- "Implement one-click checkout"
- "Design alert rule engine"

### Medium Complexity (8-10 SP)
- "Design payment architecture"
- "Add PayPal payment support"
- "Add low stock alert system"
- "Design real-time metrics architecture"
- Most Story type items

### Lower Complexity (3-5 SP)
- Bug fixes
- Simple tasks
- Configuration tasks

This distribution (3-13 range, mostly 5-10) is realistic for enterprise software projects.

---

**Ready to demonstrate? Check your MongoDB and run test_data.py!**
