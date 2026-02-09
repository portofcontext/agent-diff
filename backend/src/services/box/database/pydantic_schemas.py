from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..utils.enums import BoxItemStatus, BoxTaskAction, BoxTaskCompletionRule


class CollectionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "collection"
    name: str
    collection_type: str


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "user"
    name: str | None = None
    login: str | None = None
    status: str = "active"
    job_title: str | None = None
    phone: str | None = None
    address: str | None = None
    avatar_url: str | None = None
    language: str | None = None
    timezone: str | None = None
    space_amount: int | None = None
    space_used: int | None = None
    max_upload_size: int | None = None
    notification_email: dict[str, Any] | None = None
    role: str | None = None
    enterprise: dict[str, Any] | None = None
    tracking_codes: list[Any] | None = None
    can_see_managed_users: bool | None = None
    is_sync_enabled: bool | None = None
    is_external_collab_restricted: bool | None = None
    is_exempt_from_device_limits: bool | None = None
    is_exempt_from_login_verification: bool | None = None
    is_platform_access_only: bool | None = None
    my_tags: list[Any] | None = None
    hostname: str | None = None
    external_app_user_id: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None


class FolderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "folder"
    name: str | None = None
    description: str | None = None
    size: int = 0
    item_status: str = BoxItemStatus.ACTIVE.value
    parent_id: str | None = None
    created_by_id: str | None = None
    modified_by_id: str | None = None
    owned_by_id: str | None = None
    etag: str | None = None
    sequence_id: str | None = None
    tags: list[Any] | None = None
    collections: list[Any] | None = None
    shared_link: dict[str, Any] | None = None
    folder_upload_email: dict[str, Any] | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    trashed_at: datetime | None = None
    purged_at: datetime | None = None
    content_created_at: datetime | None = None
    content_modified_at: datetime | None = None
    sync_state: str | None = None
    has_collaborations: bool | None = None
    can_non_owners_invite: bool | None = None
    is_externally_owned: bool | None = None
    is_collaboration_restricted_to_enterprise: bool | None = None
    can_non_owners_view_collaborators: bool | None = None
    is_accessible_via_shared_link: bool | None = None
    is_associated_with_app_item: bool | None = None
    permissions: dict[str, Any] | None = None
    allowed_shared_link_access_levels: list[Any] | None = None
    allowed_invitee_roles: list[Any] | None = None
    watermark_info: dict[str, Any] | None = None
    classification: dict[str, Any] | None = None
    box_metadata: dict[str, Any] | None = None


class FileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "file"
    name: str | None = None
    description: str | None = None
    size: int = 0
    item_status: str = BoxItemStatus.ACTIVE.value
    parent_id: str | None = None
    created_by_id: str | None = None
    modified_by_id: str | None = None
    owned_by_id: str | None = None
    etag: str | None = None
    sequence_id: str | None = None
    sha_1: str | None = None
    file_version_id: str | None = None
    version_number: str | None = None
    comment_count: int = 0
    extension: str | None = None
    lock: dict[str, Any] | None = None
    tags: list[Any] | None = None
    collections: list[Any] | None = None
    shared_link: dict[str, Any] | None = None
    permissions: dict[str, Any] | None = None
    is_package: bool | None = None
    is_accessible_via_shared_link: bool | None = None
    is_externally_owned: bool | None = None
    has_collaborations: bool | None = None
    is_associated_with_app_item: bool | None = None
    allowed_invitee_roles: list[Any] | None = None
    shared_link_permission_options: list[Any] | None = None
    expiring_embed_link: dict[str, Any] | None = None
    watermark_info: dict[str, Any] | None = None
    box_metadata: dict[str, Any] | None = None
    representations: dict[str, Any] | None = None
    classification: dict[str, Any] | None = None
    uploader_display_name: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    trashed_at: datetime | None = None
    purged_at: datetime | None = None
    content_created_at: datetime | None = None
    content_modified_at: datetime | None = None
    expires_at: datetime | None = None
    disposition_at: datetime | None = None


class FileVersionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "file_version"
    file_id: str
    version_number: int = 1
    sha_1: str | None = None
    size: int = 0
    name: str | None = None
    uploader_display_name: str | None = None
    modified_by_id: str | None = None
    trashed_by_id: str | None = None
    trashed_at: datetime | None = None
    restored_by_id: str | None = None
    restored_at: datetime | None = None
    purged_at: datetime | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None


class FileContentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_id: str
    content_type: str | None = None


class CommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "comment"
    message: str | None = None
    tagged_message: str | None = None
    file_id: str
    item_id: str
    item_type: str = "file"
    is_reply_comment: bool = False
    created_by_id: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None


class TaskSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "task"
    message: str | None = None
    action: str = BoxTaskAction.REVIEW.value
    is_completed: bool = False
    completion_rule: str = BoxTaskCompletionRule.ALL_ASSIGNEES.value
    item_id: str
    item_type: str = "file"
    due_at: datetime | None = None
    created_by_id: str | None = None
    created_at: datetime | None = None


class TaskAssignmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "task_assignment"
    task_id: str
    item_id: str | None = None
    item_type: str | None = None
    assigned_to_id: str
    assigned_by_id: str | None = None
    message: str | None = None
    resolution_state: str = "incomplete"
    assigned_at: datetime | None = None
    reminded_at: datetime | None = None
    completed_at: datetime | None = None


class HubSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "hubs"
    title: str | None = None
    description: str | None = None
    is_ai_enabled: bool = True
    is_collaboration_restricted_to_enterprise: bool = False
    can_non_owners_invite: bool = True
    can_shared_link_be_created: bool = True
    view_count: int = 0
    created_by_id: str | None = None
    updated_by_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HubItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "hub_item"
    hub_id: str
    item_id: str
    item_type: str
    item_name: str | None = None
    position: int = 0
    added_by_id: str | None = None
    added_at: datetime | None = None
