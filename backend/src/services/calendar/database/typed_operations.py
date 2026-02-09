"""
Typed operations wrapper for Google Calendar API.

This module provides a class-based API for Calendar operations, encapsulating
session management for easier use by AI agents.
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from . import operations as ops
from .pydantic_schemas import (
    CalendarListEntrySchema,
    CalendarSchema,
    EventSchema,
    UserSchema,
)
from .schema import AccessRole


class CalendarOperations:
    """
    Typed operations for Google Calendar API.

    This class wraps the raw operations functions and manages the database session,
    providing a cleaner API for AI agents to use.

    Example usage:
        ops = CalendarOperations(session)

        # Create a user
        user = ops.create_user(
            email="user@example.com",
            display_name="Test User"
        )

        # Create a calendar
        calendar = ops.create_calendar(
            owner_id=user.id,
            summary="Work Calendar"
        )

        # Create an event
        event = ops.create_event(
            calendar_id=calendar.id,
            summary="Team Meeting",
            start={"dateTime": "2024-01-15T10:00:00Z"},
            end={"dateTime": "2024-01-15T11:00:00Z"}
        )
    """

    def __init__(self, session: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def create_user(
        self,
        email: str,
        *,
        user_id: Optional[str] = None,
        display_name: Optional[str] = None,
        create_primary_calendar: bool = True,
    ) -> UserSchema:
        """
        Create a new user with optional primary calendar.

        Args:
            email: User email address
            user_id: Optional user ID (defaults to email)
            display_name: Optional display name
            create_primary_calendar: Whether to create primary calendar (default: True)

        Returns:
            User model

        Raises:
            DuplicateError: If user already exists
        """
        result = ops.create_user(
            self.session,
            email=email,
            user_id=user_id,
            display_name=display_name,
            create_primary_calendar=create_primary_calendar,
        )
        return UserSchema.model_validate(result)

    def get_user(self, user_id: str) -> Optional[UserSchema]:
        """
        Get a user by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            User model or None if not found
        """
        result = ops.get_user(self.session, user_id)
        return UserSchema.model_validate(result) if result else None

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        """
        Get a user by email address.

        Args:
            email: Email address to search for

        Returns:
            User model or None if not found
        """
        result = ops.get_user_by_email(self.session, email)
        return UserSchema.model_validate(result) if result else None

    # ========================================================================
    # CALENDAR OPERATIONS
    # ========================================================================

    def create_calendar(
        self,
        owner_id: str,
        summary: str,
        *,
        description: Optional[str] = None,
        location: Optional[str] = None,
        time_zone: Optional[str] = None,
        calendar_id: Optional[str] = None,
    ) -> CalendarSchema:
        """
        Create a new secondary calendar.

        Args:
            owner_id: User ID of the calendar owner
            summary: Calendar title/name
            description: Optional calendar description
            location: Optional location
            time_zone: Optional timezone (defaults to UTC)
            calendar_id: Optional calendar ID (auto-generated if not provided)

        Returns:
            Calendar model

        Raises:
            ValidationError: If owner not found
        """
        result = ops.create_calendar(
            self.session,
            owner_id=owner_id,
            summary=summary,
            description=description,
            location=location,
            time_zone=time_zone,
            calendar_id=calendar_id,
        )
        return CalendarSchema.model_validate(result)

    def get_calendar(self, calendar_id: str) -> Optional[CalendarSchema]:
        """
        Get a calendar by ID.

        Args:
            calendar_id: Calendar ID to retrieve

        Returns:
            Calendar model or None if not found
        """
        result = ops.get_calendar(self.session, calendar_id)
        return CalendarSchema.model_validate(result) if result else None

    def update_calendar(
        self,
        calendar_id: str,
        *,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        time_zone: Optional[str] = None,
    ) -> CalendarSchema:
        """
        Update a calendar.

        Args:
            calendar_id: Calendar ID to update
            summary: New calendar title/name
            description: New description
            location: New location
            time_zone: New timezone

        Returns:
            Updated Calendar model

        Raises:
            CalendarNotFoundError: If calendar not found
        """
        result = ops.update_calendar(
            self.session,
            calendar_id=calendar_id,
            summary=summary,
            description=description,
            location=location,
            time_zone=time_zone,
        )
        return CalendarSchema.model_validate(result)

    def delete_calendar(self, calendar_id: str) -> None:
        """
        Delete a calendar.

        Args:
            calendar_id: Calendar ID to delete

        Raises:
            CalendarNotFoundError: If calendar not found
            ValidationError: If trying to delete primary calendar
        """
        ops.delete_calendar(self.session, calendar_id)

    def clear_calendar(self, calendar_id: str) -> int:
        """
        Delete all events from a calendar.

        Args:
            calendar_id: Calendar ID to clear

        Returns:
            Number of events deleted

        Raises:
            CalendarNotFoundError: If calendar not found
        """
        return ops.clear_calendar(self.session, calendar_id)

    # ========================================================================
    # CALENDAR LIST OPERATIONS
    # ========================================================================

    def insert_calendar_list_entry(
        self,
        user_id: str,
        calendar_id: str,
        *,
        access_role: AccessRole = AccessRole.reader,
        summary_override: Optional[str] = None,
        color_id: Optional[str] = None,
        hidden: bool = False,
        selected: bool = True,
    ) -> CalendarListEntrySchema:
        """
        Subscribe a user to a calendar (insert calendar list entry).

        Args:
            user_id: User ID subscribing to the calendar
            calendar_id: Calendar ID to subscribe to
            access_role: Access role (default: reader)
            summary_override: Optional custom title
            color_id: Optional color ID
            hidden: Whether to hide in UI (default: False)
            selected: Whether selected for display (default: True)

        Returns:
            CalendarListEntry model

        Raises:
            ValidationError: If user or calendar not found
            DuplicateError: If already subscribed
        """
        result = ops.insert_calendar_list_entry(
            self.session,
            user_id=user_id,
            calendar_id=calendar_id,
            access_role=access_role,
            summary_override=summary_override,
            color_id=color_id,
            hidden=hidden,
            selected=selected,
        )
        return CalendarListEntrySchema.model_validate(result)

    def get_calendar_list_entry(
        self,
        user_id: str,
        calendar_id: str,
    ) -> Optional[CalendarListEntrySchema]:
        """
        Get a specific calendar list entry.

        Args:
            user_id: User ID
            calendar_id: Calendar ID

        Returns:
            CalendarListEntry model or None if not found
        """
        result = ops.get_calendar_list_entry(
            self.session,
            user_id=user_id,
            calendar_id=calendar_id,
        )
        return CalendarListEntrySchema.model_validate(result) if result else None

    def list_calendar_list_entries(
        self,
        user_id: str,
        *,
        show_deleted: bool = False,
        show_hidden: bool = False,
        min_access_role: Optional[AccessRole] = None,
    ) -> list[CalendarListEntrySchema]:
        """
        List calendar list entries for a user.

        Args:
            user_id: User ID
            show_deleted: Include deleted entries (default: False)
            show_hidden: Include hidden entries (default: False)
            min_access_role: Filter by minimum access role

        Returns:
            List of CalendarListEntry models
        """
        results = ops.list_calendar_list_entries(
            self.session,
            user_id=user_id,
            show_deleted=show_deleted,
            show_hidden=show_hidden,
            min_access_role=min_access_role,
        )
        return [CalendarListEntrySchema.model_validate(r) for r in results]

    # ========================================================================
    # EVENT OPERATIONS
    # ========================================================================

    def create_event(
        self,
        calendar_id: str,
        user_id: str,
        *,
        start: dict[str, Any],
        end: dict[str, Any],
        summary: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[dict[str, Any]]] = None,
        recurrence: Optional[list[str]] = None,
        event_id: Optional[str] = None,
        **kwargs: Any,
    ) -> EventSchema:
        """
        Create a new event.

        Args:
            calendar_id: Calendar ID to create event in
            user_id: User ID creating the event (for permissions and creator/organizer)
            start: Start time (dict with 'dateTime' or 'date')
            end: End time (dict with 'dateTime' or 'date')
            summary: Event title
            description: Event description
            location: Event location
            attendees: Optional list of attendee dicts
            recurrence: Optional recurrence rules (RRULE format)
            event_id: Optional event ID (auto-generated if not provided)
            **kwargs: Additional event fields

        Returns:
            Event model

        Raises:
            CalendarNotFoundError: If calendar not found
            ValidationError: If required fields missing or invalid
        """
        result = ops.create_event(
            self.session,
            calendar_id=calendar_id,
            user_id=user_id,
            start=start,
            end=end,
            summary=summary,
            description=description,
            location=location,
            attendees=attendees,
            recurrence=recurrence,
            event_id=event_id,
            **kwargs,
        )
        return EventSchema.model_validate(result)

    def get_event(
        self,
        calendar_id: str,
        event_id: str,
        user_id: str,
    ) -> Optional[EventSchema]:
        """
        Get an event by ID.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID to retrieve
            user_id: User ID (for permissions check)

        Returns:
            Event model or None if not found
        """
        result = ops.get_event(
            self.session,
            calendar_id=calendar_id,
            event_id=event_id,
            user_id=user_id,
        )
        return EventSchema.model_validate(result) if result else None

    def list_events(
        self,
        calendar_id: str,
        user_id: str,
        *,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        show_deleted: bool = False,
        single_events: bool = False,
        max_results: int = 250,
    ) -> list[EventSchema]:
        """
        List events in a calendar.

        Args:
            calendar_id: Calendar ID
            user_id: User ID (for permissions check)
            time_min: Lower bound for event start time (RFC3339 format)
            time_max: Upper bound for event start time (RFC3339 format)
            show_deleted: Include deleted events (default: False)
            single_events: Expand recurring events (default: False)
            max_results: Maximum results to return (default: 250)

        Returns:
            List of Event models (note: returns first element of tuple from ops.list_events)

        Raises:
            CalendarNotFoundError: If calendar not found
        """
        events, _, _ = ops.list_events(
            self.session,
            calendar_id=calendar_id,
            user_id=user_id,
            time_min=time_min,
            time_max=time_max,
            show_deleted=show_deleted,
            single_events=single_events,
            max_results=max_results,
        )
        return [EventSchema.model_validate(e) for e in events]

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        user_id: str,
        *,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        start: Optional[dict[str, Any]] = None,
        end: Optional[dict[str, Any]] = None,
        attendees: Optional[list[dict[str, Any]]] = None,
        recurrence: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> EventSchema:
        """
        Update an event (full update).

        Args:
            calendar_id: Calendar ID
            event_id: Event ID to update
            user_id: User ID (for permissions check)
            summary: New event title
            description: New description
            location: New location
            start: New start time
            end: New end time
            attendees: New attendees list
            recurrence: New recurrence rules
            **kwargs: Additional fields to update

        Returns:
            Updated Event model

        Raises:
            EventNotFoundError: If event not found
            ValidationError: If invalid field values
        """
        update_data = {}
        if summary is not None:
            update_data["summary"] = summary
        if description is not None:
            update_data["description"] = description
        if location is not None:
            update_data["location"] = location
        if start is not None:
            update_data["start"] = start
        if end is not None:
            update_data["end"] = end
        if attendees is not None:
            update_data["attendees"] = attendees
        if recurrence is not None:
            update_data["recurrence"] = recurrence
        update_data.update(kwargs)

        result = ops.update_event(
            self.session,
            calendar_id=calendar_id,
            event_id=event_id,
            user_id=user_id,
            **update_data,
        )
        return EventSchema.model_validate(result)

    def delete_event(
        self,
        calendar_id: str,
        event_id: str,
        user_id: str,
    ) -> None:
        """
        Delete an event.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID to delete
            user_id: User ID (for permissions check)

        Raises:
            EventNotFoundError: If event not found
        """
        ops.delete_event(
            self.session,
            calendar_id=calendar_id,
            event_id=event_id,
            user_id=user_id,
        )

    def quick_add_event(
        self,
        calendar_id: str,
        text: str,
    ) -> EventSchema:
        """
        Create an event from a natural language text string.

        Args:
            calendar_id: Calendar ID
            text: Natural language event description

        Returns:
            Created Event model

        Raises:
            CalendarNotFoundError: If calendar not found
            ValidationError: If text cannot be parsed
        """
        result = ops.quick_add_event(
            self.session,
            calendar_id=calendar_id,
            text=text,
        )
        return EventSchema.model_validate(result)
