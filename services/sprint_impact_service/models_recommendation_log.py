"""
models_recommendation_log.py
──────────────────────────────
Pydantic v2 models for the RecommendationLog collection.
Supports logging every ML prediction and capturing the user's
feedback so the system can close the Continuous Learning Loop.

MongoDB collection name: recommendation_logs

Usage example (motor async driver) at the bottom of this file.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, model_validator


# ──────────────────────────────────────────────────────────────────────────────
# Helper: MongoDB ObjectId compatibility for Pydantic v2
# ──────────────────────────────────────────────────────────────────────────────

class PyObjectId(str):
    """Thin wrapper so Pydantic v2 accepts BSON ObjectIds as plain strings."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v!r}")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class SuggestedAction(str, Enum):
    ADD    = "ADD"
    SWAP   = "SWAP"
    DEFER  = "DEFER"
    SPLIT  = "SPLIT"
    ACCEPT = "ACCEPT"


class TakenAction(str, Enum):
    """What the user actually did after seeing the recommendation."""
    FOLLOWED_RECOMMENDATION = "FOLLOWED_RECOMMENDATION"
    IGNORED_RECOMMENDATION  = "IGNORED_RECOMMENDATION"
    ADDED_ANYWAY            = "ADDED_ANYWAY"
    DEFERRED_MANUALLY       = "DEFERRED_MANUALLY"
    SWAPPED_MANUALLY        = "SWAPPED_MANUALLY"
    SPLIT_MANUALLY          = "SPLIT_MANUALLY"
    NO_ACTION               = "NO_ACTION"


# ──────────────────────────────────────────────────────────────────────────────
# Nested model: ML Predictions snapshot
# ──────────────────────────────────────────────────────────────────────────────

class MLPredictions(BaseModel):
    """
    Raw numeric outputs captured from the four ML models at prediction time.
    Storing these enables offline model-drift analysis and retraining pipelines.
    """

    # ── Effort (XGBoost quantile regression) ─────────────────────────────────
    predicted_hours_lower:  float = Field(..., ge=0, description="Lower-bound effort estimate (hours)")
    predicted_hours_median: float = Field(..., ge=0, description="Median effort estimate (hours)")
    predicted_hours_upper:  float = Field(..., ge=0, description="Upper-bound effort estimate (hours)")
    hours_remaining_in_sprint: float = Field(..., ge=0, description="Available sprint hours when prediction was made")

    # ── Schedule risk (XGBClassifier, probability 0–100) ─────────────────────
    schedule_risk_probability: float = Field(
        ..., ge=0, le=100,
        description="Percentage probability that this ticket will spill over the sprint boundary"
    )
    schedule_risk_label: str = Field(
        default="Unknown",
        description="Human-readable dominant class, e.g. 'High Risk', 'Low Risk'"
    )

    # ── Quality risk (TabNet classifier, probability 0–100) ───────────────────
    quality_risk_probability: float = Field(
        ..., ge=0, le=100,
        description="Percentage probability of a defect being introduced"
    )

    # ── Productivity impact (XGBoost regressor, –1 to +1 normalised) ─────────
    productivity_velocity_change: float = Field(
        ..., ge=-100, le=100,
        description="Projected velocity change as a percentage (negative = slowdown)"
    )
    productivity_days_lost: float = Field(
        ..., ge=0,
        description="Estimated team-days lost due to context switching"
    )

    # ── Overall risk score (derived in recommendation engine) ────────────────
    overall_risk_score: int = Field(
        ..., ge=0,
        description="Composite risk score (0 = safe, higher = more risky)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "predicted_hours_lower": 12.0,
                "predicted_hours_median": 18.5,
                "predicted_hours_upper": 26.0,
                "hours_remaining_in_sprint": 48.0,
                "schedule_risk_probability": 62.3,
                "schedule_risk_label": "High Risk",
                "quality_risk_probability": 45.0,
                "productivity_velocity_change": -22.5,
                "productivity_days_lost": 1.8,
                "overall_risk_score": 7,
            }
        }


# ──────────────────────────────────────────────────────────────────────────────
# Main document model: RecommendationLog
# ──────────────────────────────────────────────────────────────────────────────

