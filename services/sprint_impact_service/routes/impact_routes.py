from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from pymongo import DESCENDING

from database import get_database, get_sprint_by_id, get_backlog_items_by_sprint
from impact_predictor import impact_predictor
from recommendation_engine import recommendation_engine
from explanation_generator import explanation_generator

router = APIRouter()


class AnalyzeRequest(BaseModel):
    sprint_id:    str
    title:        str = Field(..., min_length=1, max_length=300)
    description:  str = Field(default="")
    story_points: int = Field(default=5, ge=1, le=100)
    priority:     str = Field(default="Medium")
    type:         str = Field(default="Task")


class FeedbackRequest(BaseModel):
    accepted:     Optional[bool] = None
    taken_action: Optional[str]  = None
    user_rating:  Optional[int]  = Field(default=None, ge=1, le=5)
    user_comment: Optional[str]  = None


def _build_sprint_context(sprint: dict, existing_items: list) -> dict:
    start_str = sprint.get("start_date")
    end_str   = sprint.get("end_date")
    days_remaining   = 14
    days_since_start = 0
    sprint_progress  = 0.0

    if start_str and end_str:
        try:
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end   = datetime.strptime(end_str,   "%Y-%m-%d")
            now   = datetime.utcnow()
            days_remaining   = max(0, (end - now).days)
            days_since_start = max(0, (now - start).days)
            total_days       = max(1, (end - start).days)
            sprint_progress  = round((days_since_start / total_days) * 100, 1)
        except ValueError:
            pass

    total_sp = sum(item.get("story_points", 0) for item in existing_items)
    velocity = max(total_sp, 30)

    return {
        "sprint_id":               sprint["id"],
        "start_date":              start_str,
        "end_date":                end_str,
        "days_remaining":          days_remaining,
        "days_since_sprint_start": days_since_start,
        "sprint_progress":         sprint_progress,
        "sprint_load_7d":          total_sp,
        "team_velocity_14d":       velocity,
        "current_load":            total_sp,
        "item_count":              len(existing_items),
    }


def _derive_risk_level(schedule_risk: float, quality_risk: float) -> str:
    if schedule_risk > 0.55 or quality_risk > 0.60:
        return "critical"
    if schedule_risk > 0.35 or quality_risk > 0.40:
        return "high"
    if schedule_risk > 0.20 or quality_risk > 0.25:
        return "medium"
    return "low"


@router.get("/sprints/{sprint_id}/context")
async def get_sprint_context(sprint_id: str):
    sprint = await get_sprint_by_id(sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail=f"Sprint '{sprint_id}' not found.")

    existing_items = await get_backlog_items_by_sprint(sprint_id)
    ctx = _build_sprint_context(sprint, existing_items)

    return {
        "sprint_id":       sprint_id,
        "sprint_name":     sprint.get("name", ""),
        "sprint_status":   sprint.get("status", ""),
        "current_load":    ctx["current_load"],
        "item_count":      ctx["item_count"],
        "days_remaining":  ctx["days_remaining"],
        "sprint_progress": ctx["sprint_progress"],
        "team_velocity":   ctx["team_velocity_14d"],
        "free_capacity":   max(0, ctx["team_velocity_14d"] - ctx["current_load"]),
    }


@router.get("/history/{space_id}")
async def get_analysis_history(
    space_id: str,
    limit: int = Query(default=50, le=200),
):
    db = get_database()

    sprint_ids: list[str]        = []
    sprint_names: dict[str, str] = {}

    async for s in db.sprints.find({"space_id": space_id}, {"_id": 1, "name": 1}):
        sid = str(s["_id"])
        sprint_ids.append(sid)
        sprint_names[sid] = s.get("name", "Unknown Sprint")

    if not sprint_ids:
        return {"history": [], "total": 0}

    logs   = []
    cursor = (
        db.recommendation_logs
        .find({"sprint_id": {"$in": sprint_ids}})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )

    async for doc in cursor:
        sprint_id = doc.get("sprint_id", "")
        risk      = _derive_risk_level(
            doc.get("ml_schedule_risk", 0.0),
            doc.get("ml_quality_risk",  0.0),
        )
        created = doc.get("created_at")
        logs.append({
            "log_id":         str(doc["_id"]),
            "sprint_id":      sprint_id,
            "sprint_name":    sprint_names.get(sprint_id, "Unknown Sprint"),
            "item":           doc.get("work_item_title", ""),
            "story_points":   doc.get("work_item_story_points", 0),
            "priority":       doc.get("work_item_priority", ""),
            "risk":           risk,
            "recommendation": doc.get("suggested_action", ""),
            "taken_action":   doc.get("taken_action"),
            "accepted":       doc.get("accepted"),
            "date":           created.isoformat() if isinstance(created, datetime) else str(created or ""),
        })

    return {"history": logs, "total": len(logs)}


