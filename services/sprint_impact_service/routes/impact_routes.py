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
# DeveloperExitRequest defined locally below

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
        sprint_id_str = str(completed_sprint["_id"])
        completed_items = await db.backlog_items.find(
            {"sprint_id": sprint_id_str, "status": "Done"}
        ).to_list(length=None)
        completed_sp = sum(item.get("story_points", 0) for item in completed_items)
        if completed_sp == 0:
            return fallback
        num_assignees = len(completed_sprint.get("assignees", [])) or 1
        hours_per_sp  = (num_assignees * sprint_duration_days * 8) / completed_sp
        daily_sp      = completed_sp / sprint_duration_days
        dynamic_focus = daily_sp * hours_per_sp / num_assignees
        return max(2.0, min(10.0, round(dynamic_focus, 1)))
    except Exception as e:
        print(f"Error calculating dynamic focus hours: {e}")
        return fallback


async def get_historical_velocity(space_id: str) -> float:
    """
    Return the average completed-sprint velocity (SP done) from the last
    3 completed sprints for this space.  Falls back to 30 SP if no history.

    FIX: Previously the code used max(total_sp_in_current_sprint, 30) as the
    velocity denominator, which made free_capacity always zero because
    velocity == current_load.  Real velocity must come from history.
    """
    try:
        db = get_database()
        velocities = []
        cursor = db.sprints.find(
            {"space_id": space_id, "status": "Completed"},
            sort=[("updated_at", DESCENDING)],
            limit=3,
        )
        async for sprint in cursor:
            sid = str(sprint["_id"])
            done_sp = 0
            async for item in db.backlog_items.find({"sprint_id": sid, "status": "Done"}):
                done_sp += item.get("story_points", 0)
            if done_sp > 0:
                velocities.append(done_sp)
        if velocities:
            return round(sum(velocities) / len(velocities), 1)
        return 30.0
    except Exception as e:
        print(f"Error fetching historical velocity: {e}")
        return 30.0


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


def _build_sprint_context(sprint: dict, existing_items: list, historical_velocity: float = 30.0) -> dict:
    """
    Build the sprint context dict passed to ML models and the decision engine.

    FIX — velocity and free_capacity:
      Old: team_velocity_14d = max(total_sp_in_sprint, 30)
           free_capacity     = velocity - current_load = 0 always

      New: team_velocity_14d = historical_velocity (average of last 3 completed sprints)
           done_sp           = sum of Done items in current sprint
           free_capacity     = total_sp - done_sp  (remaining uncommitted work)
           This is what the sprint ACTUALLY has left to absorb.
    """
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
    done_sp  = sum(
        item.get("story_points", 0) for item in existing_items
        if item.get("status") == "Done"
    )
    # Remaining capacity = total committed SP minus what is already Done
    # This is the SP the team still has to deliver, so new items compete for
    # the gap between this and the historical velocity.
    remaining_committed = total_sp - done_sp

    return {
        "sprint_id":               sprint["id"],
        "start_date":              start_str,
        "end_date":                end_str,
        "days_remaining":          days_remaining,
        "days_since_sprint_start": days_since_start,
        "sprint_progress":         sprint_progress,
        "sprint_load_7d":          total_sp,          # total planned SP (for ML features)
        "done_sp":                 done_sp,            # SP already completed
        "remaining_committed":     remaining_committed, # SP still in-flight
        "team_velocity_14d":       historical_velocity, # FIX: real history, not current load
        "current_load":            total_sp,
        "item_count":              len(existing_items),
        "assignee_count":          sprint.get("assignee_count", 2),
    }


def _compute_free_capacity(sprint_context: dict) -> float:
    """
    Free capacity = historical velocity - remaining committed SP.

    FIX: Old code used team_velocity_14d - sprint_load_7d, but both were
    the same number (max(total_sp, 30) vs total_sp), always giving 0.

    Example (Sprint 6 in FinTrack):
      historical_velocity   = 36 SP (avg of last 3 sprints)
      total_planned_sp      = 40 SP
      done_sp               = 21 SP
      remaining_committed   = 40 - 21 = 19 SP
      free_capacity         = 36 - 19 = 17 SP  ← team can absorb 17 more SP
    """
    return max(0.0, sprint_context["team_velocity_14d"] - sprint_context["remaining_committed"])


