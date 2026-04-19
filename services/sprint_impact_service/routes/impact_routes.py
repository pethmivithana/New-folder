from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from pymongo import DESCENDING

from database import get_database, get_sprint_by_id, get_backlog_items_by_sprint
from impact_predictor import impact_predictor
from decision_engine import (
    calculate_agile_recommendation,
    check_productivity_saturation,
)
from explanation_generator import explanation_generator
from input_validation import validate_requirement


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


async def calculate_dynamic_focus_hours(space_id: str, fallback: float = 6.0) -> float:
    try:
        db = get_database()
        completed_sprint = await db.sprints.find_one(
            {"space_id": space_id, "status": "Completed"},
            sort=[("updated_at", DESCENDING)],
        )
        if not completed_sprint:
            return fallback

        start_date = completed_sprint.get("start_date")
        end_date   = completed_sprint.get("end_date")
        if not start_date or not end_date:
            return fallback

        if isinstance(start_date, str):
            start_date = parse_datetime_string(start_date)
        if isinstance(end_date, str):
            end_date = parse_datetime_string(end_date)

        sprint_duration_days = max(1, (end_date - start_date).days)
        sprint_id_str        = str(completed_sprint["_id"])

        completed_items = await db.backlog_items.find(
            {"sprint_id": sprint_id_str, "status": "Done"}
        ).to_list(length=None)

        completed_sp = sum(item.get("story_points", 0) for item in completed_items)
        if completed_sp == 0:
            return fallback

        num_assignees      = len(completed_sprint.get("assignees", [])) or 1
        hours_per_sp       = (num_assignees * sprint_duration_days * 8) / completed_sp
        daily_sp           = completed_sp / sprint_duration_days
        dynamic_focus_hours = daily_sp * hours_per_sp / num_assignees
        return max(2.0, min(10.0, round(dynamic_focus_hours, 1)))
    except Exception as e:
        print(f"Error calculating dynamic focus hours: {e}")
        return fallback


async def get_space_velocity_history(space_id: str) -> dict:
    """
    Calculate team velocity from past sprints (completed in last 90 days).
    Returns: { 'avg_velocity': float, 'velocity_14d': float, 'count': int, 'fallback': bool }
    """
    try:
        db = get_database()
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        completed_sprints = await db.sprints.find(
            {"space_id": space_id, "status": "Completed", "updated_at": {"$gte": cutoff_date}}
        ).sort("updated_at", DESCENDING).to_list(length=20)
        
        if not completed_sprints:
            return {"avg_velocity": None, "velocity_14d": None, "count": 0, "fallback": True}
        
        velocities = []
        for sprint in completed_sprints:
            sprint_id_str = str(sprint["_id"])
            completed_items = await db.backlog_items.find(
                {"sprint_id": sprint_id_str, "status": "Done"}
            ).to_list(length=None)
            velocity = sum(item.get("story_points", 0) for item in completed_items)
            velocities.append(velocity)
        
        avg_velocity = sum(velocities) / len(velocities) if velocities else None
        # Most recent 2 sprints (~14 days)
        velocity_14d = sum(velocities[:2]) / 2 if len(velocities) >= 2 else avg_velocity
        
        return {
            "avg_velocity": round(avg_velocity, 1) if avg_velocity else None,
            "velocity_14d": round(velocity_14d, 1) if velocity_14d else None,
            "count": len(velocities),
            "fallback": False
        }
    except Exception as e:
        print(f"Error calculating velocity history: {e}")
        return {"avg_velocity": None, "velocity_14d": None, "count": 0, "fallback": True}


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
            start = parse_datetime_string(start_str)
            end   = parse_datetime_string(end_str)
            now   = datetime.utcnow()
            days_remaining   = max(0, (end - now).days)
            days_since_start = max(0, (now - start).days)
            total_days       = max(1, (end - start).days)
            sprint_progress  = round((days_since_start / total_days) * 100, 1)
        except (ValueError, TypeError):
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
        # NEW: pass assignee_count through so impact_predictor can use it
        "assignee_count":          sprint.get("assignee_count", 2),
    }


