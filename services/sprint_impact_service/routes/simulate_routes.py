"""
routes/simulate_routes.py
──────────────────────────
FastAPI router for the What-If simulation endpoint.

POST /api/sprints/{sprint_id}/simulate-change

Accepts a new ticket's data, runs the ML impact models and the
Recommendation Engine, and returns a before/after comparison — without
writing anything to the database.  Pure read + compute.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

# Internal dependencies (already in your project)
from database import get_sprint_by_id, get_backlog_items_by_sprint
from impact_predictor import impact_predictor
from recommendation_engine import recommendation_engine
from explanation_generator import explanation_generator, ExplanationResult

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response Schemas
# ──────────────────────────────────────────────────────────────────────────────

class NewTicketInput(BaseModel):
    """The hypothetical ticket the user wants to evaluate."""
    title:        str   = Field(..., min_length=1, max_length=300, examples=["Add Stripe payment gateway"])
    description:  str   = Field(default="", max_length=4000)
    story_points: int   = Field(..., ge=1, le=100, examples=[8])
    priority:     str   = Field(default="Medium", examples=["High"])
    type:         str   = Field(default="Task",   examples=["Story"])

    class Config:
        json_schema_extra = {
            "example": {
                "title":        "Add Stripe payment gateway",
                "description":  "Integrate Stripe Checkout and handle webhooks for payment confirmation.",
                "story_points": 8,
                "priority":     "High",
                "type":         "Story",
            }
        }


# ── Metric card (shared by both before and after states) ─────────────────────

class MetricCard(BaseModel):
    value:   str  = Field(description="Display value, e.g. '18h / 48h Remaining'")
    label:   str  = Field(description="Short label, e.g. 'Effort Estimate'")
    status:  str  = Field(description="'safe' | 'warning' | 'critical'")
    sub_text: str = Field(description="One-sentence context sentence")


class RiskMetrics(BaseModel):
    effort:       MetricCard
    schedule:     MetricCard
    productivity: MetricCard
    quality:      MetricCard


# ── Current sprint state (before adding the ticket) ──────────────────────────

class CurrentState(BaseModel):
    sprint_id:        str
    sprint_name:      str
    total_items:      int
    total_story_points: int
    days_remaining:   int | float
    sprint_progress:  float   = Field(description="0.0–100.0 percentage complete")
    hours_remaining:  float


# ── Simulated state (after adding the ticket) ────────────────────────────────

class SimulatedState(BaseModel):
    new_total_story_points: int
    new_hours_required:     float
    risk_metrics:           RiskMetrics
    recommendation_action:  str   = Field(description="ADD | SWAP | DEFER | SPLIT")
    short_explanation:      str
    detailed_explanation:   str
    confidence_color:       str   = Field(description="'green' | 'yellow' | 'red'")
    action_verb:            str
    action_plan:            dict[str, Any] = Field(default_factory=dict)
    target_ticket:          Optional[dict[str, Any]] = None


# ── Full simulation response ──────────────────────────────────────────────────

class SimulationResponse(BaseModel):
    simulated_at:    datetime = Field(default_factory=datetime.utcnow)
    sprint_id:       str
    ticket_evaluated: NewTicketInput
    current_state:   CurrentState
    simulated_state: SimulatedState

    class Config:
        json_schema_extra = {
            "example": {
                "simulated_at": "2025-01-15T10:30:00Z",
                "sprint_id":    "664f1a2b3c4d5e6f7a8b9c0d",
                "ticket_evaluated": {
                    "title":        "Add Stripe payment gateway",
                    "story_points": 8,
                    "priority":     "High",
                    "type":         "Story",
                },
                "current_state": {
                    "sprint_id":    "664f1a2b3c4d5e6f7a8b9c0d",
                    "sprint_name":  "Sprint 4",
                    "total_items":  12,
                    "total_story_points": 34,
                    "days_remaining": 5,
                    "sprint_progress": 64.3,
                    "hours_remaining": 30.0,
                },
                "simulated_state": {
                    "new_total_story_points": 42,
                    "new_hours_required":     48.5,
                    "recommendation_action":  "DEFER",
                    "short_explanation":      "⏸ Defer to Next Sprint",
                    "confidence_color":       "red",
                    "action_verb":            "Defer to Backlog",
                },
            }
        }


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

WORK_HOURS_PER_DAY = 6


def _build_current_state(sprint: dict, existing_items: list[dict]) -> CurrentState:
    """Compute the sprint's current load metrics."""
    start_str = sprint.get("start_date")
    end_str   = sprint.get("end_date")

    days_remaining  = 14
    sprint_progress = 0.0

    if start_str and end_str:
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end   = datetime.strptime(end_str,   "%Y-%m-%d")
        now   = datetime.utcnow()
        days_remaining  = max(0, (end - now).days)
        days_since_start = max(0, (now - start).days)
        total_days       = max(1, (end - start).days)
        sprint_progress  = round((days_since_start / total_days) * 100, 1)

    total_sp       = sum(item.get("story_points", 0) for item in existing_items)
    hours_remaining = days_remaining * WORK_HOURS_PER_DAY

    return CurrentState(
        sprint_id           = sprint["id"],
        sprint_name         = sprint.get("name", ""),
        total_items         = len(existing_items),
        total_story_points  = total_sp,
        days_remaining      = days_remaining,
        sprint_progress     = sprint_progress,
        hours_remaining     = float(hours_remaining),
    )


