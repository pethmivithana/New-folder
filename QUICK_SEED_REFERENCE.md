# Quick Seed Reference

## One-Command Setup

```bash
cd /vercel/share/v0-project/services/sprint_impact_service && python seed_complex_dataset.py
```

## What Happens

1. ✅ **Clears ALL previous data** from MongoDB
   - Deletes all spaces
   - Deletes all sprints
   - Deletes all backlog items

2. ✅ **Loads MongoDB URI from .env**
   ```
   /vercel/share/.env.project → MONGODB_URI
   ```

3. ✅ **Seeds Complete Dataset**
   - 1 Space (Cloud-Native Microservices Platform)
   - 6 Sprints (5 completed + 1 active)
   - 53+ Backlog items with real technical descriptions
   - Connected to MongoDB Atlas database: `agile-tool`

## Database Name
```
"agile-tool"  ← This is the database name in MongoDB
```

NOT `sprint_impact_db`

## Collections Created

| Collection | Records | Status |
|-----------|---------|--------|
| spaces | 1 | ✅ |
| sprints | 6 | ✅ |
| backlog_items | 53+ | ✅ |

## Active Sprint Info

**Sprint 6 - Cost Optimization & Security Hardening**
- **Dates:** April 27 - May 11, 2026
- **Status:** ACTIVE (currently mid-sprint)
- **Days Elapsed:** 7 (as of May 4, 2026)
- **Days Remaining:** 7
- **Progress:** 50% (7 days in, 7 days remaining)

## Environment Check

Before running, verify:

```bash
# Check MONGODB_URI is set
grep MONGODB_URI /vercel/share/.env.project

# Should output something like:
# MONGODB_URI='mongodb+srv://user:pass@cluster.mongodb.net/agile-tool'
```

## Verify After Seeding

```bash
# In MongoDB Atlas Console:
# 1. Go to Database → Collections
# 2. Select "agile-tool" database
# 3. Verify 3 collections: spaces, sprints, backlog_items
# 4. Count records in each collection
```

## Key Files

| What | Where |
|------|-------|
| Seed Script | `/vercel/share/v0-project/services/sprint_impact_service/seed_complex_dataset.py` |
| Setup Guide | `/vercel/share/v0-project/SETUP_SEED_DATASET.md` |
| Environment | `/vercel/share/.env.project` |

## Test Requirements File

For testing the ML models with Sprint 6 items:
```
/vercel/share/v0-project/TEST_REQUIREMENTS_SPRINT_6.md
```

Contains 10 strong requirements aligned with Sprint 6 goal: "Cost Optimization & Security Hardening"
