"""
Default values for Linear entities.

This module provides sensible defaults for auto-generated Linear schema entities,
avoiding repetition when creating instances with many required fields.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


def organization_defaults(
    name: str, url_key: Optional[str] = None, **overrides: Any
) -> dict[str, Any]:
    """
    Generate default values for Organization creation.

    Args:
        name: Organization name (required)
        url_key: Optional URL key (defaults to lowercase name)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Organization
    """
    if url_key is None:
        url_key = name.lower().replace(" ", "-").replace("_", "-")

    defaults = {
        "id": str(uuid4()),
        "name": name,
        "urlKey": url_key,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        # Boolean fields
        "aiAddonEnabled": False,
        "customersEnabled": False,
        "feedEnabled": False,
        "gitLinkbackMessagesEnabled": False,
        "gitPublicLinkbackMessagesEnabled": False,
        "hipaaComplianceEnabled": False,
        "roadmapEnabled": False,
        "samlEnabled": False,
        "scimEnabled": False,
        # Numeric fields
        "createdIssueCount": 0,
        "customerCount": 0,
        "fiscalYearStartMonth": 1.0,
        "initiativeUpdateRemindersHour": 9.0,
        "projectUpdateRemindersHour": 9.0,
        "periodUploadVolume": 0.0,
        "userCount": 0,
        # String fields
        "initiativeUpdateRemindersDay": "monday",
        "projectUpdateRemindersDay": "monday",
        "releaseChannel": "stable",
        "projectUpdatesReminderFrequency": "weekly",
        "slaDayCount": "7",
        # List/Dict fields
        "allowedAuthServices": [],
        "allowedFileUploadContentTypes": ["image/png", "image/jpeg", "application/pdf"],
        "previousUrlKeys": [],
        "customersConfiguration": {},
        "workingDays": [1.0, 2.0, 3.0, 4.0, 5.0],  # Monday-Friday
    }

    # Apply overrides
    defaults.update(overrides)
    return defaults


def user_defaults(email: str, name: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for User creation.

    Args:
        email: User email (required)
        name: User name (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for User
    """
    user_id = str(uuid4())

    # Generate initials from name
    name_parts = name.split()
    if len(name_parts) >= 2:
        initials = f"{name_parts[0][0]}{name_parts[1][0]}".upper()
    else:
        initials = name[:2].upper()

    defaults = {
        "id": user_id,
        "email": email,
        "name": name,
        "displayName": overrides.get("displayName", name),
        "active": True,
        "admin": False,
        "app": False,
        "guest": False,
        "avatarBackgroundColor": "#6B7280",  # Gray-500
        "canAccessAnyPublicTeam": True,
        "createdIssueCount": 0,
        "initials": initials,
        "inviteHash": str(uuid4()),  # Generate unique invite hash
        "isAssignable": True,
        "isMe": False,
        "isMentionable": True,
        "url": f"https://linear.app/user/{user_id}",
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
    }

    defaults.update(overrides)
    return defaults


def team_defaults(
    name: str, key: str, organization_id: str, **overrides: Any
) -> dict[str, Any]:
    """
    Generate default values for Team creation.

    Args:
        name: Team name (required)
        key: Team key (required, e.g., "ENG")
        organization_id: Organization ID (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Team
    """
    team_id = str(uuid4())

    defaults = {
        "id": team_id,
        "name": name,
        "key": key,
        "organizationId": organization_id,
        "displayName": name,  # Use name as display name by default
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        # Boolean fields
        "aiThreadSummariesEnabled": False,
        "private": False,
        "cycleIssueAutoAssignCompleted": False,
        "cycleIssueAutoAssignStarted": False,
        "cycleLockToActive": False,
        "cyclesEnabled": False,
        "groupIssueHistory": False,
        "inheritIssueEstimation": False,
        "inheritWorkflowStatuses": False,
        "issueEstimationAllowZero": True,
        "issueEstimationExtended": False,
        "issueOrderingNoPriorityFirst": False,
        "issueSortOrderDefaultToBottom": False,
        "requirePriorityToLeaveTriage": False,
        "scimManaged": False,
        "slackIssueComments": False,
        "slackIssueStatuses": False,
        "slackNewIssue": False,
        "triageEnabled": False,
        # Float fields
        "autoArchivePeriod": 0.0,
        "cycleCooldownTime": 0.0,
        "cycleDuration": 7.0,  # 1 week default
        "cycleStartDay": 0.0,  # Monday
        "defaultIssueEstimate": 1.0,
        "upcomingCycleCount": 0.0,
        # Integer fields
        "issueCount": 0,
        # String fields
        "issueEstimationType": "notUsed",
        "setIssueSortOrderOnStateChange": "off",
        "timezone": "America/Los_Angeles",
        "inviteHash": str(uuid4()),
        "cycleCalenderUrl": f"https://linear.app/team/{team_id}/cycles.ics",
        # Dict/JSON fields
        "currentProgress": {},
        "progressHistory": {},
    }

    defaults.update(overrides)
    return defaults