class RecommendationLogCreate(BaseModel):
    """
    Schema for inserting a new recommendation log document.
    Call this when the Impact Analyzer responds to the user.
    """

    # ── Context identifiers ───────────────────────────────────────────────────
    sprint_id:    PyObjectId = Field(..., description="MongoDB ObjectId of the sprint being analysed")
    work_item_id: PyObjectId = Field(..., description="ObjectId of the NEW ticket being evaluated")
    requested_by: PyObjectId = Field(..., description="ObjectId of the user who triggered the analysis")

    # ── Ticket snapshot (denormalised for audit purposes) ─────────────────────
    work_item_title:       str   = Field(..., max_length=300)
    work_item_story_points: int  = Field(..., ge=1, le=100)
    work_item_priority:    str   = Field(..., description="Low | Medium | High | Critical")

    # ── ML output ─────────────────────────────────────────────────────────────
    ml_predictions: MLPredictions

    # ── Recommendation ────────────────────────────────────────────────────────
    suggested_action:  SuggestedAction = Field(..., description="Action the engine recommended")
    recommendation_reasoning: str      = Field(..., description="Plain-English explanation of the recommendation")
    target_ticket_id:  Optional[PyObjectId] = Field(
        default=None,
        description="ObjectId of the ticket proposed for SWAP (null for other actions)"
    )
    target_ticket_title: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Denormalised title of the swap-target ticket"
    )

    # ── User interaction (filled in later via PATCH) ──────────────────────────
    accepted:    Optional[bool]         = Field(default=None, description="Did the user accept the recommendation?")
    taken_action: Optional[TakenAction] = Field(default=None, description="What action did the user actually take?")
    user_rating: Optional[int]          = Field(
        default=None, ge=1, le=5,
        description="User quality rating of the recommendation (1 = poor, 5 = excellent)"
    )
    user_comment: Optional[str]         = Field(default=None, max_length=1000)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("work_item_priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"Low", "Medium", "High", "Critical", "Highest"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}, got {v!r}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "sprint_id":    "664f1a2b3c4d5e6f7a8b9c0d",
                "work_item_id": "664f1a2b3c4d5e6f7a8b9c0e",
                "requested_by": "664f1a2b3c4d5e6f7a8b9c0f",
                "work_item_title": "Add Stripe payment gateway integration",
                "work_item_story_points": 8,
                "work_item_priority": "High",
                "ml_predictions": {
                    "predicted_hours_lower": 12.0,
                    "predicted_hours_median": 18.5,
                    "predicted_hours_upper": 26.0,
                    "hours_remaining_in_sprint": 48.0,
                    "schedule_risk_probability": 62.3,
                    "schedule_risk_label": "High Risk",
                    "quality_risk_probability": 45.0,
                    "productivity_velocity_change": -22.5,
                    "productivity_days_lost": 1.8,
                    "overall_risk_score": 7,
                },
                "suggested_action": "SWAP",
                "recommendation_reasoning": "Sprint is at capacity. Swapping with lower-priority ticket.",
                "target_ticket_id":    "664f1a2b3c4d5e6f7a8b9c10",
                "target_ticket_title": "Update README documentation",
                "accepted":    None,
                "taken_action": None,
                "user_rating":  None,
                "user_comment": None,
            }
        }


class RecommendationLogUpdate(BaseModel):
    """
    Schema for capturing the user's feedback via a PATCH request.
    Only feedback fields are mutable after creation.
    """
    accepted:     Optional[bool]         = None
    taken_action: Optional[TakenAction]  = None
    user_rating:  Optional[int]          = Field(default=None, ge=1, le=5)
    user_comment: Optional[str]          = Field(default=None, max_length=1000)
    updated_at:   datetime               = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "RecommendationLogUpdate":
        filled = [
            v for k, v in self.__dict__.items()
            if k != "updated_at" and v is not None
        ]
        if not filled:
            raise ValueError("At least one feedback field must be provided.")
        return self


class RecommendationLog(RecommendationLogCreate):
    """
    Full document model returned from MongoDB (includes the generated _id).
    """
    id: PyObjectId = Field(alias="_id")

    class Config:
        populate_by_name = True


# ──────────────────────────────────────────────────────────────────────────────
# MongoDB usage example (motor async driver)
# ──────────────────────────────────────────────────────────────────────────────
"""
EXAMPLE — inserting a new log and later patching user feedback
──────────────────────────────────────────────────────────────

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

COLLECTION = "recommendation_logs"


async def insert_recommendation_log(
    db: AsyncIOMotorDatabase,
    log_data: RecommendationLogCreate,
) -> str:
    \"\"\"Insert a new recommendation log. Returns the new document's string ID.\"\"\"
    doc = log_data.model_dump()
    # Convert PyObjectId strings back to real ObjectId for native Mongo storage
    for field in ("sprint_id", "work_item_id", "requested_by", "target_ticket_id"):
        if doc.get(field):
            doc[field] = ObjectId(doc[field])
    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


async def patch_user_feedback(
    db: AsyncIOMotorDatabase,
    log_id: str,
    feedback: RecommendationLogUpdate,
) -> bool:
    \"\"\"Update only the user-feedback fields on an existing log. Returns True on success.\"\"\"
    update_doc = {k: v for k, v in feedback.model_dump().items() if v is not None}
    result = await db[COLLECTION].update_one(
        {"_id": ObjectId(log_id)},
        {"$set": update_doc},
    )
    return result.matched_count == 1


async def get_logs_for_sprint(
    db: AsyncIOMotorDatabase,
    sprint_id: str,
    limit: int = 50,
) -> list[dict]:
    \"\"\"Fetch all recommendation logs for a sprint (newest first).\"\"\"
    cursor = (
        db[COLLECTION]
        .find({"sprint_id": ObjectId(sprint_id)})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [doc async for doc in cursor]
"""