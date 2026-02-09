from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .schema import (
    AccessRole,
    AclScopeType,
    AttendeeResponseStatus,
    EventStatus,
    EventTransparency,
    EventType,
    EventVisibility,
    ReminderMethod,
)


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str | None = None
    self_: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CalendarSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    summary: str
    description: str | None = None
    location: str | None = None
    time_zone: str | None = None
    etag: str
    conference_properties: dict[str, Any] | None = None
    auto_accept_invitations: bool = False
    owner_id: str
    data_owner: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted: bool = False


class CalendarListEntrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    calendar_id: str
    etag: str
    access_role: AccessRole
    summary_override: str | None = None
    description_override: str | None = None
    color_id: str | None = None
    background_color: str | None = None
    foreground_color: str | None = None
    hidden: bool = False
    selected: bool = True
    primary: bool = False
    deleted: bool = False
    default_reminders: list[dict[str, Any]] | None = None
    notification_settings: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    calendar_id: str
    etag: str
    status: EventStatus = EventStatus.confirmed
    html_link: str | None = None
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    color_id: str | None = None
    creator_id: str | None = None
    organizer_id: str | None = None
    creator_email: str | None = None
    organizer_email: str | None = None
    creator_display_name: str | None = None
    organizer_display_name: str | None = None
    creator_profile_id: str | None = None
    organizer_profile_id: str | None = None
    creator_self: bool = False
    organizer_self: bool = False
    start: dict[str, Any]
    end: dict[str, Any]
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    start_date: str | None = None
    end_date: str | None = None
    end_time_unspecified: bool = False
    recurrence: list[str] | None = None
    recurring_event_id: str | None = None
    original_start_time: dict[str, Any] | None = None
    transparency: EventTransparency = EventTransparency.opaque
    visibility: EventVisibility = EventVisibility.default
    ical_uid: str | None = None
    sequence: int = 0
    guests_can_invite_others: bool = True
    guests_can_modify: bool = False
    guests_can_see_other_guests: bool = True
    anyone_can_add_self: bool = False
    private_copy: bool = False
    locked: bool = False
    attendees_omitted: bool = False
    hangout_link: str | None = None
    conference_data: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] | None = None
    extended_properties: dict[str, Any] | None = None
    source: dict[str, Any] | None = None
    gadget: dict[str, Any] | None = None
    reminders: dict[str, Any] | None = None
    event_type: EventType = EventType.default
    working_location_properties: dict[str, Any] | None = None
    out_of_office_properties: dict[str, Any] | None = None
    focus_time_properties: dict[str, Any] | None = None
    birthday_properties: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EventAttendeeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    email: str
    display_name: str | None = None
    organizer: bool = False
    self_: bool = False
    resource: bool = False
    optional: bool = False
    response_status: AttendeeResponseStatus = AttendeeResponseStatus.needsAction
    comment: str | None = None
    additional_guests: int = 0
    profile_id: str | None = None


class EventReminderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    method: ReminderMethod
    minutes: int


class AclRuleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    calendar_id: str
    etag: str
    role: AccessRole
    scope_type: AclScopeType
    scope_value: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted: bool = False


class SettingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    setting_id: str
    value: str
    etag: str


class ChannelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_id: str
    resource_uri: str
    type: str
    address: str
    expiration: int | None = None
    token: str | None = None
    params: dict[str, Any] | None = None
    payload: bool = False
    user_id: str | None = None
    created_at: datetime | None = None


class SyncTokenSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    user_id: str
    resource_type: str
    resource_id: str | None = None
    snapshot_time: datetime
    expires_at: datetime
    created_at: datetime | None = None
