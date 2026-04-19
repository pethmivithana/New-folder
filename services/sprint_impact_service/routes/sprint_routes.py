from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId
from models import (
    Sprint, SprintCreate, SprintUpdate, SprintStatus,
    SprintStartRequest, SprintFinishRequest, AddAssigneeRequest,
    Status, DurationType,
)
from database import get_database

router = APIRouter()


def parse_datetime_string(date_str: str) -> datetime:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        pass
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        pass
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    raise ValueError(f"Unable to parse date string: {date_str}")


def sprint_helper(sprint) -> dict:
    def format_date(date_obj):
        if not date_obj:
            return None
        if isinstance(date_obj, str):
            return date_obj
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d')
        return None

    return {
        "id":             str(sprint["_id"]),
        "name":           sprint["name"],
        "goal":           sprint["goal"],
        "duration_type":  sprint["duration_type"],
        "start_date":     format_date(sprint.get("start_date")),
        "end_date":       format_date(sprint.get("end_date")),
        "space_id":       sprint["space_id"],
        "status":         sprint["status"],
        "assignees":      sprint.get("assignees", []),
        # NEW: return assignee_count alongside the raw assignee list
        "assignee_count": sprint.get("assignee_count", 2),
        "created_at":     sprint["created_at"],
        "updated_at":     sprint["updated_at"],
    }


def calculate_dates(duration_type: str, start_date=None, end_date=None):
    if duration_type == DurationType.CUSTOM:
        if isinstance(start_date, str):
            start_dt = parse_datetime_string(start_date)
        else:
            start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else datetime.utcnow()
        if isinstance(end_date, str):
            end_dt = parse_datetime_string(end_date)
        else:
            end_dt = datetime.combine(end_date, datetime.min.time()) if end_date else start_dt + timedelta(weeks=2)
        return start_dt, end_dt

    start = datetime.utcnow()
    duration_map = {
        DurationType.ONE_WEEK:    timedelta(weeks=1),
        DurationType.TWO_WEEKS:   timedelta(weeks=2),
        DurationType.THREE_WEEKS: timedelta(weeks=3),
        DurationType.FOUR_WEEKS:  timedelta(weeks=4),
    }
    return start, start + duration_map.get(duration_type, timedelta(weeks=2))


@router.post("/", response_model=Sprint)
async def create_sprint(sprint: SprintCreate):
    db = get_database()

    if not ObjectId.is_valid(sprint.space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")

    space = await db.spaces.find_one({"_id": ObjectId(sprint.space_id)})
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # ── NEW: Validate assignee_count against space.max_assignees ─────────────
    # Rules from spec:
    #   - Must be >= 2 (enforced by Pydantic field ge=2)
    #   - Must be <= space.max_assignees (the project-level cap)
    space_max = space.get("max_assignees", 1)
    if sprint.assignee_count > space_max:
        raise HTTPException(
            status_code=400,
            detail=(
                f"assignee_count ({sprint.assignee_count}) exceeds the space limit "
                f"of {space_max} assignees. Reduce the team size or increase the space limit."
            ),
        )
    # ge=2 is enforced by Pydantic, but add an explicit message for clarity
    if sprint.assignee_count < 2:
        raise HTTPException(
            status_code=400,
            detail="assignee_count must be at least 2.",
        )

    start_date, end_date = calculate_dates(
        sprint.duration_type, sprint.start_date, sprint.end_date
    )

    sprint_dict = sprint.dict()
    sprint_dict["start_date"]     = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
    sprint_dict["end_date"]       = end_date.strftime('%Y-%m-%d')   if isinstance(end_date,   datetime) else end_date
    sprint_dict["status"]         = SprintStatus.PLANNED
    sprint_dict["assignees"]      = []
    sprint_dict["assignee_count"] = sprint.assignee_count  # store planning headcount
    sprint_dict["created_at"]     = datetime.utcnow()
    sprint_dict["updated_at"]     = datetime.utcnow()

    result    = await db.sprints.insert_one(sprint_dict)
    new_sprint = await db.sprints.find_one({"_id": result.inserted_id})
    return sprint_helper(new_sprint)


@router.get("/space/{space_id}", response_model=List[Sprint])
async def get_sprints_by_space(space_id: str):
    db = get_database()
    sprints = []
    async for sprint in db.sprints.find({"space_id": space_id}).sort("created_at", -1):
        sprints.append(sprint_helper(sprint))
    return sprints


@router.get("/{sprint_id}", response_model=Sprint)
async def get_sprint(sprint_id: str):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")
    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint_helper(sprint)


@router.put("/{sprint_id}", response_model=Sprint)
async def update_sprint(sprint_id: str, sprint_update: SprintUpdate):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")

    update_data = {k: v for k, v in sprint_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # ── NEW: Validate updated assignee_count if provided ─────────────────────
    if "assignee_count" in update_data:
        sprint_doc = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
        if not sprint_doc:
            raise HTTPException(status_code=404, detail="Sprint not found")
        space = await db.spaces.find_one({"_id": ObjectId(sprint_doc["space_id"])})
        if space:
            space_max = space.get("max_assignees", 1)
            if update_data["assignee_count"] > space_max:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"assignee_count ({update_data['assignee_count']}) exceeds "
                        f"space limit of {space_max}."
                    ),
                )
            if update_data["assignee_count"] < 2:
                raise HTTPException(
                    status_code=400,
                    detail="assignee_count must be at least 2.",
                )

    update_data["updated_at"] = datetime.utcnow()
    result = await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sprint not found")

    updated_sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    return sprint_helper(updated_sprint)