def _derive_risk_level_from_ml(schedule_risk: float, quality_risk: float) -> str:
    """
    Convert raw ML probabilities (0–100 scale) to LOW/MEDIUM/HIGH string
    used by the decision engine.
    """
    if schedule_risk > 55 or quality_risk > 60:
        return "HIGH"
    if schedule_risk > 35 or quality_risk > 40:
        return "MEDIUM"
    return "LOW"


def _derive_risk_level_for_history(schedule_risk: float, quality_risk: float) -> str:
    """For history display (stored as critical/high/medium/low)."""
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
        # NEW: expose assignee_count in context
        "assignee_count":  ctx["assignee_count"],
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
        # Use stored risk level if available (set at analysis time), else re-derive
        stored_risk = doc.get("resolved_risk_level")
        if stored_risk:
            risk = stored_risk
        else:
            risk = _derive_risk_level_for_history(
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
            # CHANGE: single "decision_output" field instead of two contradictory ones
            "recommendation": doc.get("decision_output", doc.get("suggested_action", "")),
            "taken_action":   doc.get("taken_action"),
            "accepted":       doc.get("accepted"),
            "date":           created.isoformat() if isinstance(created, datetime) else str(created or ""),
        })

    return {"history": logs, "total": len(logs)}


@router.post("/analyze")
async def analyze_impact(body: AnalyzeRequest):
    # 0. Input validation
    is_valid, error_message = validate_requirement(body.title, body.description)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # 1. Fetch sprint and items
    sprint = await get_sprint_by_id(body.sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail=f"Sprint '{body.sprint_id}' not found.")

    existing_items = await get_backlog_items_by_sprint(body.sprint_id)
    sprint_context = _build_sprint_context(sprint, existing_items)

    # 2. Space settings
    focus_hours_per_day = 6.0
    risk_appetite       = "Standard"
    space_id            = sprint.get("space_id", "")
    if space_id:
        try:
            db    = get_database()
            space = await db.spaces.find_one({"_id": ObjectId(space_id)}) if ObjectId.is_valid(space_id) else None
            if space:
                risk_appetite       = space.get("risk_appetite", "Standard")
                focus_hours_per_day = await calculate_dynamic_focus_hours(
                    space_id,
                    fallback=float(space.get("focus_hours_per_day", 6.0)),
                )
        except Exception as e:
            print(f"Error fetching space settings: {e}")

    item_data = {
        "title":        body.title,
        "description":  body.description,
        "type":         body.type,
        "priority":     body.priority,
        "story_points": body.story_points,
        "status":       "To Do",
        "sprint_id":    body.sprint_id,
    }

    # 3. ML predictions
    try:
        ml_result = impact_predictor.predict_all_impacts(
            item_data, sprint_context, existing_items,
            focus_hours_per_day=focus_hours_per_day,
            risk_appetite=risk_appetite,
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

    # 3a. Productivity saturation guard — replaces the fabricated "-99% Drop"
    prod_raw = ml_result.get("productivity", {})
    raw_log_preds = prod_raw.get("_raw_log_predictions", [])  # list of raw log values from ensemble
    saturation_status = "NORMAL"
    if raw_log_preds:
        max_raw = max(raw_log_preds)
        saturation = check_productivity_saturation(max_raw)
        if saturation["saturated"]:
            saturation_status = "CRITICAL_VOLATILITY"
            # Override the display metric with VOLATILE state
            if "display" in ml_result and "productivity" in ml_result["display"]:
                ml_result["display"]["productivity"].update({
                    "value":    "VOLATILE",
                    "label":    "Model Saturated",
                    "status":   "critical",
                    "sub_text": saturation["sub_text"],
                    "saturation_status": saturation_status,
                })

    # 4. Phase 1 — Sprint alignment (if available from prior check)
    # The alignment_state is passed from the frontend when the user has already
    # run "Check Sprint Alignment". If not provided, default to STRONGLY_ALIGNED
    # so capacity rules still apply (alignment check is a separate optional step).
    alignment_state = body.__dict__.get("alignment_state", "STRONGLY_ALIGNED")

    # 5. UNIFIED Decision Engine — replaces both old RecommendationEngine AND old decision_engine
    risk_level_str = _derive_risk_level_from_ml(
        raw_ml["schedule_risk"],
        raw_ml["quality_risk"],
    )
    effort_sp     = ml_result.get("effort", {}).get("hours_median", body.story_points * 6) / max(focus_hours_per_day, 1)
    free_capacity = raw_ml["free_capacity"]

    decision = calculate_agile_recommendation(
        alignment_state = alignment_state,
        effort_sp       = effort_sp,
        free_capacity   = free_capacity,
        priority        = body.priority,
        risk_level      = risk_level_str,
    )

    # Generate explanation (kept for UI detail panel)
    explanation = explanation_generator.generate_explanation({
        "recommendation_type": decision.action,
        "reasoning":           decision.reasoning,
        "target_ticket":       None,
        "impact_analysis":     raw_ml,
        "action_plan":         {},
        "work_item_data":      item_data,
    })

    # 6. Log to MongoDB — single decision_output field (no more dual contradictory fields)
    log_id = None
    try:
        db = get_database()
        # Resolve and STORE the risk level so history display is consistent
        resolved_risk = _derive_risk_level_for_history(
            raw_ml["schedule_risk"] / 100,
            raw_ml["quality_risk"]  / 100,
        )
        result = await db.recommendation_logs.insert_one({
            "sprint_id":                body.sprint_id,
            "space_id":                 space_id,
            "work_item_title":          body.title,
            "work_item_story_points":   body.story_points,
            "work_item_priority":       body.priority,
            # CHANGE: single field — was two fields (suggested_action + decision engine output)
            "decision_output":          decision.action,
            "rule_triggered":           decision.rule_triggered,
            "recommendation_reasoning": decision.reasoning,
            "ml_schedule_risk":         raw_ml["schedule_risk"],
            "ml_quality_risk":          raw_ml["quality_risk"],
            "ml_velocity_change":       raw_ml["velocity_change"],
            "focus_hours_per_day":      focus_hours_per_day,
            "risk_level":               risk_level_str,
            # Store resolved risk so history never re-derives with wrong thresholds
            "resolved_risk_level":      resolved_risk,
            # NEW: Capture productivity model saturation status
            "saturation_status":        saturation_status,
            "accepted":                 None,
            "taken_action":             None,
            "user_rating":              None,
            "created_at":               datetime.utcnow(),
            "updated_at":               datetime.utcnow(),
        })
        log_id = str(result.inserted_id)
    except Exception as e:
        print(f"Log write failed: {e}")

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
        # CHANGE: single "decision" field instead of "recommendation" + "decision" (was contradictory)
        "decision":     decision.to_dict(),
        "explanation":  dict(explanation),
        "sprint_context": {
            "current_load":         sprint_context["current_load"],
            "item_count":           sprint_context["item_count"],
            "days_remaining":       sprint_context["days_remaining"],
            "sprint_progress":      sprint_context["sprint_progress"],
            "free_capacity":        raw_ml["free_capacity"],
            "focus_hours_per_day":  focus_hours_per_day,
            "assignee_count":       sprint_context["assignee_count"],
        },
    }


@router.patch("/logs/{log_id}/feedback")
async def record_feedback(log_id: str, body: FeedbackRequest):
    if not ObjectId.is_valid(log_id):
        raise HTTPException(status_code=400, detail="Invalid log_id.")

    db     = get_database()
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


