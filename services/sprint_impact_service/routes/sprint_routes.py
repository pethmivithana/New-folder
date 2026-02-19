from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId
from models import Sprint, SprintCreate, SprintUpdate, SprintStatus, SprintStartRequest, SprintFinishRequest, AddAssigneeRequest, Status, DurationType
from database import get_database

router = APIRouter()

def sprint_helper(sprint) -> dict:
    return {
        "id": str(sprint["_id"]),
        "name": sprint["name"],
        "goal": sprint["goal"],
        "duration_type": sprint["duration_type"],
        "start_date": sprint.get("start_date").strftime('%Y-%m-%d') if sprint.get("start_date") else None,
        "end_date": sprint.get("end_date").strftime('%Y-%m-%d') if sprint.get("end_date") else None,
        "space_id": sprint["space_id"],
        "status": sprint["status"],
        "assignees": sprint.get("assignees", []),
        "created_at": sprint["created_at"],
        "updated_at": sprint["updated_at"]
    }

def calculate_dates(duration_type: str, start_date=None, end_date=None):
    if duration_type == DurationType.CUSTOM:
        # Convert string dates to datetime objects
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else datetime.utcnow()
        
        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_dt = datetime.combine(end_date, datetime.min.time()) if end_date else start_dt + timedelta(weeks=2)
        
        return start_dt, end_dt
    
    start = datetime.utcnow()
    if duration_type == DurationType.ONE_WEEK:
        end = start + timedelta(weeks=1)
    elif duration_type == DurationType.TWO_WEEKS:
        end = start + timedelta(weeks=2)
    elif duration_type == DurationType.THREE_WEEKS:
        end = start + timedelta(weeks=3)
    elif duration_type == DurationType.FOUR_WEEKS:
        end = start + timedelta(weeks=4)
    else:
        end = start + timedelta(weeks=2)
    
    return start, end

@router.post("/", response_model=Sprint)
async def create_sprint(sprint: SprintCreate):
    db = get_database()
    
    # Validate space exists
    if not ObjectId.is_valid(sprint.space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    
    space = await db.spaces.find_one({"_id": ObjectId(sprint.space_id)})
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    start_date, end_date = calculate_dates(
        sprint.duration_type,
        sprint.start_date,
        sprint.end_date
    )
    
    sprint_dict = sprint.dict()
    sprint_dict["start_date"] = start_date
    sprint_dict["end_date"] = end_date
    sprint_dict["status"] = SprintStatus.PLANNED
    sprint_dict["assignees"] = []
    sprint_dict["created_at"] = datetime.utcnow()
    sprint_dict["updated_at"] = datetime.utcnow()
    
    result = await db.sprints.insert_one(sprint_dict)
    new_sprint = await db.sprints.find_one({"_id": result.inserted_id})
    
    return sprint_helper(new_sprint)

@router.get("/space/{space_id}", response_model=List[Sprint])
async def get_sprints_by_space(space_id: str):
    db = get_database()
    if not ObjectId.is_valid(space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    
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
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": update_data}
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
    
    # Move backlog items back to backlog
    await db.backlog_items.update_many(
        {"sprint_id": sprint_id},
        {"$set": {"sprint_id": None, "status": Status.TODO}}
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
    
    # Check if there's already an active sprint in the space
    active_sprint = await db.sprints.find_one({
        "space_id": sprint["space_id"],
        "status": SprintStatus.ACTIVE
    })
    
    if active_sprint:
        raise HTTPException(status_code=400, detail="There is already an active sprint in this space")
    
    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"status": SprintStatus.ACTIVE, "updated_at": datetime.utcnow()}}
    )
    
    # Set all backlog items in this sprint to "To Do" status
    await db.backlog_items.update_many(
        {"sprint_id": sprint_id},
        {"$set": {"status": Status.TODO}}
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
    
    # Get incomplete backlog items
    incomplete_items = []
    async for item in db.backlog_items.find({
        "sprint_id": sprint_id,
        "status": {"$ne": Status.DONE}
    }):
        incomplete_items.append(item)
    
    # Move incomplete items
    if incomplete_items:
        if request.move_incomplete_to and request.move_incomplete_to != "backlog":
            # Move to another sprint
            if not ObjectId.is_valid(request.move_incomplete_to):
                raise HTTPException(status_code=400, detail="Invalid target sprint ID")
            
            target_sprint = await db.sprints.find_one({"_id": ObjectId(request.move_incomplete_to)})
            if not target_sprint:
                raise HTTPException(status_code=404, detail="Target sprint not found")
            
            for item in incomplete_items:
                await db.backlog_items.update_one(
                    {"_id": item["_id"]},
                    {"$set": {"sprint_id": request.move_incomplete_to}}
                )
        else:
            # Move to backlog
            for item in incomplete_items:
                await db.backlog_items.update_one(
                    {"_id": item["_id"]},
                    {"$set": {"sprint_id": None}}
                )
    
    # Mark sprint as completed
    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"status": SprintStatus.COMPLETED, "updated_at": datetime.utcnow()}}
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
    
    # Get space to check max assignees
    space = await db.spaces.find_one({"_id": ObjectId(sprint["space_id"])})
    
    current_assignees = sprint.get("assignees", [])
    if len(current_assignees) >= space["max_assignees"]:
        raise HTTPException(status_code=400, detail="Maximum number of assignees reached")
    
    if request.assignee_number in current_assignees:
        raise HTTPException(status_code=400, detail="Assignee already exists")
    
    current_assignees.append(request.assignee_number)
    
    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"assignees": current_assignees, "updated_at": datetime.utcnow()}}
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
    
    current_assignees = sprint.get("assignees", [])
    if assignee_number not in current_assignees:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    current_assignees.remove(assignee_number)
    
    await db.sprints.update_one(
        {"_id": ObjectId(sprint_id)},
        {"$set": {"assignees": current_assignees, "updated_at": datetime.utcnow()}}
    )
    
    updated_sprint = await db.sprints.find_one({"_id": ObjectId(sprint_id)})
    return sprint_helper(updated_sprint)