from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class BacklogType(str, Enum):
    TASK = "Task"
    SUBTASK = "Subtask"
    BUG = "Bug"
    STORY = "Story"

class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class Status(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"

class SprintStatus(str, Enum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    COMPLETED = "Completed"

class DurationType(str, Enum):
    ONE_WEEK = "1 Week"
    TWO_WEEKS = "2 Weeks"
    THREE_WEEKS = "3 Weeks"
    FOUR_WEEKS = "4 Weeks"
    CUSTOM = "Custom"

# Space Models
class SpaceCreate(BaseModel):
    name: str
    description: str
    max_assignees: int = Field(ge=1)

class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_assignees: Optional[int] = Field(default=None, ge=1)

class Space(BaseModel):
    id: str
    name: str
    description: str
    max_assignees: int
    created_at: datetime
    updated_at: datetime

# Sprint Models
class SprintCreate(BaseModel):
    name: str
    goal: str
    duration_type: DurationType
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    space_id: str

class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None

class Sprint(BaseModel):
    id: str
    name: str
    goal: str
    duration_type: DurationType
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    space_id: str
    status: SprintStatus
    assignees: List[int] = []
    created_at: datetime
    updated_at: datetime

# Backlog Item Models
class BacklogItemCreate(BaseModel):
    title: str
    description: str
    type: BacklogType
    priority: Priority
    story_points: int = Field(ge=3, le=15)
    space_id: str
    sprint_id: Optional[str] = None

class BacklogItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[BacklogType] = None
    priority: Optional[Priority] = None
    story_points: Optional[int] = Field(default=None, ge=3, le=15)
    sprint_id: Optional[str] = None
    status: Optional[Status] = None

class BacklogItem(BaseModel):
    id: str
    title: str
    description: str
    type: BacklogType
    priority: Priority
    story_points: int
    status: Status
    space_id: str
    sprint_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Sprint Action Models
class SprintStartRequest(BaseModel):
    sprint_id: str

class SprintFinishRequest(BaseModel):
    sprint_id: str
    move_incomplete_to: Optional[str] = None  # sprint_id or "backlog"

class AddAssigneeRequest(BaseModel):
    assignee_number: int