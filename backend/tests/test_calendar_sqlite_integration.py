"""
Real SQLite integration test for Google Calendar service.

This test creates a real SQLite database, creates tables, runs operations,
and tests state management utilities just like an AI agent eval would.
"""

import os
import sys
import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Set dummy DATABASE_URL to avoid import error (we create our own DB)
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///dummy.db")

# Import Calendar models and operations
from services.calendar.database.schema import Base, User, Calendar, Event
from services.calendar.database.typed_operations import CalendarOperations
from eval_platform.eval_utilities import (
    create_snapshot,
    delete_snapshot,
    clear_environment,
)

# Tell pytest to skip conftest fixtures for this file
pytest_plugins = []


def simple_diff(session: Session, before_suffix: str, after_suffix: str):
    """
    Simple diff implementation for SQLite testing.

    Returns a dict-like object with inserts, updates, and deletes lists.
    """
    # Get all tables
    result = session.execute(text("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE '%_snapshot_%'
    """))
    tables = [row[0] for row in result]

    inserts = []
    updates = []
    deletes = []

    for table in tables:
        before_table = f"{table}_snapshot_{before_suffix}"
        after_table = f"{table}_snapshot_{after_suffix}"

        # Get primary key column (assume 'id' for simplicity)
        pk_col = 'id'

        # Find inserts (rows in after but not in before)
        insert_query = text(f"""
            SELECT * FROM "{after_table}"
            WHERE {pk_col} NOT IN (SELECT {pk_col} FROM "{before_table}")
        """)
        insert_results = session.execute(insert_query)
        columns = insert_results.keys()
        for row in insert_results:
            row_dict = dict(zip(columns, row))
            row_dict['__table__'] = table
            inserts.append(row_dict)

        # Find deletes (rows in before but not in after)
        delete_query = text(f"""
            SELECT * FROM "{before_table}"
            WHERE {pk_col} NOT IN (SELECT {pk_col} FROM "{after_table}")
        """)
        delete_results = session.execute(delete_query)
        for row in delete_results:
            row_dict = dict(zip(columns, row))
            row_dict['__table__'] = table
            deletes.append(row_dict)

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
    ops = CalendarOperations(session)

    # Create a user (automatically creates primary calendar)
    user = ops.create_user(
        email="test@example.com",
        display_name="Test User"
    )

    # Verify user was created
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"

    # Test Pydantic serialization
    user_dict = user.model_dump()
    assert user_dict["email"] == "test@example.com"
    assert user_dict["display_name"] == "Test User"

    # Verify primary calendar was auto-created
    primary_calendar = ops.get_calendar(user.email)
    assert primary_calendar is not None
    assert primary_calendar.id == user.email
    assert primary_calendar.owner_id == user.id

    # Create a secondary calendar
    calendar = ops.create_calendar(
        owner_id=user.id,
        summary="Work Calendar",
        description="Calendar for work events",
        time_zone="America/New_York"
    )

    # Verify calendar was created
    assert calendar.id is not None
    assert calendar.summary == "Work Calendar"
    assert calendar.description == "Calendar for work events"
    assert calendar.time_zone == "America/New_York"
    assert calendar.owner_id == user.id

    # Test calendar serialization
    calendar_json = calendar.model_dump_json()
    assert "Work Calendar" in calendar_json

    # Create an event
    event = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Team Meeting",
        description="Weekly team sync",
        start={"dateTime": "2024-01-15T10:00:00Z"},
        end={"dateTime": "2024-01-15T11:00:00Z"}
    )

    # Verify event was created
    assert event.id is not None
    assert event.summary == "Team Meeting"
    assert event.description == "Weekly team sync"
    assert event.calendar_id == calendar.id

    # Retrieve event by ID
    retrieved_event = ops.get_event(calendar.id, event.id, user.id)
    assert retrieved_event is not None
    assert retrieved_event.id == event.id
    assert retrieved_event.summary == "Team Meeting"


def test_state_management_with_snapshots(sqlite_db):
    """Test state management utilities: snapshots and diffs."""
    session, session_manager, db_path = sqlite_db

    ops = CalendarOperations(session)

    # Step 1: Create baseline state
    user = ops.create_user(
        email="agent@example.com",
        display_name="Agent User"
    )
    calendar = ops.create_calendar(
        owner_id=user.id,
        summary="Test Calendar"
    )

    # Step 2: Take "before" snapshot
    before_snapshot = create_snapshot(session, "main", "before")
    assert before_snapshot.table_count > 0
    print(f"✓ Created before snapshot: {before_snapshot.table_count} tables, {before_snapshot.total_rows} rows")

    # Step 3: Simulate agent action - create an event
    event = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Q1 Planning",
        start={"dateTime": "2024-01-20T14:00:00Z"},
        end={"dateTime": "2024-01-20T15:00:00Z"}
    )
    session.commit()

    # Step 4: Take "after" snapshot
    after_snapshot = create_snapshot(session, "main", "after")
    print(f"✓ Created after snapshot: {after_snapshot.table_count} tables, {after_snapshot.total_rows} rows")

    # Step 5: Get diff
    diff = simple_diff(session, "before", "after")

    # Step 6: Verify the diff captured the event creation
    assert len(diff.inserts) == 1, f"Expected 1 insert, got {len(diff.inserts)}"

    insert = diff.inserts[0]
    assert insert["__table__"] == "calendar_events"
    assert insert["summary"] == "Q1 Planning"
    assert insert["calendar_id"] == calendar.id

    print(f"✓ Diff captured correctly:")
    print(f"  - Inserts: {len(diff.inserts)}")
    print(f"  - Updates: {len(diff.updates)}")
    print(f"  - Deletes: {len(diff.deletes)}")
    print(f"  - Created event: {insert['summary']}")

    # Cleanup snapshots
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


def test_clear_environment(sqlite_db):
    """Test clearing environment state."""
    session, session_manager, db_path = sqlite_db

    ops = CalendarOperations(session)

    # Create some data
    user1 = ops.create_user(email="user1@example.com", display_name="User 1")
    user2 = ops.create_user(email="user2@example.com", display_name="User 2")
    calendar1 = ops.create_calendar(owner_id=user1.id, summary="Calendar 1")
    event1 = ops.create_event(
        calendar_id=calendar1.id,
        user_id=user1.id,
        summary="Event 1",
        start={"dateTime": "2024-01-15T10:00:00Z"},
        end={"dateTime": "2024-01-15T11:00:00Z"}
    )
    session.commit()

    # Verify data exists
    assert ops.get_user(user1.id) is not None
    assert ops.get_user(user2.id) is not None
    assert ops.get_calendar(calendar1.id) is not None
    assert ops.get_event(calendar1.id, event1.id, user1.id) is not None

    # Store IDs before clearing
    user1_id = user1.id
    user2_id = user2.id
    calendar1_id = calendar1.id
    event1_id = event1.id

    # Clear environment
    clear_environment(session)

    # Verify all data was deleted (query fresh from database)
    assert ops.get_user(user1_id) is None
    assert ops.get_user(user2_id) is None
    # Calendar operations raise exceptions instead of returning None, so we verify differently
    # Just query the raw table to verify deletion
    from sqlalchemy import select
    from services.calendar.database.schema import Calendar, Event
    assert session.execute(select(Calendar).where(Calendar.id == calendar1_id)).scalar_one_or_none() is None
    assert session.execute(select(Event).where(Event.id == event1_id)).scalar_one_or_none() is None

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

    ops = CalendarOperations(session)

    print("\n=== AI Agent Eval: Create Event Task ===")

    # Setup: Create baseline user and calendar
    user = ops.create_user(
        email="agent@test.com",
        display_name="Test Agent User"
    )
    calendar = ops.create_calendar(
        owner_id=user.id,
        summary="Test Calendar"
    )
    session.commit()
    print(f"✓ Setup: Created baseline user {user.id} and calendar {calendar.id}")

    # Before snapshot
    create_snapshot(session, "main", "before")
    print("✓ Captured 'before' snapshot")

    # AGENT ACTION: Create an event named "Q1 Planning"
    # (This is where the AI agent would use its tool)
    print("\n→ Agent action: Creating event 'Q1 Planning'...")
    event = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Q1 Planning",
        description="Quarterly planning meeting",
        location="Conference Room A",
        start={"dateTime": "2024-01-20T14:00:00Z"},
        end={"dateTime": "2024-01-20T15:30:00Z"}
    )
    session.commit()
    print(f"✓ Agent created event {event.id}")

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

        # Check it was an event
        insert = diff.inserts[0]
        assert insert["__table__"] == "calendar_events", f"Expected calendar_events, got {insert['__table__']}"
        print("✓ Assertion passed: Entity is an event")

        # Check event summary
        assert insert["summary"] == "Q1 Planning", f"Expected 'Q1 Planning', got {insert['summary']}"
        print("✓ Assertion passed: Event summary is 'Q1 Planning'")

        # Check event description
        assert insert["description"] == "Quarterly planning meeting"
        print("✓ Assertion passed: Event description is correct")

        # Check calendar ID
        assert insert["calendar_id"] == calendar.id, f"Expected calendar_id={calendar.id}, got {insert['calendar_id']}"
        print("✓ Assertion passed: Event is in correct calendar")

        print("\n🎉 EVAL PASSED: Agent successfully created the event!")

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

    ops = CalendarOperations(session)

    # Setup baseline
    user = ops.create_user(email="user@example.com", display_name="User")
    calendar = ops.create_calendar(owner_id=user.id, summary="Calendar")
    event1 = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Event 1",
        start={"dateTime": "2024-01-15T10:00:00Z"},
        end={"dateTime": "2024-01-15T11:00:00Z"}
    )
    session.commit()

    # Before snapshot
    create_snapshot(session, "main", "before")

    # Multiple agent actions
    event2 = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Event 2",
        start={"dateTime": "2024-01-16T10:00:00Z"},
        end={"dateTime": "2024-01-16T11:00:00Z"}
    )
    event3 = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Event 3",
        start={"dateTime": "2024-01-17T10:00:00Z"},
        end={"dateTime": "2024-01-17T11:00:00Z"}
    )
    ops.update_event(calendar_id=calendar.id, event_id=event1.id, user_id=user.id, summary="Updated Event 1"
    )
    session.commit()

    # After snapshot
    create_snapshot(session, "main", "after")

    # Get diff
    diff = simple_diff(session, "before", "after")

    # Verify (note: simple_diff doesn't track updates, only inserts/deletes)
    assert len(diff.inserts) == 2, f"Expected 2 inserts, got {len(diff.inserts)}"

    # Check inserts
    insert_summaries = {insert["summary"] for insert in diff.inserts}
    assert "Event 2" in insert_summaries
    assert "Event 3" in insert_summaries

    print("✓ Multiple operations diff captured correctly:")
    print(f"  - {len(diff.inserts)} inserts")
    print(f"  - {len(diff.deletes)} deletes")
    print(f"  - Note: simple_diff for SQLite only tracks inserts/deletes")

    # Cleanup
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


def test_list_operations(sqlite_db):
    """Test list operations."""
    session, session_manager, db_path = sqlite_db

    ops = CalendarOperations(session)

    # Create test data
    user = ops.create_user(email="test@example.com", display_name="Test User")
    calendar = ops.create_calendar(owner_id=user.id, summary="Test Calendar")

    # Create multiple events
    event1 = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Event 1",
        start={"dateTime": "2024-01-15T10:00:00Z"},
        end={"dateTime": "2024-01-15T11:00:00Z"}
    )
    event2 = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Event 2",
        start={"dateTime": "2024-01-16T10:00:00Z"},
        end={"dateTime": "2024-01-16T11:00:00Z"}
    )
    event3 = ops.create_event(
        user_id=user.id,
        calendar_id=calendar.id,
        summary="Event 3",
        start={"dateTime": "2024-01-17T10:00:00Z"},
        end={"dateTime": "2024-01-17T11:00:00Z"}
    )
    session.commit()

    # List all events
    events = ops.list_events(calendar_id=calendar.id, user_id=user.id)
    assert len(events) == 3

    # Verify all events are returned
    event_summaries = {e.summary for e in events}
    assert "Event 1" in event_summaries
    assert "Event 2" in event_summaries
    assert "Event 3" in event_summaries

    print("✓ List operations working correctly")


if __name__ == "__main__":
    # Run tests directly with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
