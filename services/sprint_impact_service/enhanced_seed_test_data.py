"""
ENHANCED SEED_TEST_DATA.PY
──────────────────────────────────────────────────────────────────────────────
Generates a comprehensive, realistic Agile project history with 5 completed sprints
and 1 active sprint. Includes:

✓ Velocity Fluctuation (Sprint 1-5: 20, 35, 15, 32, 28 SP)
✓ Dynamic Capacity Math based on velocity changes
✓ Historical hours-per-day calculations (not hardcoded)
✓ Assignee impact on sprint capacity
✓ Daily burndown/burnup logs for chart rendering
✓ Detailed backlog items with varied complexity
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "agile-tool"

# Sprint Configuration
SPRINTS = [
    {"name": "Sprint 1", "velocity": 20, "days": 10, "assignees": 3, "completed": True},
    {"name": "Sprint 2", "velocity": 35, "days": 10, "assignees": 4, "completed": True},  # More devs added
    {"name": "Sprint 3", "velocity": 15, "days": 10, "assignees": 3, "completed": True},  # Holiday slowdown
    {"name": "Sprint 4", "velocity": 32, "days": 10, "assignees": 4, "completed": True},  # Recovery
    {"name": "Sprint 5", "velocity": 28, "days": 10, "assignees": 3, "completed": True},  # Stabilized
    {"name": "Sprint 6", "velocity": 30, "days": 10, "assignees": 4, "completed": False}, # Active
]

BASE_FOCUS_HOURS_PER_DAY = 6.0
BASE_ASSIGNEES = 3


# ─────────────────────────────────────────────────────────────────────────────
# Connection Helper
# ─────────────────────────────────────────────────────────────────────────────

def connect():
    """Connect to MongoDB and return client and database."""
    try:
        client = MongoClient(MONGODB_URI)
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        print(f"✓ Connected to MongoDB: {MONGODB_URI}")
        return client, db
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic Capacity Calculation
# ─────────────────────────────────────────────────────────────────────────────

def calculate_dynamic_capacity(velocity: int, assignees: int, days: int) -> dict:
    """
    Calculate sprint capacity based on historical velocity and team size.
    
    Formula:
        Total_Sprint_Hours = velocity * hours_per_sp
        Hours_Per_SP = (total_days * focus_hours * num_assignees) / velocity
        Effective_Capacity = velocity * (assignees / base_assignees)
    
    Args:
        velocity: Story points delivered in this sprint
        assignees: Number of team members
        days: Duration of sprint in days
    
    Returns:
        dict with calculated metrics
    """
    total_sprint_hours = days * BASE_FOCUS_HOURS_PER_DAY * assignees
    hours_per_sp = total_sprint_hours / max(velocity, 1)
    
    # Capacity scales with team size
    capacity_multiplier = assignees / BASE_ASSIGNEES
    effective_capacity = velocity * capacity_multiplier
    
    return {
        "total_hours": total_sprint_hours,
        "hours_per_sp": round(hours_per_sp, 2),
        "velocity": velocity,
        "assignees": assignees,
        "capacity_multiplier": round(capacity_multiplier, 2),
        "effective_capacity": round(effective_capacity, 1),
    }


def generate_realistic_burndown(
    total_sp: int,
    days: int,
    velocity_pattern: str = "normal"
) -> list:
    """
    Generate realistic daily burndown data.
    
    Patterns:
      - normal: smooth decline
      - holiday: flat for first 2 days, then normal
      - slowstart: slow first half, then fast
    """
    burndown = []
    daily_burn = total_sp / days
    
    for day in range(days + 1):
        if velocity_pattern == "holiday":
            # Slow start due to holidays
            if day <= 2:
                remaining = total_sp - (daily_burn * 0.3 * day)
            else:
                burn_so_far = (daily_burn * 0.6) + (daily_burn * (day - 2))
                remaining = total_sp - burn_so_far
        elif velocity_pattern == "slowstart":
            # Slow start, faster end
            if day <= days * 0.5:
                remaining = total_sp - (daily_burn * 0.5 * day)
            else:
                burn_so_far = (daily_burn * 0.5 * (days * 0.5)) + (daily_burn * 1.3 * (day - days * 0.5))
                remaining = total_sp - burn_so_far
        else:  # normal
            remaining = total_sp - (daily_burn * day)
        
        remaining = max(0, remaining)
        
        burndown.append({
            "day": day,
            "remaining_sp": round(remaining, 1),
            "hours_remaining": round(remaining * calculate_dynamic_capacity(total_sp, 3, days)["hours_per_sp"], 1),
            "timestamp": (datetime.now() - timedelta(days=days - day)).isoformat(),
        })
    
    return burndown


# ─────────────────────────────────────────────────────────────────────────────
# Data Generation
# ─────────────────────────────────────────────────────────────────────────────

def seed_space(db) -> str:
    """Create the Space."""
    space_doc = {
        "_id": ObjectId(),
        "name": "TechCorp Engineering",
        "description": "Internal payment processing platform",
        "max_assignees": 5,
        "focus_hours_per_day": 6.0,
        "risk_appetite": "Standard",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    result = db.spaces.insert_one(space_doc)
    print(f"✓ Created Space: {space_doc['name']} (ID: {result.inserted_id})")
    return str(result.inserted_id)


def seed_backlog_items(db, space_id: str) -> dict:
    """Create backlog items with varying complexity."""
    items = [
        {
            "title": "Implement OAuth 2.0 integration",
            "description": "Add OAuth provider support for third-party integrations. Requires API keys, token management, and security review.",
            "type": "Story",
            "priority": "High",
            "story_points": 13,
            "status": "To Do",
            "space_id": space_id,
        },
        {
            "title": "Create user dashboard",
            "description": "Build responsive dashboard showing transaction history, balance, and analytics. Mobile-first design.",
            "type": "Story",
            "priority": "High",
            "story_points": 8,
            "status": "To Do",
            "space_id": space_id,
        },
        {
            "title": "Fix payment webhook timeout",
            "description": "Critical: webhooks timing out after 30 seconds. Investigate queue processing and add retry logic.",
            "type": "Bug",
            "priority": "Critical",
            "story_points": 5,
            "status": "To Do",
            "space_id": space_id,
        },
        {
            "title": "Database query optimization",
            "description": "Analyze slow queries in transaction reports. Create indexes and optimize N+1 queries.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 5,
            "status": "To Do",
            "space_id": space_id,
        },
        {
            "title": "Write API documentation",
            "description": "Complete OpenAPI/Swagger docs for all endpoints. Include rate limiting and error codes.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 3,
            "status": "To Do",
            "space_id": space_id,
        },
        {
            "title": "Add two-factor authentication",
            "description": "Implement TOTP-based 2FA. Support SMS and authenticator apps.",
            "type": "Story",
            "priority": "High",
            "story_points": 8,
            "status": "To Do",
            "space_id": space_id,
        },
        {
            "title": "Setup monitoring and alerting",
            "description": "Configure Prometheus, Grafana, and alerts for API latency, error rates, and database health.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 5,
            "status": "To Do",
            "space_id": space_id,
        },
        {
            "title": "Batch payment processing",
            "description": "Allow admins to process payments in bulk (CSV upload). Validation and error reporting.",
            "type": "Story",
            "priority": "Medium",
            "story_points": 8,
            "status": "To Do",
            "space_id": space_id,
        },
    ]
    
    item_ids = {}
    for item in items:
        item["_id"] = ObjectId()
        item["created_at"] = datetime.now()
        item["updated_at"] = datetime.now()
        db.backlog_items.insert_one(item)
        item_ids[item["title"]] = str(item["_id"])
        print(f"  - {item['title']} ({item['story_points']} SP)")
    
    return item_ids


def seed_sprints(db, space_id: str, item_ids: dict) -> dict:
    """Create sprints 1-6 with historical data and active sprint."""
    sprint_ids = {}
    base_date = datetime.now() - timedelta(days=60)
    
    for idx, sprint_config in enumerate(SPRINTS):
        sprint_doc = {
            "_id": ObjectId(),
            "name": sprint_config["name"],
            "goal": f"Complete core payment features and improve system reliability" if idx < 3 else f"Enhance security and scale infrastructure",
            "duration_type": "2 Weeks" if sprint_config["days"] == 10 else "Custom",
            "space_id": space_id,
            "status": "Completed" if sprint_config["completed"] else "Active",
            "assignees": list(range(1, sprint_config["assignees"] + 1)),
            "created_at": base_date + timedelta(days=idx * 14),
            "updated_at": base_date + timedelta(days=idx * 14),
            "start_date": (base_date + timedelta(days=idx * 14)).isoformat(),
            "end_date": (base_date + timedelta(days=(idx + 1) * 14)).isoformat(),
            
            # Historical Analytics
            "planned_velocity": sprint_config["velocity"],
            "actual_velocity": sprint_config["velocity"],
            "capacity_info": calculate_dynamic_capacity(
                sprint_config["velocity"],
                sprint_config["assignees"],
                sprint_config["days"]
            ),
            "burndown_history": generate_realistic_burndown(
                sprint_config["velocity"],
                sprint_config["days"],
                velocity_pattern="holiday" if idx == 2 else ("slowstart" if idx == 0 else "normal")
            ),
        }
        
        db.sprints.insert_one(sprint_doc)
        sprint_ids[sprint_config["name"]] = str(sprint_doc["_id"])
        
        capacity_info = sprint_doc["capacity_info"]
        print(f"\n✓ {sprint_config['name']}:")
        print(f"  - Velocity: {capacity_info['velocity']} SP")
        print(f"  - Assignees: {capacity_info['assignees']}")
        print(f"  - Hours/SP: {capacity_info['hours_per_sp']}h")
        print(f"  - Effective Capacity: {capacity_info['effective_capacity']} SP")
    
    return sprint_ids


def seed_completed_items(db, space_id: str, sprint_ids: dict, item_ids: dict):
    """Create completed items for historical sprints."""
    completed_items = [
        ("Sprint 1", ["Write API documentation", "Database query optimization"], ["Done", "Done"]),
        ("Sprint 2", ["Create user dashboard", "Add two-factor authentication"], ["Done", "Done"]),
        ("Sprint 3", ["Setup monitoring and alerting"], ["Done"]),
        ("Sprint 4", ["Implement OAuth 2.0 integration", "Batch payment processing"], ["Done", "Done"]),
        ("Sprint 5", ["Fix payment webhook timeout"], ["Done"]),
        ("Sprint 6", ["Create user dashboard"], ["In Progress"]),
    ]
    
    for sprint_name, titles, statuses in completed_items:
        sprint_id = sprint_ids.get(sprint_name)
        if not sprint_id:
            continue
        
        for title, status in zip(titles, statuses):
            if title in item_ids:
                db.backlog_items.update_one(
                    {"_id": ObjectId(item_ids[title])},
                    {
                        "$set": {
                            "sprint_id": sprint_id,
                            "status": status,
                            "updated_at": datetime.now(),
                        }
                    }
                )
                print(f"  ✓ {title} → {sprint_name} ({status})")


def clear_database(db):
    """Clear existing data."""
    collections = ["spaces", "sprints", "backlog_items"]
    for collection in collections:
        result = db[collection].delete_many({})
        print(f"✓ Cleared {collection}: {result.deleted_count} documents removed")


def main():
    """Main seeding orchestration."""
    print("\n" + "=" * 80)
    print("SEEDING ENHANCED TEST DATA FOR AGILE IMPACT ANALYZER")
    print("=" * 80 + "\n")
    
    client, db = connect()
    
    try:
        # Clear existing data
        print("\n[STEP 1] Clearing existing data...")
        clear_database(db)
        
        # Seed space
        print("\n[STEP 2] Creating Space...")
        space_id = seed_space(db)
        
        # Seed backlog
        print("\n[STEP 3] Creating Backlog Items...")
        item_ids = seed_backlog_items(db, space_id)
        
        # Seed sprints with capacity metrics
        print("\n[STEP 4] Creating Sprints with Dynamic Capacity...")
        sprint_ids = seed_sprints(db, space_id, item_ids)
        
        # Seed completed items into sprints
        print("\n[STEP 5] Assigning items to sprints...")
        seed_completed_items(db, space_id, sprint_ids, item_ids)
        
        print("\n" + "=" * 80)
        print("✓ SEEDING COMPLETE!")
        print("=" * 80)
        print(f"\nGenerated Data Summary:")
        print(f"  - Space: TechCorp Engineering")
        print(f"  - Sprints: 6 (5 completed, 1 active)")
        print(f"  - Backlog Items: {len(item_ids)}")
        print(f"  - Historical Velocities: 20 → 35 → 15 → 32 → 28 → 30 SP")
        print(f"  - Data includes realistic burndown charts and capacity metrics")
        print("\nDatabase ready for testing!\n")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    main()
