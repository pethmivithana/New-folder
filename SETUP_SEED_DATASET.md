# How to Seed the Complex Dataset

## Overview
The `seed_complex_dataset.py` script will:
1. **Clear all existing data** from MongoDB (spaces, sprints, backlog items)
2. **Load MongoDB URI from .env.project** environment file
3. **Seed the complete Cloud-Native Microservices Platform dataset**
   - 1 Space (project)
   - 6 Sprints (5 completed, 1 active)
   - 53+ Backlog items with realistic technical descriptions

## Prerequisites

Before running the seed script, ensure:

✅ **Python 3.8+** is installed
✅ **MongoDB Atlas** cluster is running
✅ **MONGODB_URI** is set in `/vercel/share/.env.project`
✅ **Required packages** are installed

## Installation & Setup

### 1. Install Required Packages

```bash
cd /vercel/share/v0-project/services/sprint_impact_service
pip install pymongo python-dotenv
```

### 2. Verify MongoDB URI in .env

Check that your `/vercel/share/.env.project` contains:

```bash
MONGODB_URI='mongodb+srv://your-username:your-password@your-cluster.mongodb.net/agile-tool'
```

The script reads from this environment variable automatically.

## Running the Seed Script

### Option 1: Direct Execution (Recommended)

```bash
cd /vercel/share/v0-project/services/sprint_impact_service
python seed_complex_dataset.py
```

### Option 2: With Environment File Explicitly

If the environment variables aren't auto-loaded:

```bash
cd /vercel/share/v0-project/services/sprint_impact_service
python -c "from dotenv import load_dotenv; load_dotenv('/vercel/share/.env.project'); import seed_complex_dataset; seed_complex_dataset.main()"
```

### Option 3: From Project Root

```bash
cd /vercel/share/v0-project
python services/sprint_impact_service/seed_complex_dataset.py
```

## What Gets Cleared & Seeded

### Data Cleared
When you run the script, these MongoDB collections are **completely deleted**:
- `db.spaces` - all spaces/projects
- `db.sprints` - all sprints
- `db.backlog_items` - all backlog items

### Data Seeded

**1 Space Created:**
- Name: Cloud-Native Microservices Platform
- Team Size: 8 developers
- Average Velocity: 45 SP

**6 Sprints Created:**
| Sprint | Name | Status | Dates | Completion |
|--------|------|--------|-------|-----------|
| Sprint 1 | Foundation & Docker Containerization | Completed | Mar 17-31, 2026 | 93% |
| Sprint 2 | Istio Service Mesh & Distributed Tracing | Completed | Apr 1-15, 2026 | 96% |
| Sprint 3 | PostgreSQL Sharding & Apache Kafka Integration | Completed | Apr 16-30, 2026 | 94% |
| Sprint 4 | Kong API Gateway & Advanced Rate Limiting | Completed (Poor) | May 1-8, 2026 | 78% |
| Sprint 5 | Prometheus Metrics & Horizontal Pod Autoscaling | Completed | Apr 9-23, 2026 | 91% |
| **Sprint 6** | **Cost Optimization & Security Hardening** | **ACTIVE** | **Apr 27-May 11, 2026** | **In Progress (50%)** |

**53+ Backlog Items**
- Real technical descriptions (Docker, Kubernetes, Istio, Kafka, PostgreSQL, etc.)
- Mix of completed, in-progress, and todo items
- Story points: 3-13 SP
- Assigned to team members

## Expected Output

When you run the script, you should see:

```
🌱 Seeding Complex Dataset: Cloud-Native Microservices Platform

✓ Cleared existing data from all collections
  - Deleted all spaces
  - Deleted all sprints
  - Deleted all backlog items
✓ Created space: Cloud-Native Microservices Platform
✓ Created 6 sprints
✓ Created 53 backlog items across 6 sprints

✅ Dataset seeded successfully!
   Space: Cloud-Native Microservices Platform
   Sprints: 6 (5 completed, 1 active)
   Backlog Items: 53 total
   Total Story Points: 311 SP
   Active Sprint (Sprint 6): April 27 - May 11, 2026 (Currently mid-sprint)

🚀 Dataset ready for sprint impact prediction testing!
```

## Troubleshooting

### Error: "MONGODB_URI not found"
**Solution:** Verify `/vercel/share/.env.project` contains the MongoDB connection string:
```bash
cat /vercel/share/.env.project | grep MONGODB_URI
```

### Error: "Connection refused"
**Solution:** Ensure MongoDB Atlas cluster is active and IP whitelist includes your server IP

### Error: "pymongo not installed"
**Solution:** Install dependencies:
```bash
pip install pymongo python-dotenv
```

### Error: "Authentication failed"
**Solution:** Verify MongoDB credentials in MONGODB_URI are correct

## Key Features of the Dataset

✅ **Realistic Technical Content**
- Kubernetes, Docker, Istio, Kafka, PostgreSQL sharding
- Cloud-native architecture patterns
- Real sprint goals and technical descriptions

✅ **Active Sprint in Progress**
- Sprint 6 is currently mid-sprint (7 days elapsed, 7 days remaining)
- Contains both completed and in-progress items
- Perfect for testing sprint impact predictions

✅ **Complete Project Lifecycle**
- Past sprints show team velocity trends
- Sprint 4 (poorly completed) tests edge cases
- Active sprint validates prediction accuracy

✅ **ML Testing Ready**
- Diverse backlog items test feature engineering
- Multiple story point sizes test effort predictions
- Sprint goal alignment can be validated
- Risk predictions can be compared

## Clearing Data Manually (If Needed)

If you only want to clear data without reseeding:

```python
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv("/vercel/share/.env.project")
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["agile-tool"]

# Clear all collections
db.spaces.delete_many({})
db.sprints.delete_many({})
db.backlog_items.delete_many({})
print("Data cleared successfully")
```

## Next Steps

After seeding the dataset:

1. **Verify in MongoDB Atlas:**
   - Log into MongoDB Atlas console
   - Check `agile-tool` database
   - Confirm spaces, sprints, backlog_items collections exist

2. **Test ML Models:**
   - Run the sprint impact prediction service
   - Add new backlog items to Sprint 6
   - Verify effort, risk, and productivity predictions

3. **Test Sprint Goal Alignment:**
   - Add items matching Sprint 6 goal: "Cost Optimization & Security Hardening"
   - Verify alignment scores are high for matching items

4. **Run Full Pipeline:**
   - Backend: Flask/FastAPI service processes predictions
   - Frontend: View sprint impact cards and recommendations

## File Locations

| File | Location |
|------|----------|
| Seed Script | `/vercel/share/v0-project/services/sprint_impact_service/seed_complex_dataset.py` |
| Environment | `/vercel/share/.env.project` |
| Database | MongoDB Atlas (Cloud) |
| Database Name | `agile-tool` |

---

**Last Updated:** May 4, 2026
**Dataset Version:** Complex v2.0 (Current Dates)
**Status:** Ready for Viva Testing
