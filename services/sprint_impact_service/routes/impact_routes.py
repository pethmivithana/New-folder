from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from impact_predictor import impact_predictor
from database import get_sprint_by_id, get_backlog_items_by_sprint
from datetime import datetime

router = APIRouter()


class ImpactAnalysisRequest(BaseModel):
    title: str
    description: str
    story_points: int
    priority: str
    sprint_id: str


@router.post("/impact/analyze")
async def analyze_impact(request: ImpactAnalysisRequest):
    """Analyze impact using DL models"""
    try:
        # Get sprint context
        sprint = await get_sprint_by_id(request.sprint_id)
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
        
        existing_items = await get_backlog_items_by_sprint(request.sprint_id)
        
        # Build sprint context
        sprint_context = {
            'sprint_id': sprint['id'],
            'start_date': sprint.get('start_date'),
            'end_date': sprint.get('end_date'),
            'current_load': sum(item.get('story_points', 0) for item in existing_items),
            'item_count': len(existing_items),
        }
        
        # Build item data
        item_data = {
            'title': request.title,
            'description': request.description,
            'story_points': request.story_points,
            'priority': request.priority,
            'type': 'Story',
        }
        
        # Get predictions from DL models
        result = impact_predictor.predict_all_impacts(item_data, sprint_context, existing_items)
        
        # Verify display object exists
        if 'display' not in result:
            print("ERROR: Display object missing from result!")
            print(f"Result keys: {result.keys()}")
        
        return result
        
    except Exception as e:
        print(f"Impact analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/impact/sprint/{sprint_id}/context")
async def get_sprint_context(sprint_id: str):
    """Get sprint context for impact analysis"""
    try:
        sprint = await get_sprint_by_id(sprint_id)
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")
        
        existing_items = await get_backlog_items_by_sprint(sprint_id)
        
        start = sprint.get('start_date')
        end = sprint.get('end_date')
        
        if start and end:
            if isinstance(start, str):
                start = datetime.strptime(start, '%Y-%m-%d')
            if isinstance(end, str):
                end = datetime.strptime(end, '%Y-%m-%d')
            now = datetime.utcnow()
            days_remaining = max(0, (end - now).days)
            days_since_start = max(0, (now - start).days)
            total_days = (end - start).days
            sprint_progress = round((days_since_start / max(1, total_days)) * 100, 1)
        else:
            days_remaining = 14
            sprint_progress = 0
        
        return {
            'sprint_id': sprint['id'],
            'sprint_name': sprint.get('name', ''),
            'current_load': sum(item.get('story_points', 0) for item in existing_items),
            'item_count': len(existing_items),
            'days_remaining': days_remaining,
            'sprint_progress': sprint_progress,
        }
        
    except Exception as e:
        print(f"Get sprint context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))