"""
Comprehensive MongoDB Seeding Script for Agile Replanning Decision Support System

This script generates a realistic "Golden Dataset" to test all AI and analytical features:
- TF-IDF for Story Point Suggestion
- Dense Vector Embeddings for Sprint Goal Alignment
- XGBoost/PyTorch models for Effort, Schedule Risk, Quality Risk, and Productivity
- 3-Phase Rule Engine (ADD, DEFER, SPLIT, SWAP)
- Analytics: Velocity Charts and Burndown Charts
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "agile-tool"

# Connect to MongoDB
def connect():
    """Connect to MongoDB and return client and database."""
    try:
        client = MongoClient(MONGODB_URI)
        client.admin.command('ping')  # Verify connection
        db = client[DATABASE_NAME]
        print(f"✓ Connected to MongoDB: {MONGODB_URI}")
        return client, db
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Data Generation Helpers
# ─────────────────────────────────────────────────────────────────────────────

def generate_burndown_history(total_days: int, total_points: int, 
                              final_remaining: int = 0, is_flat: bool = False) -> list:
    """
    Generate a realistic burndown history for a sprint.
    
    Args:
        total_days: Number of sprint days
        total_points: Total story points in sprint
        final_remaining: Story points remaining at end (0 = perfect, >0 = spillover)
        is_flat: If True, shows flatline at end (typical for delayed sprints)
    
    Returns:
        List of daily burndown records
    """
    history = []
    
    if is_flat:
        # Flatline pattern: slow burn, then stalls
        daily_burn = total_points * 0.7 / (total_days * 0.5)  # Slow burn for first half
        stall_point = int(total_days * 0.6)
        
        for day in range(total_days + 1):
            if day <= stall_point:
                remaining = max(0, total_points - (daily_burn * day))
            else:
                remaining = final_remaining  # Stalls out
            
            history.append({
                "day": day,
                "remaining_points": round(remaining, 1),
                "timestamp": (datetime.now() - timedelta(days=total_days-day)).isoformat()
            })
    else:
        # Perfect linear burn
        daily_burn = (total_points - final_remaining) / total_days
        
        for day in range(total_days + 1):
            remaining = max(final_remaining, total_points - (daily_burn * day))
            history.append({
                "day": day,
                "remaining_points": round(remaining, 1),
                "timestamp": (datetime.now() - timedelta(days=total_days-day)).isoformat()
            })
    
    return history

# ─────────────────────────────────────────────────────────────────────────────
# Data Seeding Functions
# ─────────────────────────────────────────────────────────────────────────────

def seed_space(db) -> str:
    """
    Create the Space: "FinTech Payment Portal"
    
    Returns:
        space_id (MongoDB ObjectId as string)
    """
    print("\n[1] Seeding Space...")
    
    space_doc = {
        "name": "FinTech Payment Portal",
        "description": "Core payment gateway infrastructure and user dashboard.",
        "max_assignees": 5,
        "focus_hours_per_day": 6.0,
        "risk_appetite": "Standard",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    result = db.spaces.insert_one(space_doc)
    space_id = str(result.inserted_id)
    
    print(f"  ✓ Space created: {space_id}")
    print(f"    Name: {space_doc['name']}")
    print(f"    Description: {space_doc['description']}")
    
    return space_id

def seed_completed_sprints(db, space_id: str):
    """
    Create 3 completed sprints with realistic burndown histories.
    
    Sprint 1: Perfect linear burn (25 SP planned, 25 SP completed)
    Sprint 2: Flatline pattern (30 SP planned, 22 SP completed - spillover)
    Sprint 3: Perfect linear burn (20 SP planned, 20 SP completed)
    """
    print("\n[2] Seeding Completed Sprints...")
    
    sprints_config = [
        {
            "name": "Sprint 1: Foundation & Auth",
            "goal": "Foundation & Auth",
            "status": "Completed",
            "planned_sp": 25,
            "completed_sp": 25,
            "duration_days": 14,
            "is_flat": False,
            "index": 0,
        },
        {
            "name": "Sprint 2: User Profiles",
            "goal": "User Profiles",
            "status": "Completed",
            "planned_sp": 30,
            "completed_sp": 22,
            "duration_days": 14,
            "is_flat": True,
            "index": 1,
        },
        {
            "name": "Sprint 3: Security Audit",
            "goal": "Security Audit",
            "status": "Completed",
            "planned_sp": 20,
            "completed_sp": 20,
            "duration_days": 14,
            "is_flat": False,
            "index": 2,
        },
    ]
    
    now = datetime.now()
    sprint_ids = []
    
    for config in sprints_config:
        # Calculate dates (past sprints)
        days_offset = 45 - (config["index"] * 15)  # 45, 30, 15 days ago
        start_date = now - timedelta(days=days_offset)
        end_date = start_date + timedelta(days=config["duration_days"])
        
        sprint_doc = {
            "name": config["name"],
            "goal": config["goal"],
            "space_id": space_id,
            "status": config["status"],
            "duration_type": "2 Weeks",
            "start_date": start_date,
            "end_date": end_date,
            "assignees": [],
            "created_at": start_date,
            "updated_at": now,
        }
        
        result = db.sprints.insert_one(sprint_doc)
        sprint_id = str(result.inserted_id)
        sprint_ids.append(sprint_id)
        
        # Generate burndown history
        final_remaining = config["planned_sp"] - config["completed_sp"]
        burndown = generate_burndown_history(
            total_days=config["duration_days"],
            total_points=config["planned_sp"],
            final_remaining=final_remaining,
            is_flat=config["is_flat"]
        )
        
        # Update sprint with burndown history
        db.sprints.update_one(
            {"_id": result.inserted_id},
            {"$set": {"burndown_history": burndown}}
        )
        
        print(f"  ✓ {config['name']} ({sprint_id})")
        print(f"    Planned: {config['planned_sp']} SP | Completed: {config['completed_sp']} SP")
        print(f"    Dates: {start_date.date()} to {end_date.date()}")
        if config["is_flat"]:
            print(f"    Pattern: Flatline (spillover)")
        else:
            print(f"    Pattern: Perfect linear burn")

def seed_active_sprint(db, space_id: str) -> str:
    """
    Create the current active sprint: "Sprint 4: Stripe Integration"
    - Capacity: 30 SP total
    - Currently populated: 24 SP (6 SP free remaining)
    
    Returns:
        sprint_id (MongoDB ObjectId as string)
    """
    print("\n[3] Seeding Active Sprint...")
    
    now = datetime.now()
    start_date = now - timedelta(days=3)  # Started 3 days ago
    end_date = now + timedelta(days=11)   # Ends in 11 days
    
    sprint_doc = {
        "name": "Sprint 4: Stripe Integration",
        "goal": "Integrate Stripe API to securely process live credit card transactions and handle webhooks.",
        "space_id": space_id,
        "status": "Active",
        "duration_type": "2 Weeks",
        "start_date": start_date,
        "end_date": end_date,
        "assignees": [],
        "created_at": now,
        "updated_at": now,
    }
    
    result = db.sprints.insert_one(sprint_doc)
    sprint_id = str(result.inserted_id)
    
    print(f"  ✓ Sprint created: {sprint_id}")
    print(f"    Name: {sprint_doc['name']}")
    print(f"    Goal: {sprint_doc['goal']}")
    print(f"    Capacity: 30 SP (6 SP free remaining)")
    print(f"    Status: Active")
    
    return sprint_id

def seed_sprint_backlog_items(db, sprint_id: str):
    """
    Create 6 backlog items that fill the active sprint (24 SP total).
    These are realistic payment-related tasks.
    """
    print("\n[4] Seeding Sprint Backlog Items (24 SP)...")
    
    items = [
        {
            "title": "Setup Stripe account and API keys",
            "description": "Create Stripe account, generate API keys, configure webhooks for payment events.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "In Progress",
        },
        {
            "title": "Implement Stripe payment form component",
            "description": "Build React component for Stripe card element with form validation and error handling.",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "To Do",
        },
        {
            "title": "Create payment processing API endpoint",
            "description": "Implement POST /api/payments endpoint that calls Stripe API and handles charge creation.",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "To Do",
        },
        {
            "title": "Integrate webhook handling for payment events",
            "description": "Listen for Stripe webhook events and update payment status in database.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 3,
            "status": "To Do",
        },
    ]
    
    now = datetime.now()
    
    for item in items:
        item_doc = {
            "title": item["title"],
            "description": item["description"],
            "type": item["type"],
            "priority": item["priority"],
            "story_points": item["story_points"],
            "status": item["status"],
            "space_id": sprint_id.split("_")[0],  # Use space_id from sprint_id context
            "sprint_id": sprint_id,
            "created_at": now,
            "updated_at": now,
        }
        
        result = db.backlog_items.insert_one(item_doc)
        print(f"  ✓ {item['title']} ({item['story_points']} SP)")
    
    print(f"  Total Sprint Items: 24 SP (6 SP capacity remaining)")

def seed_backlog_items(db, space_id: str):
    """
    Create 5 unassigned backlog items that test specific ML rules:
    
    Item A: "Perfect Fit" - Tests 'ADD' rule
    Item B: "Emergency" - Tests 'SWAP/ADD' via Layer 1 Blocker
    Item C: "Monster" - Tests 'SPLIT' rule (TF-IDF predicts 13+ points)
    Item D: "Distraction" - Tests 'DEFER' rule
    Item E: "Tangential" - Tests 'EVALUATE/CONSIDER'
    """
    print("\n[5] Seeding Backlog Items (Testing ML Rules)...")
    
    items = [
        {
            "title": "Add CVC validation field to checkout",
            "description": "Ensure the Stripe credit card form requires a 3-digit security code.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "To Do",
            "epic": "Payment Gateway",
            "components": ["stripe", "frontend"],
            "rule_test": "Item A - Perfect Fit (ADD)",
            "notes": "High semantic alignment with Stripe Integration, low effort, high priority."
        },
        {
            "title": "Production database crash on login",
            "description": "Emergency! Users cannot log in. The service is down.",
            "type": "Bug",
            "priority": "Critical",
            "story_points": 8,
            "status": "To Do",
            "epic": "Auth",
            "components": ["backend", "database"],
            "rule_test": "Item B - Emergency (SWAP/ADD)",
            "notes": "Mismatched epic but Critical priority triggers Layer 1 Blocker."
        },
        {
            "title": "Refactor legacy monolithic transaction database",
            "description": "Massive architectural overhaul of the cryptographic payload. Complex database migrations required. This involves complete restructuring of transaction tables, encryption mechanisms, and data integrity checks.",
            "type": "Story",
            "priority": "Medium",
            "story_points": 13,  # Will trigger SPLIT if capacity exceeded
            "status": "To Do",
            "epic": "Payment Gateway",
            "components": ["backend", "database"],
            "rule_test": "Item C - Monster (SPLIT)",
            "notes": "TF-IDF keywords trigger high point estimate. Exceeds free capacity, triggers SPLIT."
        },
        {
            "title": "Change footer background color",
            "description": "Marketing wants the bottom of the homepage to be dark blue instead of gray.",
            "type": "Task",
            "priority": "Low",
            "story_points": 3,
            "status": "To Do",
            "epic": "UI Polish",
            "components": ["css", "frontend"],
            "rule_test": "Item D - Distraction (DEFER)",
            "notes": "Low semantic alignment with Stripe Integration goal, low priority."
        },
        {
            "title": "Update PayPal webhook handler",
            "description": "Adjust the endpoint for PayPal refund receipts. Currently the webhook handler for PayPal refunds is receiving incorrect refund status codes.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 5,
            "status": "To Do",
            "epic": "Payment Gateway",
            "components": ["backend", "api"],
            "rule_test": "Item E - Tangential (EVALUATE)",
            "notes": "Related to payments but not Stripe-specific. Moderate alignment, consider for future sprint."
        },
    ]
    
    now = datetime.now()
    
    for item in items:
        item_doc = {
            "title": item["title"],
            "description": item["description"],
            "type": item["type"],
            "priority": item["priority"],
            "story_points": item["story_points"],
            "status": item["status"],
            "space_id": space_id,
            "sprint_id": None,  # Unassigned to backlog
            "epic": item.get("epic"),
            "components": item.get("components", []),
            "created_at": now,
            "updated_at": now,
        }
        
        result = db.backlog_items.insert_one(item_doc)
        print(f"  ✓ {item['title']}")
        print(f"    {item['rule_test']}")
        print(f"    SP: {item['story_points']} | Priority: {item['priority']}")

def create_indexes(db):
    """Create necessary MongoDB indexes for performance."""
    print("\n[6] Creating Indexes...")
    
    db.spaces.create_index([("created_at", DESCENDING)])
    db.sprints.create_index([("space_id", ASCENDING)])
    db.sprints.create_index([("status", ASCENDING)])
    db.backlog_items.create_index([("space_id", ASCENDING)])
    db.backlog_items.create_index([("sprint_id", ASCENDING)])
    db.backlog_items.create_index([("priority", ASCENDING)])
    
    print("  ✓ All indexes created")

# ─────────────────────────────────────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Main seeding function."""
    print("\n" + "="*70)
    print("AGILE REPLANNING SYSTEM - GOLDEN DATASET SEEDING")
    print("="*70)
    
    client, db = connect()
    
    try:
        # Clear existing data
        print("\n[0] Clearing existing data...")
        db.spaces.delete_many({})
        db.sprints.delete_many({})
        db.backlog_items.delete_many({})
        print("  ✓ Database cleared")
        
        # Seed data
        space_id = seed_space(db)
        seed_completed_sprints(db, space_id)
        active_sprint_id = seed_active_sprint(db, space_id)
        seed_sprint_backlog_items(db, active_sprint_id)
        seed_backlog_items(db, space_id)
        create_indexes(db)
        
        # Summary
        print("\n" + "="*70)
        print("SEEDING COMPLETE")
        print("="*70)
        
        space_count = db.spaces.count_documents({})
        sprint_count = db.sprints.count_documents({})
        backlog_count = db.backlog_items.count_documents({})
        
        print(f"\nStatistics:")
        print(f"  ✓ Spaces: {space_count}")
        print(f"  ✓ Sprints: {sprint_count}")
        print(f"  ✓ Backlog Items: {backlog_count}")
        
        print(f"\nSpace ID: {space_id}")
        print(f"Active Sprint ID: {active_sprint_id}")
        
        print("\nDataset Structure:")
        print("  • 1 Space (FinTech Payment Portal)")
        print("  • 4 Sprints (3 Completed, 1 Active)")
        print("  • Sprint 1: Foundation & Auth (25 SP, perfect burn)")
        print("  • Sprint 2: User Profiles (22/30 SP, flatline pattern)")
        print("  • Sprint 3: Security Audit (20 SP, perfect burn)")
        print("  • Sprint 4: Stripe Integration (24/30 SP active, 6 SP capacity)")
        print("  • 4 Sprint Items (24 SP total in active sprint)")
        print("  • 5 Backlog Items (testing ML rules: ADD, SWAP, SPLIT, DEFER, EVALUATE)")
        
        print("\n" + "="*70)
        print("Ready for testing AI/ML features and analytics!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()
