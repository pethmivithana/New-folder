from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "agile-tool"

client = None
database = None

async def connect_db():
    global client, database
    client = AsyncIOMotorClient(MONGODB_URI)
    database = client[DATABASE_NAME]
    
    # Create indexes
    await database.spaces.create_index([("created_at", DESCENDING)])
    await database.sprints.create_index([("space_id", ASCENDING)])
    await database.backlog_items.create_index([("space_id", ASCENDING)])
    await database.backlog_items.create_index([("sprint_id", ASCENDING)])
    
    print("Connected to MongoDB")

async def close_db():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")

def get_database():
    return database


# ── Helper functions ──────────────────────────────────────────────────────────

def _sprint_helper(sprint) -> dict:
    return {
        "id": str(sprint["_id"]),
        "name": sprint["name"],
        "goal": sprint.get("goal", ""),
        "duration_type": sprint.get("duration_type", "2 Weeks"),
        "start_date": sprint.get("start_date").strftime('%Y-%m-%d') if sprint.get("start_date") else None,
        "end_date": sprint.get("end_date").strftime('%Y-%m-%d') if sprint.get("end_date") else None,
        "space_id": sprint["space_id"],
        "status": sprint["status"],
        "assignees": sprint.get("assignees", []),
        "created_at": sprint["created_at"],
        "updated_at": sprint["updated_at"],
    }

def _backlog_helper(item) -> dict:
    return {
        "id": str(item["_id"]),
        "title": item["title"],
        "description": item["description"],
        "type": item["type"],
        "priority": item["priority"],
        "story_points": item["story_points"],
        "status": item["status"],
        "space_id": item["space_id"],
        "sprint_id": item.get("sprint_id"),
        "created_at": item["created_at"],
        "updated_at": item["updated_at"],
    }


# ── Sprint helpers ────────────────────────────────────────────────────────────

async def get_sprint_by_id(sprint_id: str) -> dict | None:
    """Fetch a single sprint by its string ID. Returns None if not found."""
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        return None
    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        return None
    return _sprint_helper(sprint)


async def get_backlog_items_by_sprint(sprint_id: str) -> list:
    """Fetch all backlog items assigned to a sprint."""
    db = get_database()
    items = []
    async for item in db.backlog_items.find({"sprint_id": sprint_id}).sort("created_at", -1):
        items.append(_backlog_helper(item))
    return items


# ── Analytics helpers ─────────────────────────────────────────────────────────

async def get_space_velocity_history(space_id: str, limit: int = 10) -> list:
    """
    Return velocity data for the last `limit` completed sprints in a space.
    Velocity = total story points of Done items in each sprint.
    """
    db = get_database()
    velocity_history = []

    async for sprint in (
        db.sprints.find({"space_id": space_id, "status": "Completed"})
        .sort("updated_at", DESCENDING)
        .limit(limit)
    ):
        sprint_id_str = str(sprint["_id"])
        done_points = 0
        async for item in db.backlog_items.find(
            {"sprint_id": sprint_id_str, "status": "Done"}
        ):
            done_points += item.get("story_points", 0)

        velocity_history.append({
            "sprint_id": sprint_id_str,
            "sprint_name": sprint["name"],
            "velocity": done_points,
        })

    # Return in chronological order
    velocity_history.reverse()
    return velocity_history


async def calculate_burndown_data(sprint_id: str) -> dict | None:
    """
    Build a simple ideal vs actual burndown chart dataset for a sprint.
    Returns None if the sprint is not found.
    """
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        return None

    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        return None

    start = sprint.get("start_date")
    end = sprint.get("end_date")

    if not start or not end:
        return {"error": "Sprint has no dates configured", "data": []}

    # Collect all items in the sprint
    total_points = 0
    done_points = 0
    async for item in db.backlog_items.find({"sprint_id": sprint_id}):
        sp = item.get("story_points", 0)
        total_points += sp
        if item.get("status") == "Done":
            done_points += sp

    remaining_points = total_points - done_points

    # Build ideal burndown line
    if isinstance(start, str):
        start = datetime.strptime(start, '%Y-%m-%d')
    if isinstance(end, str):
        end = datetime.strptime(end, '%Y-%m-%d')

    total_days = max(1, (end - start).days)
    daily_ideal = total_points / total_days

    ideal_data = []
    for day in range(total_days + 1):
        current_date = start + timedelta(days=day)
        ideal_remaining = max(0, total_points - daily_ideal * day)
        ideal_data.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "ideal": round(ideal_remaining, 1),
        })

    return {
        "sprint_name": sprint["name"],
        "total_points": total_points,
        "remaining_points": remaining_points,
        "done_points": done_points,
        "ideal_burndown": ideal_data,
    }


async def calculate_burnup_data(sprint_id: str) -> dict | None:
    """
    Build a simple burnup chart dataset for a sprint.
    Returns None if the sprint is not found.
    """
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        return None

    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        return None

    start = sprint.get("start_date")
    end = sprint.get("end_date")

    if not start or not end:
        return {"error": "Sprint has no dates configured", "data": []}

    total_points = 0
    done_points = 0
    async for item in db.backlog_items.find({"sprint_id": sprint_id}):
        sp = item.get("story_points", 0)
        total_points += sp
        if item.get("status") == "Done":
            done_points += sp

    if isinstance(start, str):
        start = datetime.strptime(start, '%Y-%m-%d')
    if isinstance(end, str):
        end = datetime.strptime(end, '%Y-%m-%d')

    total_days = max(1, (end - start).days)
    daily_target = total_points / total_days

    burnup_data = []
    for day in range(total_days + 1):
        current_date = start + timedelta(days=day)
        target = min(total_points, round(daily_target * day, 1))
        burnup_data.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "target": target,
            "scope": total_points,
        })

    return {
        "sprint_name": sprint["name"],
        "total_points": total_points,
        "done_points": done_points,
        "burnup": burnup_data,
    }