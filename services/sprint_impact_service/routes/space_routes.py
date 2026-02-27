from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from bson import ObjectId
from models import Space, SpaceCreate, SpaceUpdate
from database import get_database

router = APIRouter()

def space_helper(space) -> dict:
    return {
        "id":                  str(space["_id"]),
        "name":                space["name"],
        "description":         space["description"],
        "max_assignees":       space["max_assignees"],
        "focus_hours_per_day": space.get("focus_hours_per_day", 6.0),
        "created_at":          space["created_at"],
        "updated_at":          space["updated_at"],
    }

@router.post("/", response_model=Space)
async def create_space(space: SpaceCreate):
    db = get_database()
    space_dict = space.dict()
    space_dict["created_at"] = datetime.utcnow()
    space_dict["updated_at"] = datetime.utcnow()
    result = await db.spaces.insert_one(space_dict)
    new_space = await db.spaces.find_one({"_id": result.inserted_id})
    return space_helper(new_space)

@router.get("/", response_model=List[Space])
async def get_all_spaces():
    db = get_database()
    spaces = []
    async for space in db.spaces.find().sort("created_at", -1):
        spaces.append(space_helper(space))
    return spaces

@router.get("/{space_id}", response_model=Space)
async def get_space(space_id: str):
    db = get_database()
    if not ObjectId.is_valid(space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    space = await db.spaces.find_one({"_id": ObjectId(space_id)})
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space_helper(space)

@router.put("/{space_id}", response_model=Space)
async def update_space(space_id: str, space_update: SpaceUpdate):
    db = get_database()
    if not ObjectId.is_valid(space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    update_data = {k: v for k, v in space_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.utcnow()
    result = await db.spaces.update_one(
        {"_id": ObjectId(space_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Space not found")
    updated_space = await db.spaces.find_one({"_id": ObjectId(space_id)})
    return space_helper(updated_space)

@router.delete("/{space_id}")
async def delete_space(space_id: str):
    db = get_database()
    if not ObjectId.is_valid(space_id):
        raise HTTPException(status_code=400, detail="Invalid space ID")
    await db.sprints.delete_many({"space_id": space_id})
    await db.backlog_items.delete_many({"space_id": space_id})
    result = await db.spaces.delete_one({"_id": ObjectId(space_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Space not found")
    return {"message": "Space deleted successfully"}