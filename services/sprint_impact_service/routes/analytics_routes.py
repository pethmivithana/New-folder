from fastapi import APIRouter, HTTPException
from database import (
    get_sprint_by_id,
    get_space_velocity_history,
    calculate_burndown_data,
    calculate_burnup_data,
    get_completed_sprints,
)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3: Team Pace Calculation (for SP to Hours Translation)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/spaces/{space_id}/team-pace")
async def get_team_pace(space_id: str):
    """
    Calculate TEAM_PACE (story_points / dev_days) from historical sprint data.
    
    Returns:
      team_pace (float): Average SP completed per development day
      hours_per_sp (float): Derived conversion factor (8 / team_pace)
      sprints_analyzed (int): Number of sprints used in calculation
      metadata: Historical sprint summary
    """
    try:
        completed_sprints = await get_completed_sprints(space_id)
        
        if not completed_sprints:
            return {
                "team_pace": 1.0,
                "hours_per_sp": 8.0,
                "sprints_analyzed": 0,
                "metadata": "No completed sprints found. Using default pace (1.0 SP/day).",
            }
        
        total_completed_sp = sum(s.get("completed_sp", 0) for s in completed_sprints)
        total_dev_days = 0
        
        for sprint in completed_sprints:
            start = sprint.get("start_date")
            end = sprint.get("end_date")
            if start and end:
                # Simple day count (in production, account for weekends/holidays)
                from datetime import datetime
                if isinstance(start, str):
                    start = datetime.fromisoformat(start)
                if isinstance(end, str):
                    end = datetime.fromisoformat(end)
                days = (end - start).days
                if days > 0:
                    total_dev_days += days
        
        if total_dev_days == 0 or total_completed_sp == 0:
            return {
                "team_pace": 1.0,
                "hours_per_sp": 8.0,
                "sprints_analyzed": len(completed_sprints),
                "metadata": "Insufficient data for pace calculation. Using default pace (1.0 SP/day).",
            }
        
        team_pace = round(total_completed_sp / total_dev_days, 2)
        hours_per_sp = round(8.0 / team_pace, 2)
        
        return {
            "team_pace": team_pace,
            "hours_per_sp": hours_per_sp,
            "sprints_analyzed": len(completed_sprints),
            "total_completed_sp": total_completed_sp,
            "total_dev_days": total_dev_days,
            "metadata": f"Based on {len(completed_sprints)} completed sprints",
        }
    except Exception as e:
        print(f"Team pace calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sprints/{sprint_id}/burndown")
async def get_sprint_burndown(sprint_id: str):
    """Get burndown chart data for a sprint (logic-based, NO DL)"""
    try:
        data = await calculate_burndown_data(sprint_id)
        if not data:
            raise HTTPException(status_code=404, detail="Sprint not found")
        return data
    except HTTPException:
        raise
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
    except HTTPException:
        raise
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
                "velocity_data": [],
                "average_velocity": 0,
                "total_sprints": 0,
            }

        total_velocity = sum(v["velocity"] for v in velocity_history)
        avg_velocity = total_velocity / len(velocity_history)

        velocity_data = [
            {
                "sprint_name": v["sprint_name"],
                "completed_points": v["velocity"],
            }
            for v in velocity_history
        ]

        return {
            "velocity_data": velocity_data,
            "average_velocity": round(avg_velocity, 1),
            "total_sprints": len(velocity_history),
        }
    except Exception as e:
        print(f"Velocity chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
