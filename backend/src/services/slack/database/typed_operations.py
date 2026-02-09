"""
Typed operations wrapper for Slack API.

This module provides a class-based API for Slack operations, encapsulating
session management for easier use by AI agents.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from . import operations as ops
from .pydantic_schemas import (
    ChannelMemberSchema,
    ChannelSchema,
    MessageReactionSchema,
    MessageSchema,
    TeamSchema,
    UserSchema,
)


class SlackOperations:
    """
    Typed operations for Slack API.

    This class wraps the raw operations functions and manages the database session,
    providing a cleaner API for AI agents to use.

    Example usage:
        ops = SlackOperations(session)

        # Create a team
        team = ops.create_team(team_name="Acme Inc")

        # Create a user
        user = ops.create_user(
            username="jdoe",
            email="jdoe@acme.com",
            real_name="John Doe"
        )

        # Create a channel
        channel = ops.create_channel(
            channel_name="general",
            team_id=team.team_id
        )

        # Send a message
        message = ops.send_message(
            channel_id=channel.channel_id,
            user_id=user.user_id,
            text="Hello, world!"
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
    # TEAM OPERATIONS
    # ========================================================================

    def create_team(
        self,
        team_name: str,
        *,
        team_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        default_channel_name: Optional[str] = None,
    ) -> TeamSchema:
        """
        Create a new Slack team/workspace.

        Args:
            team_name: Name of the team
            team_id: Optional team ID (auto-generated if not provided)
            created_at: Optional creation timestamp
            default_channel_name: Optional name for default channel

        Returns:
            Team model
        """
        team = ops.create_team(
            self.session,
            team_name=team_name,
            team_id=team_id,
            created_at=created_at,
            default_channel_name=default_channel_name,
        )
        return TeamSchema.model_validate(team)

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def create_user(
        self,
        username: str,
        email: str,
        *,
        user_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        real_name: Optional[str] = None,
        display_name: Optional[str] = None,
        timezone: Optional[str] = None,
        title: Optional[str] = None,
    ) -> UserSchema:
        """
        Create a new Slack user.

        Args:
            username: Username
            email: Email address
            user_id: Optional user ID (auto-generated if not provided)
            created_at: Optional creation timestamp
            real_name: Optional real name
            display_name: Optional display name
            timezone: Optional timezone
            title: Optional job title

        Returns:
            User model
        """
        user = ops.create_user(
            self.session,
            username=username,
            email=email,
            user_id=user_id,
            created_at=created_at,
            real_name=real_name,
            display_name=display_name,
            timezone=timezone,
            title=title,
        )
        return UserSchema.model_validate(user)

    def get_user(self, user_id: str) -> UserSchema:
        """
        Get a user by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            User model

        Raises:
            ValueError: If user not found
        """
        user = ops.get_user(self.session, user_id)
        return UserSchema.model_validate(user)

    def get_user_by_email(self, email: str) -> UserSchema:
        """
        Get a user by email address.

        Args:
            email: Email address to search for

        Returns:
            User model

        Raises:
            ValueError: If user not found
        """
        user = ops.get_user_by_email(self.session, email)
        return UserSchema.model_validate(user)

    def list_users(self, team_id: str) -> list[UserSchema]:
        """
        List all users in a team.

        Args:
            team_id: Team ID

        Returns:
            List of User models
        """
        users = ops.list_users(self.session, team_id)
        return [UserSchema.model_validate(u) for u in users]

    # ========================================================================
    # CHANNEL OPERATIONS
    # ========================================================================

    def create_channel(
        self,
        channel_name: str,
        team_id: str,
        *,
        channel_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> ChannelSchema:
        """
        Create a new channel.

        Args:
            channel_name: Channel name
            team_id: Team ID
            channel_id: Optional channel ID (auto-generated if not provided)
            created_at: Optional creation timestamp

        Returns:
            Channel model

        Raises:
            ValueError: If team not found or channel name already taken
        """
        channel = ops.create_channel(
            self.session,
            channel_name=channel_name,
            team_id=team_id,
            channel_id=channel_id,
            created_at=created_at,
        )
        return ChannelSchema.model_validate(channel)

    def archive_channel(self, channel_id: str) -> ChannelSchema:
        """
        Archive a channel.

        Args:
            channel_id: Channel ID to archive

        Returns:
            Updated Channel model

        Raises:
            ValueError: If channel not found
        """
        channel = ops.archive_channel(self.session, channel_id)
        return ChannelSchema.model_validate(channel)

    def unarchive_channel(self, channel_id: str) -> ChannelSchema:
        """
        Unarchive a channel.

        Args:
            channel_id: Channel ID to unarchive

        Returns:
            Updated Channel model

        Raises:
            ValueError: If channel not found
        """
        channel = ops.unarchive_channel(self.session, channel_id)
        return ChannelSchema.model_validate(channel)

    def rename_channel(self, channel_id: str, new_name: str) -> ChannelSchema:
        """
        Rename a channel.

        Args:
            channel_id: Channel ID
            new_name: New channel name

        Returns:
            Updated Channel model

        Raises:
            ValueError: If channel not found
        """
        channel = ops.rename_channel(self.session, channel_id, new_name)
        return ChannelSchema.model_validate(channel)

    def set_channel_topic(self, channel_id: str, topic: str) -> ChannelSchema:
        """
        Set a channel's topic.

        Args:
            channel_id: Channel ID
            topic: New topic

        Returns:
            Updated Channel model

        Raises:
            ValueError: If channel not found
        """
        channel = ops.set_channel_topic(self.session, channel_id, topic)
        return ChannelSchema.model_validate(channel)

    def invite_user_to_channel(
        self,
        channel_id: str,
        user_id: str,
        *,
        joined_at: Optional[datetime] = None,
    ) -> ChannelMemberSchema:
        """
        Invite a user to a channel.

        Args:
            channel_id: Channel ID
            user_id: User ID to invite
            joined_at: Optional join timestamp

        Returns:
            ChannelMember model

        Raises:
            ValueError: If channel or user not found
        """
        member = ops.invite_user_to_channel(
            self.session,
            channel_id=channel_id,
            user_id=user_id,
            joined_at=joined_at,
        )
        return ChannelMemberSchema.model_validate(member)

    def kick_user_from_channel(
        self, channel_id: str, user_id: str
    ) -> ChannelMemberSchema:
        """
        Remove a user from a channel.

        Args:
            channel_id: Channel ID
            user_id: User ID to remove
        """
        member = ops.kick_user_from_channel(self.session, channel_id, user_id)
        return ChannelMemberSchema.model_validate(member)

    def join_channel(
        self,
        channel_id: str,
        user_id: str,
        *,
        joined_at: Optional[datetime] = None,
    ) -> ChannelMemberSchema:
        """
        User joins a channel.

        Args:
            channel_id: Channel ID to join
            user_id: User ID
            joined_at: Optional join timestamp

        Returns:
            ChannelMember model
        """
        member = ops.join_channel(
            self.session,
            channel_id=channel_id,
            user_id=user_id,
            joined_at=joined_at,
        )
        return ChannelMemberSchema.model_validate(member)

    def leave_channel(self, channel_id: str, user_id: str) -> None:
        """
        User leaves a channel.

        Args:
            channel_id: Channel ID to leave
            user_id: User ID
        """
        ops.leave_channel(self.session, channel_id, user_id)

    def list_user_channels(
        self,
        user_id: str,
        team_id: str,
        *,
        exclude_archived: bool = False,
    ) -> list[ChannelSchema]:
        """
        List channels a user is a member of.

        Args:
            user_id: User ID
            team_id: Team ID
            exclude_archived: Exclude archived channels (default: False)

        Returns:
            List of Channel models
        """
        channels = ops.list_user_channels(
            self.session,
            user_id=user_id,
            team_id=team_id,
            exclude_archived=exclude_archived,
        )
        return [ChannelSchema.model_validate(c) for c in channels]

    def list_public_channels(self, team_id: str) -> list[ChannelSchema]:
        """
        List all public channels in a team.

        Args:
            team_id: Team ID

        Returns:
            List of Channel models
        """
        channels = ops.list_public_channels(self.session, team_id)
        return [ChannelSchema.model_validate(c) for c in channels]

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    def send_message(
        self,
        channel_id: str,
        user_id: str,
        text: str,
        *,
        parent_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        blocks: Optional[list] = None,
    ) -> MessageSchema:
        """
        Send a message to a channel.

        Args:
            channel_id: Channel ID
            user_id: User ID sending the message
            text: Message text
            parent_id: Optional parent message ID (for threading)
            created_at: Optional creation timestamp
            blocks: Optional Slack blocks

        Returns:
            Message model

        Raises:
            ValueError: If channel or user not found, or user not in channel
        """
        message = ops.send_message(
            self.session,
            channel_id=channel_id,
            user_id=user_id,
            message_text=text,
            parent_id=parent_id,
            created_at=created_at,
            blocks=blocks,
        )
        return MessageSchema.model_validate(message)

    def send_direct_message(
        self,
        sender_id: str,
        recipient_id: str,
        text: str,
        *,
        team_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        blocks: Optional[list] = None,
    ) -> MessageSchema:
        """
        Send a direct message to another user.

        Args:
            sender_id: Sender user ID
            recipient_id: Recipient user ID
            text: Message text
            team_id: Optional team ID
            created_at: Optional creation timestamp
            blocks: Optional Slack blocks

        Returns:
            Message model

        Raises:
            ValueError: If sender or recipient not found
        """
        message = ops.send_direct_message(
            self.session,
            message_text=text,
            sender_id=sender_id,
            recipient_id=recipient_id,
            team_id=team_id,
            created_at=created_at,
            blocks=blocks,
        )
        return MessageSchema.model_validate(message)

    def update_message(
        self,
        message_id: str,
        text: str,
        *,
        blocks: Optional[list] = None,
    ) -> MessageSchema:
        """
        Update a message.

        Args:
            message_id: Message ID to update
            text: New message text
            blocks: Optional Slack blocks

        Returns:
            Updated Message model

        Raises:
            ValueError: If message not found
        """
        message = ops.update_message(
            self.session,
            message_id=message_id,
            text=text,
            blocks=blocks,
        )
        return MessageSchema.model_validate(message)

    def delete_message(self, message_id: str) -> None:
        """
        Delete a message.

        Args:
            message_id: Message ID to delete
        """
        ops.delete_message(self.session, message_id)

    def add_emoji_reaction(
        self,
        message_id: str,
        user_id: str,
        emoji_name: str,
    ) -> MessageReactionSchema:
        """
        Add an emoji reaction to a message.

        Args:
            message_id: Message ID
            user_id: User ID adding the reaction
            emoji_name: Emoji name (e.g., "thumbsup")

        Returns:
            MessageReaction model

        Raises:
            ValueError: If message or user not found
        """
        reaction = ops.add_emoji_reaction(
            self.session,
            message_id=message_id,
            user_id=user_id,
            emoji_name=emoji_name,
        )
        return MessageReactionSchema.model_validate(reaction)

    def remove_emoji_reaction(self, user_id: str, reaction_id: str) -> None:
        """
        Remove an emoji reaction.

        Args:
            user_id: User ID who added the reaction
            reaction_id: Reaction ID to remove
        """
        ops.remove_emoji_reaction(self.session, user_id, reaction_id)

    def get_reactions(self, message_id: str) -> list[MessageReactionSchema]:
        """
        Get all reactions for a message.

        Args:
            message_id: Message ID

        Returns:
            List of MessageReaction models
        """
        reactions = ops.get_reactions(self.session, message_id)
        return [MessageReactionSchema.model_validate(r) for r in reactions]

    def list_channel_history(
        self,
        channel_id: str,
        *,
        limit: int = 100,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
    ) -> list[MessageSchema]:
        """
        List messages in a channel.

        Args:
            channel_id: Channel ID
            limit: Maximum number of messages to return (default: 100)
            oldest: Only messages after this timestamp
            latest: Only messages before this timestamp

        Returns:
            List of Message models
        """
        messages = ops.list_channel_history(
            self.session,
            channel_id=channel_id,
            limit=limit,
            oldest=oldest,
            latest=latest,
        )
        return [MessageSchema.model_validate(m) for m in messages]

    def list_thread_messages(
        self,
        thread_ts: str,
        *,
        limit: int = 100,
    ) -> list[MessageSchema]:
        """
        List messages in a thread.

        Args:
            thread_ts: Thread timestamp
            limit: Maximum number of messages to return (default: 100)

        Returns:
            List of Message models
        """
        messages = ops.list_thread_messages(
            self.session,
            thread_ts=thread_ts,
            limit=limit,
        )
        return [MessageSchema.model_validate(m) for m in messages]
