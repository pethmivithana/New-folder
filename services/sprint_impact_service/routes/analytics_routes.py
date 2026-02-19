from fastapi import APIRouter, HTTPException
from database import (
    get_sprint_by_id,
    get_space_velocity_history,
    calculate_burndown_data,
    calculate_burnup_data
)

router = APIRouter()


@router.get("/sprints/{sprint_id}/burndown")
async def get_sprint_burndown(sprint_id: str):
    """Get burndown chart data for a sprint (logic-based, NO DL)"""
    try:
        data = await calculate_burndown_data(sprint_id)
        if not data:
            raise HTTPException(status_code=404, detail="Sprint not found")
        return data
    except Exception as e:
        print(f"Burndown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sprints/{sprint_id}/burnup")
async def get_sprint_burnup(sprint_id: str):
    """Get burnup chart data for a sprint (logic-based, NO DL)"""
    try:
        data = await calculate_burnup_data(sprint_id)
        if not data:
            raise HTTPException(status_code=404, detail="Sprint not found")
        return data
    except Exception as e:
        print(f"Burnup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spaces/{space_id}/velocity")
async def get_velocity_chart(space_id: str):
    """Get velocity chart data for a space (logic-based, NO DL)"""
    try:
        velocity_history = await get_space_velocity_history(space_id, limit=10)
        
        if not velocity_history:
            return {
                'velocity_data': [],
                'average_velocity': 0,
                'total_sprints': 0
            }
        
        total_velocity = sum(v['velocity'] for v in velocity_history)
        avg_velocity = total_velocity / len(velocity_history) if velocity_history else 0
        
        # Format for chart
        velocity_data = [
            {
                'sprint_name': v['sprint_name'],
                'completed_points': v['velocity']
            }
            for v in velocity_history
        ]
        
        return {
            'velocity_data': velocity_data,
            'average_velocity': round(avg_velocity, 1),
            'total_sprints': len(velocity_history)
        }
    except Exception as e:
        print(f"Velocity chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))