from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from bson import ObjectId
from models import BacklogItem, BacklogItemCreate, BacklogItemUpdate, Status
from database import get_database

router = APIRouter()

def backlog_helper(item) -> dict:
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
        "updated_at": item["updated_at"]
    }

@router.post("/", response_model=BacklogItem)
async def create_backlog_item(item: BacklogItemCreate):
    db = get_database()
    
    # Validate space exists
    if not ObjectId.is_valid(item.space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    
    space = await db.spaces.find_one({"_id": ObjectId(item.space_id)})
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    # Validate sprint if provided
    if item.sprint_id:
        if not ObjectId.is_valid(item.sprint_id):
            raise HTTPException(status_code=400, detail="Invalid sprint ID")
        
        sprint = await db.sprints.find_one({"_id": ObjectId(item.sprint_id)})
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
    
    item_dict = item.dict()
    item_dict["status"] = Status.TODO
    item_dict["created_at"] = datetime.utcnow()
    item_dict["updated_at"] = datetime.utcnow()
    
    result = await db.backlog_items.insert_one(item_dict)
    new_item = await db.backlog_items.find_one({"_id": result.inserted_id})
    
    return backlog_helper(new_item)

@router.get("/space/{space_id}", response_model=List[BacklogItem])
async def get_backlog_items_by_space(space_id: str):
    db = get_database()
    if not ObjectId.is_valid(space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    
    items = []
    async for item in db.backlog_items.find({"space_id": space_id}).sort("created_at", -1):
        items.append(backlog_helper(item))
    return items

@router.get("/space/{space_id}/backlog", response_model=List[BacklogItem])
async def get_unassigned_backlog_items(space_id: str):
    db = get_database()
    if not ObjectId.is_valid(space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    
    items = []
    async for item in db.backlog_items.find({
        "space_id": space_id,
        "sprint_id": None
    }).sort("created_at", -1):
        items.append(backlog_helper(item))
    return items

@router.get("/sprint/{sprint_id}", response_model=List[BacklogItem])
async def get_backlog_items_by_sprint(sprint_id: str):
    db = get_database()
    if not ObjectId.is_valid(sprint_id):
        raise HTTPException(status_code=400, detail="Invalid sprint ID")
    
    items = []
    async for item in db.backlog_items.find({"sprint_id": sprint_id}).sort("created_at", -1):
        items.append(backlog_helper(item))
    return items

@router.get("/{item_id}", response_model=BacklogItem)
async def get_backlog_item(item_id: str):
    db = get_database()
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    item = await db.backlog_items.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    
    return backlog_helper(item)

@router.put("/{item_id}", response_model=BacklogItem)
async def update_backlog_item(item_id: str, item_update: BacklogItemUpdate):
    db = get_database()
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    update_data = {k: v for k, v in item_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Validate sprint if being updated
    if "sprint_id" in update_data and update_data["sprint_id"]:
        if not ObjectId.is_valid(update_data["sprint_id"]):
            raise HTTPException(status_code=400, detail="Invalid sprint ID")
        
        sprint = await db.sprints.find_one({"_id": ObjectId(update_data["sprint_id"])})
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.backlog_items.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    
    updated_item = await db.backlog_items.find_one({"_id": ObjectId(item_id)})
    return backlog_helper(updated_item)

@router.delete("/{item_id}")
async def delete_backlog_item(item_id: str):
    db = get_database()
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    result = await db.backlog_items.delete_one({"_id": ObjectId(item_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    
    return {"message": "Backlog item deleted successfully"}

@router.patch("/{item_id}/status")
async def update_item_status(item_id: str, status: Status):
    db = get_database()
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    result = await db.backlog_items.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    
    updated_item = await db.backlog_items.find_one({"_id": ObjectId(item_id)})
    return backlog_helper(updated_item)