def issue_defaults(team_id: str, title: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for Issue creation.

    Args:
        team_id: Team ID (required)
        title: Issue title (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Issue
    """
    defaults = {
        "id": str(uuid4()),
        "teamId": team_id,
        "title": title,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "priority": 0,
        "estimate": 0.0,
        "sortOrder": 0.0,
        "subIssueSortOrder": 0.0,
        "trashed": False,
    }

    defaults.update(overrides)
    return defaults


def project_defaults(name: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for Project creation.

    Args:
        name: Project name (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Project
    """
    defaults = {
        "id": str(uuid4()),
        "name": name,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "sortOrder": 0.0,
        "startedAt": datetime.now(),
        "autoArchivedAt": None,
        "canceledAt": None,
        "completedAt": None,
        "trashed": False,
    }

    defaults.update(overrides)
    return defaults


def comment_defaults(issue_id: str, body: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for Comment creation.

    Args:
        issue_id: Issue ID (required)
        body: Comment body (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Comment
    """
    defaults = {
        "id": str(uuid4()),
        "issueId": issue_id,
        "body": body,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "edited": False,
    }

    defaults.update(overrides)
    return defaults


def workflow_state_defaults(
    name: str, team_id: str, type: str = "unstarted", **overrides: Any
) -> dict[str, Any]:
    """
    Generate default values for WorkflowState creation.

    Args:
        name: State name (required, e.g., "Todo", "In Progress")
        team_id: Team ID (required)
        type: State type (default: "unstarted", options: "unstarted", "started", "completed", "canceled")
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for WorkflowState
    """
    defaults = {
        "id": str(uuid4()),
        "name": name,
        "teamId": team_id,
        "type": type,
        "color": "#000000",
        "position": overrides.get("position", 0.0),  # Default to position 0
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
    }

    defaults.update(overrides)
    return defaults


def cycle_defaults(
    team_id: str, number: int, starts_at: datetime, ends_at: datetime, **overrides: Any
) -> dict[str, Any]:
    """
    Generate default values for Cycle creation.

    Args:
        team_id: Team ID (required)
        number: Cycle number (required)
        starts_at: Start date (required)
        ends_at: End date (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Cycle
    """
    defaults = {
        "id": str(uuid4()),
        "teamId": team_id,
        "number": number,
        "startsAt": starts_at,
        "endsAt": ends_at,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
    }

    defaults.update(overrides)
    return defaults


def initiative_defaults(name: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for Initiative creation.

    Args:
        name: Initiative name (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Initiative
    """
    defaults = {
        "id": str(uuid4()),
        "name": name,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "sortOrder": 0.0,
        "trashed": False,
    }

    defaults.update(overrides)
    return defaults


def document_defaults(title: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for Document creation.

    Args:
        title: Document title (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Document
    """
    defaults = {
        "id": str(uuid4()),
        "title": title,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "sortOrder": 0.0,
        "slugId": title.lower().replace(" ", "-")[:32],
    }

    defaults.update(overrides)
    return defaults


def attachment_defaults(title: str, url: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for Attachment creation.

    Args:
        title: Attachment title (required)
        url: Attachment URL (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for Attachment
    """
    defaults = {
        "id": str(uuid4()),
        "title": title,
        "url": url,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "groupBySource": False,
    }

    defaults.update(overrides)
    return defaults


def project_milestone_defaults(
    name: str, project_id: str, **overrides: Any
) -> dict[str, Any]:
    """
    Generate default values for ProjectMilestone creation.

    Args:
        name: Milestone name (required)
        project_id: Project ID (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for ProjectMilestone
    """
    defaults = {
        "id": str(uuid4()),
        "name": name,
        "projectId": project_id,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "sortOrder": 0.0,
    }

    defaults.update(overrides)
    return defaults


def issue_label_defaults(name: str, **overrides: Any) -> dict[str, Any]:
    """
    Generate default values for IssueLabel creation.

    Args:
        name: Label name (required)
        **overrides: Any field overrides

    Returns:
        Dictionary of field values for IssueLabel
    """
    defaults = {
        "id": str(uuid4()),
        "name": name,
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "color": "#6B7280",  # Gray-500
    }

    defaults.update(overrides)
    return defaults