def _derive_risk_level_from_ml(schedule_risk: float, quality_risk: float) -> str:
    """
    Convert raw ML probabilities (0–100 scale) to LOW / MEDIUM / HIGH.

    schedule_risk and quality_risk are on a 0–100 scale as returned by the
    ML models (already multiplied by 100 in impact_predictor).
    """
    if schedule_risk > 55 or quality_risk > 60:
        return "HIGH"
    if schedule_risk > 30 or quality_risk > 35:
        return "MEDIUM"
    return "LOW"


def _derive_risk_level_for_history(schedule_risk_pct: float, quality_risk_pct: float) -> str:
    """For history table display. Inputs on 0–100 scale."""
    if schedule_risk_pct > 55 or quality_risk_pct > 60:
        return "critical"
    if schedule_risk_pct > 30 or quality_risk_pct > 35:
        return "high"
    if schedule_risk_pct > 15 or quality_risk_pct > 20:
        return "medium"
    return "low"


@router.get("/sprints/{sprint_id}/context")
async def get_sprint_context(sprint_id: str):
    """
    Returns accurate sprint context data for the frontend capacity bar and stat pills.

    FIX: Now returns real done_sp, remaining_committed, historical_velocity,
    and correctly computed free_capacity — not the old always-zero value.
    """
    sprint = await get_sprint_by_id(sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail=f"Sprint '{sprint_id}' not found.")

    existing_items    = await get_backlog_items_by_sprint(sprint_id)
    space_id          = sprint.get("space_id", "")
    historical_velocity = await get_historical_velocity(space_id) if space_id else 30.0
    ctx               = _build_sprint_context(sprint, existing_items, historical_velocity)
    free_cap          = _compute_free_capacity(ctx)

    return {
        "sprint_id":            sprint_id,
        "sprint_name":          sprint.get("name", ""),
        "sprint_status":        sprint.get("status", ""),
        "current_load":         ctx["current_load"],
        "done_sp":              ctx["done_sp"],
        "remaining_committed":  ctx["remaining_committed"],
        "item_count":           ctx["item_count"],
        "days_remaining":       ctx["days_remaining"],
        "days_since_start":     ctx["days_since_sprint_start"],
        "sprint_progress":      ctx["sprint_progress"],
        "team_velocity":        ctx["team_velocity_14d"],   # historical avg
        "free_capacity":        free_cap,
        "assignee_count":       ctx["assignee_count"],
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

    # 2. Space settings + historical velocity
    focus_hours_per_day  = 6.0
    risk_appetite        = "Standard"
    space_id             = sprint.get("space_id", "")
    historical_velocity  = 30.0

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

        # FIX: fetch real historical velocity separately so it's always available
        historical_velocity = await get_historical_velocity(space_id)

    # 3. Build sprint context with correct velocity
    sprint_context = _build_sprint_context(sprint, existing_items, historical_velocity)
    free_capacity  = _compute_free_capacity(sprint_context)

    item_data = {
        "title":        body.title,
        "description":  body.description,
        "type":         body.type,
        "priority":     body.priority,
        "story_points": body.story_points,
        "status":       "To Do",
        "sprint_id":    body.sprint_id,
    }

    # 4. ML predictions — use corrected sprint_context
    try:
        ml_result = impact_predictor.predict_all_impacts(
            item_data, sprint_context, existing_items,
            focus_hours_per_day=focus_hours_per_day,
            risk_appetite=risk_appetite,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ML prediction failed: {exc}")

    # Extract raw ML numbers — all on 0–100 % scale
    schedule_risk_pct  = ml_result.get("schedule_risk", {}).get("probability", 0.0)
    quality_risk_pct   = ml_result.get("quality_risk",  {}).get("probability", 0.0)
    velocity_change    = ml_result.get("productivity",  {}).get("velocity_change", 0.0)

    raw_ml = {
        "schedule_risk":   schedule_risk_pct,
        "quality_risk":    quality_risk_pct,
        "velocity_change": velocity_change,
        "days_remaining":  sprint_context["days_remaining"],
        "free_capacity":   free_capacity,
    }

    # 4a. Productivity saturation guard
    prod_raw      = ml_result.get("productivity", {})
    raw_log_preds = prod_raw.get("_raw_log_predictions", [])
    if raw_log_preds:
        max_raw    = max(raw_log_preds)
        saturation = check_productivity_saturation(max_raw)
        if saturation["saturated"] and "display" in ml_result and "productivity" in ml_result["display"]:
            ml_result["display"]["productivity"].update({
                "value":    "VOLATILE",
                "label":    "Model Saturated",
                "status":   "critical",
                "sub_text": saturation["sub_text"],
            })

    # 5. Derive risk level from ML predictions
    risk_level_str = _derive_risk_level_from_ml(schedule_risk_pct, quality_risk_pct)

    # 6. FIX: effort_sp must be in STORY POINTS not hours.
    #    Old: effort_sp = hours_median / focus_hours  → 3h/6h = 0.5 SP (always tiny)
    #    New: use body.story_points directly as the planning estimate.
    #         The ML effort model's hours output is used for display only.
    #         The decision engine rules operate in SP units.
    effort_sp = float(body.story_points)

    # 7. Decision engine — alignment_state defaults to STRONGLY_ALIGNED unless
    #    the frontend ran Phase 1 alignment check first and stored the result
    alignment_state = getattr(body, "alignment_state", None) or "STRONGLY_ALIGNED"

    decision = calculate_agile_recommendation(
        alignment_state = alignment_state,
        effort_sp       = effort_sp,
        free_capacity   = free_capacity,
        priority        = body.priority,
        risk_level      = risk_level_str,
    )

    # 8. Build ML signal summary to attach to the decision for the frontend
    #    This replaces the old explanation_generator text that was misleading.
    ml_signals_summary = {
        "schedule_risk_pct":  round(schedule_risk_pct, 1),
        "quality_risk_pct":   round(quality_risk_pct, 1),
        "velocity_change_pct": round(abs(velocity_change), 1),
        "effort_sp":           effort_sp,
        "free_capacity_sp":    round(free_capacity, 1),
        "historical_velocity": round(historical_velocity, 1),
        "risk_level":          risk_level_str,
        "days_remaining":      sprint_context["days_remaining"],
        "done_sp":             sprint_context["done_sp"],
        "remaining_committed": sprint_context["remaining_committed"],
    }

    # Keep explanation_generator for the detailed_explanation text only
    explanation = explanation_generator.generate_explanation({
        "recommendation_type": decision.action,
        "reasoning":           decision.reasoning,
        "target_ticket":       None,
        "impact_analysis": {
            "schedule_risk":   schedule_risk_pct,
            "quality_risk":    quality_risk_pct,
            "velocity_change": velocity_change,
            "days_remaining":  sprint_context["days_remaining"],
            "free_capacity":   free_capacity,
        },
        "action_plan":    {},
        "work_item_data": item_data,
    })

    # 9. Log to MongoDB
    log_id = None
    try:
        db             = get_database()
        resolved_risk  = _derive_risk_level_for_history(schedule_risk_pct, quality_risk_pct)
        result         = await db.recommendation_logs.insert_one({
            "sprint_id":                body.sprint_id,
            "space_id":                 space_id,
            "work_item_title":          body.title,
            "work_item_story_points":   body.story_points,
            "work_item_priority":       body.priority,
            "decision_output":          decision.action,
            "rule_triggered":           decision.rule_triggered,
            "recommendation_reasoning": decision.reasoning,
            "ml_schedule_risk":         schedule_risk_pct,
            "ml_quality_risk":          quality_risk_pct,
            "ml_velocity_change":       velocity_change,
            "focus_hours_per_day":      focus_hours_per_day,
            "risk_level":               risk_level_str,
            "resolved_risk_level":      resolved_risk,
            "effort_sp":                effort_sp,
            "free_capacity_sp":         round(free_capacity, 1),
            "historical_velocity":      round(historical_velocity, 1),
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
        "log_id":      log_id,
        "sprint_id":   body.sprint_id,
        "space_id":    space_id,
        "analysed_at": datetime.utcnow().isoformat(),
        "display":     ml_result.get("display", {}),
        "ml_raw": {
            "effort":        ml_result.get("effort",        {}),
            "schedule_risk": ml_result.get("schedule_risk", {}),
            "quality_risk":  ml_result.get("quality_risk",  {}),
            "productivity":  ml_result.get("productivity",  {}),
            "summary":       ml_result.get("summary",       {}),
        },
        "decision":          decision.to_dict(),
        "ml_signals":        ml_signals_summary,   # NEW: clean ML data for frontend
        "explanation":       dict(explanation),
        "sprint_context": {
            "current_load":         sprint_context["current_load"],
            "done_sp":              sprint_context["done_sp"],
            "remaining_committed":  sprint_context["remaining_committed"],
            "item_count":           sprint_context["item_count"],
            "days_remaining":       sprint_context["days_remaining"],
            "sprint_progress":      sprint_context["sprint_progress"],
            "free_capacity":        round(free_capacity, 1),
            "historical_velocity":  round(historical_velocity, 1),
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