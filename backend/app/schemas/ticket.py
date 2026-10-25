from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from pydantic.alias_generators import to_camel

from app.domain.status import EventType, Priority, TicketStatus

Trimmed = Annotated[str, StringConstraints(strip_whitespace=True)]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# requests


class CreateTicketRequest(ApiModel):
    title: Annotated[Trimmed, Field(min_length=3, max_length=120)]
    description: Annotated[Trimmed, Field(max_length=1000)] | None = None
    asset_code: Annotated[Trimmed, Field(pattern=r"^[A-Z0-9-]{2,40}$")]
    priority: Priority = Priority.MEDIUM
    reported_by: Annotated[Trimmed, Field(min_length=2, max_length=100)]


class ChangeStatusRequest(ApiModel):
    to_status: TicketStatus
    diagnosis: Annotated[Trimmed, Field(max_length=1000)] | None = None
    comment: Annotated[Trimmed, Field(max_length=1000)] | None = None
    actor: Annotated[Trimmed, Field(min_length=1, max_length=100)]
    version: int = Field(ge=1, le=2_147_483_647)

    @field_validator("diagnosis", "comment")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        return value or None


class AddCommentRequest(ApiModel):
    comment: Annotated[Trimmed, Field(min_length=1, max_length=1000)]
    actor: Annotated[Trimmed, Field(min_length=1, max_length=100)]


class AssignRequest(ApiModel):
    operator_id: int | None
    actor: Annotated[Trimmed, Field(min_length=1, max_length=100)]
    version: int = Field(ge=1, le=2_147_483_647)


# responses


class OperatorOut(ApiModel):
    id: int
    name: str
    email: str


class OperatorRef(ApiModel):
    id: int
    name: str


class TransitionOut(ApiModel):
    from_status: TicketStatus
    to_status: TicketStatus
    requires_diagnosis: bool
    requires_comment: bool


class AllowedTransition(ApiModel):
    to_status: TicketStatus
    requires_diagnosis: bool
    requires_comment: bool


class TicketOut(ApiModel):
    id: int
    code: str
    title: str
    description: str | None
    asset_code: str
    priority: Priority
    status: TicketStatus
    diagnosis: str | None
    assigned_operator: OperatorRef | None
    reported_by: str
    created_at: datetime
    updated_at: datetime
    version: int
    allowed_transitions: list[AllowedTransition]


class HistoryEventOut(ApiModel):
    id: int
    ticket_id: int
    event_type: EventType
    from_status: TicketStatus | None
    to_status: TicketStatus | None
    comment: str | None
    actor: str
    created_at: datetime


class NotificationOut(ApiModel):
    id: int
    ticket_id: int
    ticket_title: str
    from_status: TicketStatus | None
    to_status: TicketStatus | None
    actor: str
    created_at: datetime
