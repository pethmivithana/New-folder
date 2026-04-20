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
    def format_date(date_obj):
        if not date_obj:
            return None
        if isinstance(date_obj, str):
            return date_obj
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d')
        return None
    
    return {
        "id": str(sprint["_id"]),
        "name": sprint["name"],
        "goal": sprint.get("goal", ""),
        "duration_type": sprint.get("duration_type", "2 Weeks"),
        "start_date": format_date(sprint.get("start_date")),
        "end_date": format_date(sprint.get("end_date")),
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


async def get_completed_sprints(space_id: str, limit: int = 20) -> list:
    """
    Fetch the last `limit` completed sprints for a space (for TEAM_PACE calculation).
    
    Returns list of dicts with: id, completed_sp, start_date, end_date
    """
    db = get_database()
    completed_sprints = []
    
    async for sprint in (
        db.sprints.find({"space_id": space_id, "status": "Completed"})
        .sort("updated_at", DESCENDING)
        .limit(limit)
    ):
        sprint_id_str = str(sprint["_id"])
        
        # Calculate completed story points for this sprint
        completed_sp = 0
        async for item in db.backlog_items.find({"sprint_id": sprint_id_str, "status": "Done"}):
            completed_sp += item.get("story_points", 0)
        
        completed_sprints.append({
            "id": sprint_id_str,
            "completed_sp": completed_sp,
            "start_date": sprint.get("start_date"),
            "end_date": sprint.get("end_date"),
        })
    
    return completed_sprints


async def get_last_completed_sprint(space_id: str) -> dict | None:
    """
    Fetch the most recently completed sprint for a space.
    Used to calculate actual focus hours from real sprint data.
    
    Returns:
        dict with: sprint_id, completed_story_points, sprint_duration_days, assignee_count
        or None if no completed sprint exists
    """
    db = get_database()
    
    # Find the most recent completed sprint
    sprint = await db.sprints.find_one(
        {"space_id": space_id, "status": "Completed"},
        sort=[("updated_at", DESCENDING)]
    )
    
    if not sprint:
        return None
    
    sprint_id_str = str(sprint["_id"])
    
    # Calculate sprint duration in days
    start = sprint.get("start_date")
    end = sprint.get("end_date")
    sprint_duration_days = 1
    
    try:
        if isinstance(start, str):
            start = datetime.strptime(start, '%Y-%m-%d')
        if isinstance(end, str):
            end = datetime.strptime(end, '%Y-%m-%d')
        
        if start and end:
            sprint_duration_days = max(1, (end - start).days)
    except (ValueError, TypeError):
        sprint_duration_days = 1
    
    # Count completed story points and assignees
    completed_story_points = 0
    assignee_set = set()
    
    async for item in db.backlog_items.find({"sprint_id": sprint_id_str, "status": "Done"}):
        completed_story_points += item.get("story_points", 0)
        # Note: assignees might be stored differently; adjust based on your schema
        if "assignee_id" in item:
            assignee_set.add(item["assignee_id"])
    
    assignee_count = max(1, len(assignee_set))
    
    return {
        "sprint_id": sprint_id_str,
        "completed_story_points": completed_story_points,
        "sprint_duration_days": sprint_duration_days,
        "assignee_count": assignee_count,
    }


async def calculate_sprint_capacity(space_id: str, new_assignee_count: int, base_sp_per_assignee: int = 8) -> int:
    """
    Calculate recommended sprint capacity for a new sprint based on:
    1. Historical team velocity (completed SP from previous sprints)
    2. Assignee count (number of people on the new sprint)
    3. Completion ratio (% of committed work actually completed)
    
    Formula:
      For first sprint: capacity = new_assignee_count * base_sp_per_assignee
      For subsequent sprints: capacity = (previous_velocity * completion_ratio) * (new_assignee_count / previous_assignee_count)
    
    Args:
        space_id: The space/project ID
        new_assignee_count: Number of assignees on the new sprint
        base_sp_per_assignee: Default SP per assignee (typically 8)
    
    Returns:
        Recommended capacity in story points
    """
    db = get_database()
    
    # Check if there are any completed sprints
    previous_sprint = await db.sprints.find_one(
        {"space_id": space_id, "status": "Completed"},
        sort=[("updated_at", DESCENDING)]
    )
    
    # FIRST SPRINT: Use default calculation
    if not previous_sprint:
        return new_assignee_count * base_sp_per_assignee
    
    # SUBSEQUENT SPRINTS: Calculate based on historical performance
    previous_sprint_id = str(previous_sprint["_id"])
    previous_assignee_count = previous_sprint.get("assignee_count", 2)
    
    # Get all items from previous sprint to calculate completion ratio
    total_committed_sp = 0
    completed_sp = 0
    
    async for item in db.backlog_items.find({"sprint_id": previous_sprint_id}):
        sp = item.get("story_points", 0)
        total_committed_sp += sp
        if item.get("status") == "Done":
            completed_sp += sp
    
    # Calculate completion ratio (how well team executed)
    completion_ratio = (completed_sp / total_committed_sp) if total_committed_sp > 0 else 1.0
    
    # Calculate new capacity: scale by completion ratio and assignee count change
    # If team completed 80% with 3 people, and now we have 2 people:
    # new_capacity = 24 * 0.80 * (2/3) = 12.8 SP
    previous_capacity = previous_assignee_count * base_sp_per_assignee
    new_capacity = int(
        previous_capacity * completion_ratio * (new_assignee_count / previous_assignee_count)
    )
    
    # Ensure minimum capacity of (assignee_count * 4) to avoid overly pessimistic calculations
    min_capacity = new_assignee_count * 4
    return max(min_capacity, new_capacity)


async def check_sprint_capacity_status(sprint_id: str) -> dict:
    """
    Check current sprint capacity status.
    
    Returns:
      {
        "sprint_id": sprint_id,
        "team_capacity_sp": 16,
        "current_load_sp": 12,
        "remaining_capacity_sp": 4,
        "safe_limit_80_sp": 12.8,
        "capacity_percentage": 75.0,
        "status": "HEALTHY"  # HEALTHY, CAUTION, CRITICAL
      }
    
    Status codes:
      - HEALTHY: < 80% used
      - CAUTION: 80-100% used (warning shown to user)
      - CRITICAL: >= 100% used (block new additions)
    """
    db = get_database()
    
    if not ObjectId.is_valid(sprint_id):
        return None
    
    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        return None
    
    team_capacity_sp = sprint.get("team_capacity_sp", 16)
    
    # Calculate current load from all items in sprint
    current_load_sp = 0
    async for item in db.backlog_items.find({"sprint_id": sprint_id}):
        if item.get("status") != "Done":
            current_load_sp += item.get("story_points", 0)
    
    remaining_capacity = team_capacity_sp - current_load_sp
    capacity_percentage = (current_load_sp / team_capacity_sp * 100) if team_capacity_sp > 0 else 0
    safe_limit_80 = team_capacity_sp * 0.80
    
    # Determine status
    if capacity_percentage >= 100:
        status = "CRITICAL"
    elif capacity_percentage >= 80:
        status = "CAUTION"
    else:
        status = "HEALTHY"
    
    return {
        "sprint_id": sprint_id,
        "team_capacity_sp": team_capacity_sp,
        "current_load_sp": current_load_sp,
        "remaining_capacity_sp": max(0, remaining_capacity),
        "safe_limit_80_sp": round(safe_limit_80, 1),
        "capacity_percentage": round(capacity_percentage, 1),
        "status": status,
    }


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
    try:
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
    except (ValueError, TypeError):
        ideal_data = []

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

    try:
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
    except (ValueError, TypeError):
        burnup_data = []

    return {
        "sprint_name": sprint["name"],
        "total_points": total_points,
        "done_points": done_points,
        "burnup": burnup_data,
    }