@router.post("/analyze")
async def analyze_impact(body: AnalyzeRequest):
    # 1. Fetch sprint
    sprint = await get_sprint_by_id(body.sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail=f"Sprint '{body.sprint_id}' not found.")

    existing_items = await get_backlog_items_by_sprint(body.sprint_id)
    sprint_context = _build_sprint_context(sprint, existing_items)

    # 2. Fetch space to get focus_hours_per_day
    focus_hours_per_day = 6.0
    space_id = sprint.get("space_id", "")
    if space_id:
        try:
            db    = get_database()
            space = await db.spaces.find_one({"_id": ObjectId(space_id)}) if ObjectId.is_valid(space_id) else None
            if space:
                focus_hours_per_day = float(space.get("focus_hours_per_day", 6.0))
        except Exception:
            pass  # fall back to default if lookup fails

    item_data = {
        "title":        body.title,
        "description":  body.description,
        "type":         body.type,
        "priority":     body.priority,
        "story_points": body.story_points,
        "status":       "To Do",
        "sprint_id":    body.sprint_id,
    }

    # 3. ML predictions — pass focus_hours_per_day into the predictor
    try:
        ml_result = impact_predictor.predict_all_impacts(
            item_data, sprint_context, existing_items,
            focus_hours_per_day=focus_hours_per_day,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ML prediction failed: {exc}")

    raw_ml = {
        "schedule_risk":   ml_result.get("schedule_risk", {}).get("probability", 0),
        "quality_risk":    ml_result.get("quality_risk",  {}).get("probability", 0),
        "velocity_change": ml_result.get("productivity",  {}).get("velocity_change", 0),
        "days_remaining":  sprint_context["days_remaining"],
        "free_capacity":   max(0, sprint_context["team_velocity_14d"] - sprint_context["sprint_load_7d"]),
    }

    # 4. Recommendation + explanation
    recommendation = recommendation_engine.generate_recommendation(
        new_ticket     = item_data,
        sprint_context = sprint_context,
        active_items   = existing_items,
        ml_predictions = raw_ml,
    )
    explanation = explanation_generator.generate_explanation({
        "recommendation_type": recommendation.get("recommendation_type", "DEFER"),
        "reasoning":           recommendation.get("reasoning", ""),
        "target_ticket":       recommendation.get("target_ticket"),
        "impact_analysis":     raw_ml,
        "action_plan":         recommendation.get("action_plan", {}),
        "work_item_data":      item_data,
    })

    # 5. Log to MongoDB
    log_id = None
    try:
        db = get_database()
        result = await db.recommendation_logs.insert_one({
            "sprint_id":                body.sprint_id,
            "space_id":                 space_id,
            "work_item_title":          body.title,
            "work_item_story_points":   body.story_points,
            "work_item_priority":       body.priority,
            "suggested_action":         recommendation.get("recommendation_type"),
            "recommendation_reasoning": recommendation.get("reasoning", ""),
            "target_ticket_id":         (recommendation.get("target_ticket") or {}).get("id"),
            "target_ticket_title":      (recommendation.get("target_ticket") or {}).get("title"),
            "ml_schedule_risk":         raw_ml["schedule_risk"],
            "ml_quality_risk":          raw_ml["quality_risk"],
            "ml_velocity_change":       raw_ml["velocity_change"],
            "focus_hours_per_day":      focus_hours_per_day,
            "accepted":                 None,
            "taken_action":             None,
            "user_rating":              None,
            "created_at":               datetime.utcnow(),
            "updated_at":               datetime.utcnow(),
        })
        log_id = str(result.inserted_id)
    except Exception:
        pass

    return {
        "log_id":       log_id,
        "sprint_id":    body.sprint_id,
        "space_id":     space_id,
        "analysed_at":  datetime.utcnow().isoformat(),
        "display":      ml_result.get("display", {}),
        "ml_raw": {
            "effort":        ml_result.get("effort",        {}),
            "schedule_risk": ml_result.get("schedule_risk", {}),
            "quality_risk":  ml_result.get("quality_risk",  {}),
            "productivity":  ml_result.get("productivity",  {}),
            "summary":       ml_result.get("summary",       {}),
        },
        "recommendation": recommendation,
        "explanation":    dict(explanation),
        "sprint_context": {
            "current_load":         sprint_context["current_load"],
            "item_count":           sprint_context["item_count"],
            "days_remaining":       sprint_context["days_remaining"],
            "sprint_progress":      sprint_context["sprint_progress"],
            "free_capacity":        raw_ml["free_capacity"],
            "focus_hours_per_day":  focus_hours_per_day,
        },
    }


@router.patch("/logs/{log_id}/feedback")
async def record_feedback(log_id: str, body: FeedbackRequest):
    if not ObjectId.is_valid(log_id):
        raise HTTPException(status_code=400, detail="Invalid log_id.")

    db = get_database()
    update = {"updated_at": datetime.utcnow()}
    if body.accepted     is not None: update["accepted"]     = body.accepted
    if body.taken_action is not None: update["taken_action"] = body.taken_action
    if body.user_rating  is not None: update["user_rating"]  = body.user_rating
    if body.user_comment is not None: update["user_comment"] = body.user_comment

    if len(update) == 1:
        raise HTTPException(status_code=400, detail="No feedback fields provided.")

    result = await db.recommendation_logs.update_one(
        {"_id": ObjectId(log_id)},
        {"$set": update},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Log entry not found.")

    return {"ok": True, "log_id": log_id}