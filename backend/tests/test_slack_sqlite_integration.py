"""
Real SQLite integration test for Slack service.

This test creates a real SQLite database, creates tables, runs operations,
and tests state management utilities just like an AI agent eval would.
"""

import os
import sys
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from eval_platform.eval_utilities import (
    clear_environment,
    create_snapshot,
    delete_snapshot,
)

# Import Slack models and operations
from services.slack.database.schema import Base, Channel, Message, Team, User
from services.slack.database.typed_operations import SlackOperations

# Tell pytest to skip conftest fixtures for this file
pytest_plugins = []


def simple_diff(session: Session, before_suffix: str, after_suffix: str):
    """
    Simple diff implementation for SQLite testing.

    Returns a dict-like object with inserts, updates, and deletes lists.
    """
    # Get all tables
    result = session.execute(
        text("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE '%_snapshot_%'
    """)
    )
    tables = [row[0] for row in result]

    inserts = []
    updates = []
    deletes = []

    for table in tables:
        before_table = f"{table}_snapshot_{before_suffix}"
        after_table = f"{table}_snapshot_{after_suffix}"

        # Get primary key column
        # For Slack, different tables have different PK names
        pk_cols = {
            "users": "user_id",
            "teams": "team_id",
            "channels": "channel_id",
            "messages": "message_id",
            "channel_members": "membership_id",
            "message_reactions": "reaction_id",
            "user_teams": "user_team_id",
            "files": "file_id",
        }
        pk_col = pk_cols.get(table, "id")

        try:
            # Find inserts (rows in after but not in before)
            insert_query = text(f"""
                SELECT * FROM "{after_table}"
                WHERE {pk_col} NOT IN (SELECT {pk_col} FROM "{before_table}")
            """)
            insert_results = session.execute(insert_query)
            columns = insert_results.keys()
            for row in insert_results:
                row_dict = dict(zip(columns, row))
                row_dict["__table__"] = table
                inserts.append(row_dict)

            # Find deletes (rows in before but not in after)
            delete_query = text(f"""
                SELECT * FROM "{before_table}"
                WHERE {pk_col} NOT IN (SELECT {pk_col} FROM "{after_table}")
            """)
            delete_results = session.execute(delete_query)
            for row in delete_results:
                row_dict = dict(zip(columns, row))
                row_dict["__table__"] = table
                deletes.append(row_dict)
        except Exception:
            # Skip tables that don't exist in both snapshots
            pass

    # Create a simple object with the same interface as DiffResult
    class SimpleDiffResult:
        def __init__(self, inserts, updates, deletes):
            self.inserts = inserts
            self.updates = updates
            self.deletes = deletes

    return SimpleDiffResult(inserts, updates, deletes)


class SimpleSessionManager:
    """Simple session manager for testing (replaces the full isolation engine)."""

    def __init__(self, engine):
        self.engine = engine
        self.base_engine = engine  # Add base_engine for Differ compatibility
        self.SessionLocal = sessionmaker(bind=engine)

    def get_session(self, schema_name: str = "main") -> Session:
        """Get a session for the database."""
        return self.SessionLocal()


@pytest.fixture
def sqlite_db():
    """Create a temporary SQLite database for testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    # Create engine
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Create session manager
    session_manager = SimpleSessionManager(engine)

    yield session, session_manager, db_path

    # Cleanup
    session.close()
    engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


def test_basic_operations(sqlite_db):
    """Test basic CRUD operations work with SQLite."""
    session, session_manager, db_path = sqlite_db

    # Initialize operations
    ops = SlackOperations(session)

    # Create a team
    team = ops.create_team(team_name="Acme Inc")

    # Verify team was created
    assert team.team_id is not None
    assert team.team_name == "Acme Inc"

    # Test Pydantic serialization
    team_dict = team.model_dump()
    assert team_dict["team_name"] == "Acme Inc"

    # Create a user
    user = ops.create_user(
        username="jdoe",
        email="jdoe@acme.com",
        real_name="John Doe",
        display_name="John",
    )

    # Verify user was created
    assert user.user_id is not None
    assert user.username == "jdoe"
    assert user.email == "jdoe@acme.com"
    assert user.real_name == "John Doe"

    # Test user serialization
    user_json = user.model_dump_json()
    assert "jdoe" in user_json

    # Create a channel
    channel = ops.create_channel(channel_name="general", team_id=team.team_id)

    # Verify channel was created
    assert channel.channel_id is not None
    assert channel.channel_name == "general"
    assert channel.team_id == team.team_id

    # Test channel serialization
    channel_dict = channel.model_dump()
    assert channel_dict["channel_name"] == "general"

    # Invite user to channel
    membership = ops.invite_user_to_channel(
        channel_id=channel.channel_id, user_id=user.user_id
    )

    # Verify membership was created
    assert membership is not None

    # Send a message
    message = ops.send_message(
        channel_id=channel.channel_id, user_id=user.user_id, text="Hello, world!"
    )

    # Verify message was created
    assert message.message_id is not None
    assert message.message_text == "Hello, world!"
    assert message.channel_id == channel.channel_id
    assert message.user_id == user.user_id

    # Retrieve user by ID
    retrieved_user = ops.get_user(user.user_id)
    assert retrieved_user is not None
    assert retrieved_user.user_id == user.user_id


def test_state_management_with_snapshots(sqlite_db):
    """Test state management utilities: snapshots and diffs."""
    session, session_manager, db_path = sqlite_db

    ops = SlackOperations(session)

    # Step 1: Create baseline state
    team = ops.create_team(team_name="Test Team")
    user = ops.create_user(username="agent", email="agent@example.com")
    channel = ops.create_channel(channel_name="test-channel", team_id=team.team_id)
    ops.invite_user_to_channel(channel_id=channel.channel_id, user_id=user.user_id)

    # Step 2: Take "before" snapshot
    before_snapshot = create_snapshot(session, "main", "before")
    assert before_snapshot.table_count > 0
    print(
        f"✓ Created before snapshot: {before_snapshot.table_count} tables, {before_snapshot.total_rows} rows"
    )

    # Step 3: Simulate agent action - send a message
    message = ops.send_message(
        channel_id=channel.channel_id, user_id=user.user_id, text="Test message"
    )
    session.commit()

    # Step 4: Take "after" snapshot
    after_snapshot = create_snapshot(session, "main", "after")
    print(
        f"✓ Created after snapshot: {after_snapshot.table_count} tables, {after_snapshot.total_rows} rows"
    )

    # Step 5: Get diff
    diff = simple_diff(session, "before", "after")

    # Step 6: Verify the diff captured the message creation
    assert len(diff.inserts) == 1, f"Expected 1 insert, got {len(diff.inserts)}"

    insert = diff.inserts[0]
    assert insert["__table__"] == "messages"
    assert insert["message_text"] == "Test message"
    assert insert["channel_id"] == channel.channel_id

    print("✓ Diff captured correctly:")
    print(f"  - Inserts: {len(diff.inserts)}")
    print(f"  - Updates: {len(diff.updates)}")
    print(f"  - Deletes: {len(diff.deletes)}")
    print(f"  - Created message: {insert['message_text']}")

    # Cleanup snapshots
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


def test_clear_environment(sqlite_db):
    """Test clearing environment state."""
    session, session_manager, db_path = sqlite_db

    ops = SlackOperations(session)

    # Create some data
    team = ops.create_team(team_name="Team 1")
    user1 = ops.create_user(username="user1", email="user1@example.com")
    user2 = ops.create_user(username="user2", email="user2@example.com")
    channel = ops.create_channel(channel_name="channel1", team_id=team.team_id)
    ops.invite_user_to_channel(channel_id=channel.channel_id, user_id=user1.user_id)
    message = ops.send_message(
        channel_id=channel.channel_id, user_id=user1.user_id, text="Test"
    )
    session.commit()

    # Verify data exists
    assert ops.get_user(user1.user_id) is not None
    assert ops.get_user(user2.user_id) is not None

    # Store IDs before clearing
    user1_id = user1.user_id
    user2_id = user2.user_id
    team_id = team.team_id
    channel_id = channel.channel_id
    message_id = message.message_id

    # Clear environment
    clear_environment(session)

    # Verify all data was deleted (query fresh from database)
    # Slack operations raise exceptions instead of returning None, so we verify differently
    from sqlalchemy import select

    assert (
        session.execute(
            select(User).where(User.user_id == user1_id)
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(User).where(User.user_id == user2_id)
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(Team).where(Team.team_id == team_id)
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(Channel).where(Channel.channel_id == channel_id)
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(Message).where(Message.message_id == message_id)
        ).scalar_one_or_none()
        is None
    )

    print("✓ Environment cleared successfully")


def test_complete_agent_eval_workflow(sqlite_db):
    """
    Complete workflow simulating an AI agent evaluation.

    This demonstrates exactly how an agent eval would work:
    1. Setup baseline state
    2. Take before snapshot
    3. Agent executes action
    4. Take after snapshot
    5. Verify changes with diff
    """
    session, session_manager, db_path = sqlite_db

    ops = SlackOperations(session)

    print("\n=== AI Agent Eval: Send Message Task ===")

    # Setup: Create baseline team, user, and channel
    team = ops.create_team(team_name="Test Team")
    user = ops.create_user(
        username="agent", email="agent@test.com", real_name="Test Agent"
    )
    channel = ops.create_channel(channel_name="general", team_id=team.team_id)
    ops.invite_user_to_channel(channel_id=channel.channel_id, user_id=user.user_id)
    session.commit()
    print(
        f"✓ Setup: Created team {team.team_id}, user {user.user_id}, channel {channel.channel_id}"
    )

    # Before snapshot
    create_snapshot(session, "main", "before")
    print("✓ Captured 'before' snapshot")

    # AGENT ACTION: Send a message saying "Hello team!"
    # (This is where the AI agent would use its tool)
    print("\n→ Agent action: Sending message 'Hello team!'...")
    message = ops.send_message(
        channel_id=channel.channel_id, user_id=user.user_id, text="Hello team!"
    )
    session.commit()
    print(f"✓ Agent sent message {message.message_id}")

    # After snapshot
    create_snapshot(session, "main", "after")
    print("✓ Captured 'after' snapshot")

    # Get diff (using simple_diff for SQLite)
    diff = simple_diff(session, "before", "after")
    print("\n=== Evaluation Results ===")

    # Assertions (this is what the eval framework would check)
    try:
        # Check exactly one item was inserted
        assert len(diff.inserts) == 1, f"Expected 1 insert, got {len(diff.inserts)}"
        print("✓ Assertion passed: Exactly 1 entity created")

        # Check it was a message
        insert = diff.inserts[0]
        assert insert["__table__"] == "messages", (
            f"Expected messages, got {insert['__table__']}"
        )
        print("✓ Assertion passed: Entity is a message")

        # Check message text
        assert insert["message_text"] == "Hello team!", (
            f"Expected 'Hello team!', got {insert['text']}"
        )
        print("✓ Assertion passed: Message text is 'Hello team!'")

        # Check channel ID
        assert insert["channel_id"] == channel.channel_id
        print("✓ Assertion passed: Message is in correct channel")

        # Check user ID
        assert insert["user_id"] == user.user_id
        print("✓ Assertion passed: Message sender is correct")

        print("\n🎉 EVAL PASSED: Agent successfully sent the message!")

    except AssertionError as e:
        print(f"\n❌ EVAL FAILED: {e}")
        raise

    finally:
        # Cleanup
        delete_snapshot(session, "main", "before")
        delete_snapshot(session, "main", "after")
        print("\n✓ Cleaned up snapshots")


def test_multiple_operations_diff(sqlite_db):
    """Test diff with multiple operations."""
    session, session_manager, db_path = sqlite_db

    ops = SlackOperations(session)

    # Setup baseline
    team = ops.create_team(team_name="Team")
    user = ops.create_user(username="user", email="user@example.com")
    channel = ops.create_channel(channel_name="channel", team_id=team.team_id)
    ops.invite_user_to_channel(channel_id=channel.channel_id, user_id=user.user_id)
    message1 = ops.send_message(
        channel_id=channel.channel_id, user_id=user.user_id, text="Message 1"
    )
    session.commit()

    # Before snapshot
    create_snapshot(session, "main", "before")

    # Multiple agent actions
    message2 = ops.send_message(
        channel_id=channel.channel_id, user_id=user.user_id, text="Message 2"
    )
    message3 = ops.send_message(
        channel_id=channel.channel_id, user_id=user.user_id, text="Message 3"
    )
    ops.update_message(message_id=message1.message_id, text="Updated Message 1")
    session.commit()

    # After snapshot
    create_snapshot(session, "main", "after")

    # Get diff
    diff = simple_diff(session, "before", "after")

    # Verify (note: simple_diff doesn't track updates, only inserts/deletes)
    assert len(diff.inserts) == 2, f"Expected 2 inserts, got {len(diff.inserts)}"

    # Check inserts
    insert_texts = {insert["message_text"] for insert in diff.inserts}
    assert "Message 2" in insert_texts
    assert "Message 3" in insert_texts

    print("✓ Multiple operations diff captured correctly:")
    print(f"  - {len(diff.inserts)} inserts")
    print(f"  - {len(diff.deletes)} deletes")
    print("  - Note: simple_diff for SQLite only tracks inserts/deletes")

    # Cleanup
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


if __name__ == "__main__":
    # Run tests directly with pytest
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