@router.delete("/{sprint_id}")
async def delete_sprint(sprint_id: str):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")
    await db.backlog_items.update_many(
        {"sprint_id": sprint_id},
        {"$set": {"sprint_id": None, "status": Status.TODO}},
    )
    result = await db.sprints.delete_one({"_id": ObjectId(sprint_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return {"message": "Sprint deleted successfully"}


@router.post("/{sprint_id}/start")
async def start_sprint(sprint_id: str):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")

    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if sprint["status"] != SprintStatus.PLANNED:
        raise HTTPException(status_code=400, detail="Sprint is already started or completed")

    active_sprint = await db.sprints.find_one({
        "space_id": sprint["space_id"],
        "status":   SprintStatus.ACTIVE,
    })
    if active_sprint:
        raise HTTPException(status_code=400, detail="There is already an active sprint in this space")

    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"status": SprintStatus.ACTIVE, "updated_at": datetime.utcnow()}},
    )
    await db.backlog_items.update_many(
        {"sprint_id": sprint_id},
        {"$set": {"status": Status.TODO}},
    )
    updated_sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    return sprint_helper(updated_sprint)


@router.post("/{sprint_id}/finish")
async def finish_sprint(sprint_id: str, request: SprintFinishRequest):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")

    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if sprint["status"] != SprintStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Sprint is not active")

    incomplete_items = []
    async for item in db.backlog_items.find({
        "sprint_id": sprint_id,
        "status":    {"$ne": Status.DONE},
    }):
        incomplete_items.append(item)

    if incomplete_items:
        if request.move_incomplete_to and request.move_incomplete_to != "backlog":
            if not ObjectId.is_valid(request.move_incomplete_to):
                raise HTTPException(status_code=400, detail="Invalid target sprint ID")
            target_sprint = await db.sprints.find_one({"_id": ObjectId(request.move_incomplete_to)})
            if not target_sprint:
                raise HTTPException(status_code=404, detail="Target sprint not found")
            for item in incomplete_items:
                await db.backlog_items.update_one(
                    {"_id": item["_id"]},
                    {"$set": {"sprint_id": request.move_incomplete_to}},
                )
        else:
            for item in incomplete_items:
                await db.backlog_items.update_one(
                    {"_id": item["_id"]},
                    {"$set": {"sprint_id": None}},
                )

    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"status": SprintStatus.COMPLETED, "updated_at": datetime.utcnow()}},
    )
    updated_sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    return sprint_helper(updated_sprint)


@router.post("/{sprint_id}/assignees")
async def add_assignee(sprint_id: str, request: AddAssigneeRequest):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")
    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    space         = await db.spaces.find_one({"_id": ObjectId(sprint["space_id"])})
    space_max     = space["max_assignees"] if space else 999
    current       = sprint.get("assignees", [])

    if len(current) >= space_max:
        raise HTTPException(status_code=400, detail="Maximum number of assignees reached")
    if request.assignee_number in current:
        raise HTTPException(status_code=400, detail="Assignee already exists")

    current.append(request.assignee_number)
    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"assignees": current, "updated_at": datetime.utcnow()}},
    )
    updated_sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    return sprint_helper(updated_sprint)


@router.delete("/{sprint_id}/assignees/{assignee_number}")
async def remove_assignee(sprint_id: str, assignee_number: int):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")
    sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    current = sprint.get("assignees", [])
    if assignee_number not in current:
        raise HTTPException(status_code=404, detail="Assignee not found")

    current.remove(assignee_number)
    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"assignees": current, "updated_at": datetime.utcnow()}},
    )
    updated_sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    return sprint_helper(updated_sprint)