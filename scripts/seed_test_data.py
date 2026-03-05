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

def seed_completed_sprints(db, space_id: str) -> dict:
    """
    Create 3 completed sprints with realistic burndown histories.
    
    Sprint 1: Perfect linear burn (25 SP planned, 25 SP completed)
    Sprint 2: Flatline pattern (30 SP planned, 22 SP completed - spillover)
    Sprint 3: Perfect linear burn (20 SP planned, 20 SP completed)
    
    Returns:
        Dictionary mapping sprint names to sprint_ids for historical backlog creation
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
    sprint_ids_dict = {}
    
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
        sprint_ids_dict[f"sprint{config['index'] + 1}"] = {
            "id": sprint_id,
            "name": config["name"],
            "planned_sp": config["planned_sp"],
            "completed_sp": config["completed_sp"]
        }
        
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
    
    return sprint_ids_dict

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

def seed_historical_backlog_items(db, space_id: str, sprint_ids_dict: dict):
    """
    Create historical backlog items for the completed sprints.
    These items are crucial for velocity calculations and analytics.
    
    Sprint 1: 5 items × 5 SP each = 25 SP (all Done)
    Sprint 2: 4 Done items (22 SP) + 2 Unfinished items (8 SP) = 30 SP planned, 22 SP completed
    Sprint 3: 4 items × 5 SP each = 20 SP (all Done)
    """
    print("\n[4] Seeding Historical Backlog Items...")
    
    sprint1_id = sprint_ids_dict["sprint1"]["id"]
    sprint2_id = sprint_ids_dict["sprint2"]["id"]
    sprint3_id = sprint_ids_dict["sprint3"]["id"]
    
    now = datetime.now()
    total_items = 0
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Sprint 1: Foundation & Auth (5 items, 5 SP each, all Done)
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n  Sprint 1: Foundation & Auth (25 SP completed)")
    
    sprint1_items = [
        {
            "title": "Setup User Database Schema",
            "description": "Design and create MongoDB collections for users, with proper indexing and validation.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Create Login API Endpoint",
            "description": "Implement POST /api/auth/login with JWT token generation and session management.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Implement User Registration Flow",
            "description": "Build registration endpoint with email validation, password hashing using bcrypt.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Setup Authentication Middleware",
            "description": "Create middleware to verify JWT tokens and protect authenticated routes.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Create User Profile Endpoint",
            "description": "Implement GET /api/user/profile to retrieve authenticated user information.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 5,
            "status": "Done",
        },
    ]
    
    for item in sprint1_items:
        item_doc = {
            "title": item["title"],
            "description": item["description"],
            "type": item["type"],
            "priority": item["priority"],
            "story_points": item["story_points"],
            "status": item["status"],
            "space_id": space_id,
            "sprint_id": sprint1_id,
            "created_at": now,
            "updated_at": now,
        }
        
        db.backlog_items.insert_one(item_doc)
        print(f"    ✓ {item['title']} ({item['story_points']} SP)")
        total_items += 1
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Sprint 2: User Profiles (4 Done + 2 Unfinished = 30 SP planned, 22 SP completed)
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n  Sprint 2: User Profiles (22 SP completed, 8 SP spillover)")
    
    sprint2_items_done = [
        {
            "title": "Create User Profile Frontend",
            "description": "Build React component to display user profile with edit capability.",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "Done",
        },
        {
            "title": "Implement Profile Update API",
            "description": "Create PUT /api/user/profile endpoint to update user information.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Add Profile Picture Upload",
            "description": "Implement file upload functionality for profile pictures with image validation.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Setup User Avatar Caching",
            "description": "Configure CDN caching for user profile pictures to improve performance.",
            "type": "Task",
            "priority": "Low",
            "story_points": 4,
            "status": "Done",
        },
    ]
    
    sprint2_items_unfinished = [
        {
            "title": "Implement User Preferences System",
            "description": "Create API to store and retrieve user preferences like theme, language, notifications.",
            "type": "Story",
            "priority": "Medium",
            "story_points": 5,
            "status": "In Progress",
        },
        {
            "title": "Add Profile Analytics Dashboard",
            "description": "Build analytics dashboard showing user activity, login history, and engagement metrics.",
            "type": "Task",
            "priority": "Low",
            "story_points": 3,
            "status": "To Do",
        },
    ]
    
    for item in sprint2_items_done:
        item_doc = {
            "title": item["title"],
            "description": item["description"],
            "type": item["type"],
            "priority": item["priority"],
            "story_points": item["story_points"],
            "status": item["status"],
            "space_id": space_id,
            "sprint_id": sprint2_id,
            "created_at": now,
            "updated_at": now,
        }
        
        db.backlog_items.insert_one(item_doc)
        print(f"    ✓ {item['title']} ({item['story_points']} SP) - DONE")
        total_items += 1
    
    for item in sprint2_items_unfinished:
        item_doc = {
            "title": item["title"],
            "description": item["description"],
            "type": item["type"],
            "priority": item["priority"],
            "story_points": item["story_points"],
            "status": item["status"],
            "space_id": space_id,
            "sprint_id": sprint2_id,
            "created_at": now,
            "updated_at": now,
        }
        
        db.backlog_items.insert_one(item_doc)
        print(f"    ✓ {item['title']} ({item['story_points']} SP) - {item['status'].upper()} (SPILLOVER)")
        total_items += 1
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Sprint 3: Security Audit (4 items, 5 SP each, all Done)
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n  Sprint 3: Security Audit (20 SP completed)")
    
    sprint3_items = [
        {
            "title": "Audit Authentication Security",
            "description": "Review JWT implementation, token expiration, and password hashing standards.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Implement HTTPS and TLS",
            "description": "Configure SSL/TLS certificates and enforce HTTPS across all endpoints.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Add Input Validation & Sanitization",
            "description": "Implement input validation to prevent SQL injection and XSS attacks.",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "Done",
        },
        {
            "title": "Setup Security Logging",
            "description": "Implement comprehensive logging for security events, failed logins, and suspicious activities.",
            "type": "Task",
            "priority": "Medium",
            "story_points": 5,
            "status": "Done",
        },
    ]
    
    for item in sprint3_items:
        item_doc = {
            "title": item["title"],
            "description": item["description"],
            "type": item["type"],
            "priority": item["priority"],
            "story_points": item["story_points"],
            "status": item["status"],
            "space_id": space_id,
            "sprint_id": sprint3_id,
            "created_at": now,
            "updated_at": now,
        }
        
        db.backlog_items.insert_one(item_doc)
        print(f"    ✓ {item['title']} ({item['story_points']} SP)")
        total_items += 1
    
    print(f"\n  Total Historical Items Created: {total_items}")
    print(f"  Average Completed Velocity: ({sprint_ids_dict['sprint1']['completed_sp']} + {sprint_ids_dict['sprint2']['completed_sp']} + {sprint_ids_dict['sprint3']['completed_sp']}) / 3 = {(sprint_ids_dict['sprint1']['completed_sp'] + sprint_ids_dict['sprint2']['completed_sp'] + sprint_ids_dict['sprint3']['completed_sp']) / 3:.1f} SP/Sprint")

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
        sprint_ids_dict = seed_completed_sprints(db, space_id)
        seed_historical_backlog_items(db, space_id, sprint_ids_dict)
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
        print("    ├─ Sprint 1: Foundation & Auth")
        print("    │   └─ 5 items × 5 SP = 25 SP (all Done → 100% velocity)")
        print("    ├─ Sprint 2: User Profiles")
        print("    │   ├─ 4 Done items = 22 SP")
        print("    │   └─ 2 Unfinished items = 8 SP (spillover → 73% velocity)")
        print("    ├─ Sprint 3: Security Audit")
        print("    │   └─ 4 items × 5 SP = 20 SP (all Done → 100% velocity)")
        print("    └─ Sprint 4: Stripe Integration (ACTIVE)")
        print("        └─ 4 items = 24 SP (6 SP capacity remaining)")
        print("  • Historical Items: 13 items total (for velocity calculations)")
        print("  • Average Velocity: (25 + 22 + 20) / 3 = 22.33 SP/Sprint")
        print("  • Active Sprint Backlog: 4 items (24 SP)")
        print("  • Unassigned Backlog: 5 items (testing ML rules: ADD, SWAP, SPLIT, DEFER, EVALUATE)")
        
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