def _build_sprint_context(sprint: dict, existing_items: list[dict]) -> dict:
    """Build the context dict expected by the ML models."""
    start_str = sprint.get("start_date")
    end_str   = sprint.get("end_date")
    days_remaining   = 14
    days_since_start = 0
    sprint_progress  = 0.0

    if start_str and end_str:
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end   = datetime.strptime(end_str,   "%Y-%m-%d")
        now   = datetime.utcnow()
        days_remaining   = max(0, (end - now).days)
        days_since_start = max(0, (now - start).days)
        total_days       = max(1, (end - start).days)
        sprint_progress  = days_since_start / total_days

    total_sp = sum(item.get("story_points", 0) for item in existing_items)

    return {
        "sprint_id":              sprint["id"],
        "start_date":             start_str,
        "end_date":               end_str,
        "days_remaining":         days_remaining,
        "days_since_sprint_start": days_since_start,
        "sprint_progress":        sprint_progress,
        "sprint_load_7d":         total_sp,
        "team_velocity_14d":      max(total_sp, 30),   # floor at 30 SP
        "current_load":           total_sp,
        "item_count":             len(existing_items),
    }


def _display_to_metric_card(display_metric: dict) -> MetricCard:
    """Convert an impact_predictor display sub-object into a MetricCard."""
    return MetricCard(
        value    = display_metric.get("value",    "N/A"),
        label    = display_metric.get("label",    ""),
        status   = display_metric.get("status",   "warning"),
        sub_text = display_metric.get("sub_text", ""),
    )


def _build_risk_metrics_from_display(display: dict) -> RiskMetrics:
    return RiskMetrics(
        effort       = _display_to_metric_card(display.get("effort",       {})),
        schedule     = _display_to_metric_card(display.get("schedule",     {})),
        productivity = _display_to_metric_card(display.get("productivity", {})),
        quality      = _display_to_metric_card(display.get("quality",      {})),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{sprint_id}/simulate-change",
    response_model=SimulationResponse,
    summary="What-If simulation: assess the impact of adding a new ticket",
    description=(
        "Runs the ML impact models and Recommendation Engine against the current "
        "sprint state **without persisting anything**.  Returns a before/after "
        "comparison so the PM can decide whether to proceed."
    ),
)
async def simulate_sprint_change(
    sprint_id: str = Path(..., description="MongoDB ObjectId of the target sprint"),
    new_ticket: NewTicketInput = ...,
) -> SimulationResponse:

    # ── 1. Fetch sprint and existing items from DB ────────────────────────────
    sprint = await get_sprint_by_id(sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail=f"Sprint '{sprint_id}' not found.")

    if sprint.get("status") not in ("Planned", "Active"):
        raise HTTPException(
            status_code=400,
            detail="Simulation is only available for Planned or Active sprints.",
        )

    existing_items = await get_backlog_items_by_sprint(sprint_id)

    # ── 2. Build shared context objects ──────────────────────────────────────
    current_state   = _build_current_state(sprint, existing_items)
    sprint_context  = _build_sprint_context(sprint, existing_items)
    item_data       = new_ticket.model_dump()

    # ── 3. Run ML impact prediction ──────────────────────────────────────────
    try:
        ml_result = impact_predictor.predict_all_impacts(
            item_data, sprint_context, existing_items
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ML prediction failed: {exc}",
        ) from exc

    display: dict = ml_result.get("display", {})

    # ── 4. Run Recommendation Engine ─────────────────────────────────────────
    raw_ml = {
        "schedule_risk":   ml_result.get("schedule_risk", {}).get("probability", 0),
        "quality_risk":    ml_result.get("quality_risk",  {}).get("probability", 0),
        "velocity_change": ml_result.get("productivity",  {}).get("velocity_change", 0),
        "days_remaining":  sprint_context["days_remaining"],
        "free_capacity":   max(0, sprint_context["team_velocity_14d"] - sprint_context["sprint_load_7d"]),
    }

    recommendation = recommendation_engine.generate_recommendation(
        new_ticket   = item_data,
        sprint_context = sprint_context,
        active_items = existing_items,
        ml_predictions = raw_ml,
    )

    # ── 5. Generate human-readable explanation ────────────────────────────────
    explanation_input = {
        "recommendation_type": recommendation.get("recommendation_type", "DEFER"),
        "reasoning":           recommendation.get("reasoning", ""),
        "target_ticket":       recommendation.get("target_ticket"),
        "impact_analysis":     raw_ml,
        "action_plan":         recommendation.get("action_plan", {}),
        "work_item_data":      item_data,
    }
    explanation: ExplanationResult = explanation_generator.generate_explanation(explanation_input)

    # ── 6. Compute simulated totals ───────────────────────────────────────────
    new_total_sp       = current_state.total_story_points + new_ticket.story_points
    new_hours_required = ml_result.get("effort", {}).get("hours_median", 0.0)

    # ── 7. Assemble and return response ──────────────────────────────────────
    simulated_state = SimulatedState(
        new_total_story_points  = new_total_sp,
        new_hours_required      = float(new_hours_required),
        risk_metrics            = _build_risk_metrics_from_display(display),
        recommendation_action   = recommendation.get("recommendation_type", "DEFER"),
        short_explanation       = explanation["short_title"],
        detailed_explanation    = explanation["detailed_explanation"],
        confidence_color        = explanation["confidence_color"],
        action_verb             = explanation["action_verb"],
        action_plan             = recommendation.get("action_plan", {}),
        target_ticket           = recommendation.get("target_ticket"),
    )

    return SimulationResponse(
        sprint_id         = sprint_id,
        ticket_evaluated  = new_ticket,
        current_state     = current_state,
        simulated_state   = simulated_state,
    )