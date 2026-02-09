from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .schema import UserSettingsNotificationLevel, UserTeamsRole


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    email: str
    real_name: str | None = None
    display_name: str | None = None
    timezone: str | None = None
    title: str | None = None
    created_at: datetime | None = None
    last_login: datetime | None = None
    is_active: bool | None = None
    is_bot: bool | None = None


class TeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: str
    team_name: str
    created_at: datetime | None = None


class ChannelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: str
    channel_name: str
    team_id: str | None = None
    topic_text: str | None = None
    purpose_text: str | None = None
    is_private: bool
    is_dm: bool
    is_gc: bool
    created_at: datetime | None = None
    is_archived: bool


class MessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    parent_id: str | None = None
    channel_id: str
    user_id: str
    message_text: str | None = None
    type: str | None = None
    ts: str | None = None
    blocks: list[Any] | None = None
    created_at: datetime | None = None


class ChannelMemberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: str
    user_id: str
    joined_at: datetime | None = None


class UserRoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    role_id: str
    assigned_at: datetime | None = None


class MessageReactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    user_id: str
    reaction_type: str
    created_at: datetime | None = None


class TeamRoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: str
    team_id: str
    role_name: str | None = None


class TeamSettingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: str
    default_channel_id: str | None = None
    allow_file_uploads: bool | None = None


class FileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: str
    user_id: str
    file_name: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    file_url: str | None = None
    created_at: datetime | None = None


class UserSettingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    notification_level: UserSettingsNotificationLevel | None = None


class FileMessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_message_id: str
    file_id: str
    message_id: str


class UserTeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    team_id: str
    role: UserTeamsRole | None = None


class UserMentionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    message_id: str
    mention_id: str
    mentioned_at: datetime | None = None


class MessageEditSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    edit_id: str
    message_id: str
    edited_text: str | None = None
    edited_at: datetime | None = None
