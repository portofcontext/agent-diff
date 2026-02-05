"""
Real SQLite integration test - demonstrates actual DB operations and state management.

This test creates a real SQLite database, creates tables, runs operations,
and tests state management utilities just like an AI agent eval would.
"""

import os
import sys
import tempfile
import pytest
from datetime import datetime
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Import Box models and operations
from services.box.database.schema import Base, User, Folder, File
from services.box.database.typed_operations import BoxOperations
from eval_platform.eval_utilities import (
    create_snapshot,
    delete_snapshot,
    clear_environment,
    get_diff
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
    ops = BoxOperations(session)

    # Create a user
    user = ops.create_user(
        name="Test User",
        login="test@example.com",
        job_title="Engineer"
    )

    # Verify user was created
    assert user.id is not None
    assert user.name == "Test User"
    assert user.login == "test@example.com"
    assert user.job_title == "Engineer"

    # Test Pydantic serialization
    user_dict = user.model_dump()
    assert user_dict["name"] == "Test User"
    assert user_dict["login"] == "test@example.com"

    # Create root folder (manually without validation since it's special)
    root_folder = Folder(
        id="0",
        name="All Files",
        parent_id="0",  # Root folder points to itself
        owned_by_id=user.id,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    session.add(root_folder)
    session.commit()

    # Create a folder in root (now operations.py validation will pass)
    folder = ops.create_folder(
        name="Reports",
        parent_id="0",
        user_id=user.id
    )

    # Verify folder was created
    assert folder.id is not None
    assert folder.name == "Reports"
    assert folder.parent_id == "0"
    assert folder.owned_by_id == user.id

    # Test folder serialization
    folder_json = folder.model_dump_json()
    assert "Reports" in folder_json

    # Retrieve user by ID
    retrieved_user = ops.get_user(user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id

    # Retrieve folder by ID
    retrieved_folder = ops.get_folder(folder.id)
    assert retrieved_folder is not None
    assert retrieved_folder.name == "Reports"


def test_state_management_with_snapshots(sqlite_db):
    """Test state management utilities: snapshots and diffs."""
    session, session_manager, db_path = sqlite_db

    ops = BoxOperations(session)

    # Step 1: Create baseline state
    user = ops.create_user(
        name="Agent User",
        login="agent@example.com"
    )
    # Create root folder manually
    root = Folder(
        id="0",
        name="All Files",
        parent_id="0",
        owned_by_id=user.id,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    session.add(root)
    session.commit()

    # Step 2: Take "before" snapshot
    before_snapshot = create_snapshot(session, "main", "before")
    assert before_snapshot.table_count > 0
    print(f"✓ Created before snapshot: {before_snapshot.table_count} tables, {before_snapshot.total_rows} rows")

    # Step 3: Simulate agent action - create a folder
    folder = ops.create_folder(
        name="Q1 Reports",
        parent_id="0",
        user_id=user.id
    )
    session.commit()

    # Step 4: Take "after" snapshot
    after_snapshot = create_snapshot(session, "main", "after")
    print(f"✓ Created after snapshot: {after_snapshot.table_count} tables, {after_snapshot.total_rows} rows")

    # Step 5: Get diff
    diff = simple_diff(session, "before", "after")

    # Step 6: Verify the diff captured the folder creation
    assert len(diff.inserts) == 1, f"Expected 1 insert, got {len(diff.inserts)}"

    insert = diff.inserts[0]
    assert insert["__table__"] == "box_folders"
    assert insert["name"] == "Q1 Reports"
    assert insert["parent_id"] == "0"
    assert insert["owned_by_id"] == user.id

    print(f"✓ Diff captured correctly:")
    print(f"  - Inserts: {len(diff.inserts)}")
    print(f"  - Updates: {len(diff.updates)}")
    print(f"  - Deletes: {len(diff.deletes)}")
    print(f"  - Created folder: {insert['name']}")

    # Cleanup snapshots
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


def test_clear_environment(sqlite_db):
    """Test clearing environment state."""
    session, session_manager, db_path = sqlite_db

    ops = BoxOperations(session)

    # Create some data
    user1 = ops.create_user(name="User 1", login="user1@example.com")
    user2 = ops.create_user(name="User 2", login="user2@example.com")
    # Create root folder
    root = Folder(
        id="0",
        name="All Files",
        parent_id="0",
        owned_by_id=user1.id,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    session.add(root)
    folder = ops.create_folder(name="Test Folder", parent_id="0", user_id=user1.id)
    session.commit()

    # Verify data exists
    assert ops.get_user(user1.id) is not None
    assert ops.get_user(user2.id) is not None
    assert ops.get_folder(folder.id) is not None

    # Store IDs before clearing
    user1_id = user1.id
    user2_id = user2.id
    folder_id = folder.id

    # Clear environment
    clear_environment(session)

    # Verify all data was deleted (query fresh from database)
    assert ops.get_user(user1_id) is None
    assert ops.get_user(user2_id) is None
    assert ops.get_folder(folder_id) is None

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

    ops = BoxOperations(session)

    print("\n=== AI Agent Eval: Create Folder Task ===")

    # Setup: Create baseline user and root folder
    user = ops.create_user(
        name="Test Agent User",
        login="agent@test.com"
    )
    root = Folder(
        id="0",
        name="All Files",
        parent_id="0",
        owned_by_id=user.id,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    session.add(root)
    session.commit()
    print(f"✓ Setup: Created baseline user {user.id}")

    # Before snapshot
    create_snapshot(session, "main", "before")
    print("✓ Captured 'before' snapshot")

    # AGENT ACTION: Create a folder named "Q1 Reports"
    # (This is where the AI agent would use its tool)
    print("\n→ Agent action: Creating folder 'Q1 Reports'...")
    folder = ops.create_folder(
        name="Q1 Reports",
        parent_id="0",
        user_id=user.id
    )
    session.commit()
    print(f"✓ Agent created folder {folder.id}")

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

        # Check it was a folder
        insert = diff.inserts[0]
        assert insert["__table__"] == "box_folders", f"Expected box_folders, got {insert['__table__']}"
        print("✓ Assertion passed: Entity is a folder")

        # Check folder name
        assert insert["name"] == "Q1 Reports", f"Expected 'Q1 Reports', got {insert['name']}"
        print("✓ Assertion passed: Folder name is 'Q1 Reports'")

        # Check parent is root
        assert insert["parent_id"] == "0", f"Expected parent_id='0', got {insert['parent_id']}"
        print("✓ Assertion passed: Folder is in root")

        # Check owner
        assert insert["owned_by_id"] == user.id, f"Expected owned_by_id={user.id}, got {insert['user_id']}"
        print("✓ Assertion passed: Folder owner is correct")

        print("\n🎉 EVAL PASSED: Agent successfully created the folder!")

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

    ops = BoxOperations(session)

    # Setup baseline
    user = ops.create_user(name="User", login="user@example.com")
    root = Folder(
        id="0",
        name="All Files",
        parent_id="0",
        owned_by_id=user.id,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    session.add(root)
    folder1 = ops.create_folder(name="Folder 1", parent_id="0", user_id=user.id)
    session.commit()

    # Before snapshot
    create_snapshot(session, "main", "before")

    # Multiple agent actions
    folder2 = ops.create_folder(name="Folder 2", parent_id="0", user_id=user.id)
    folder3 = ops.create_folder(name="Folder 3", parent_id=folder1.id, user_id=user.id)
    ops.update_folder(folder1.id, user_id=user.id, name="Updated Folder 1")
    session.commit()

    # After snapshot
    create_snapshot(session, "main", "after")

    # Get diff
    diff = simple_diff(session, "before", "after")

    # Verify (note: simple_diff doesn't track updates, only inserts/deletes)
    assert len(diff.inserts) == 2, f"Expected 2 inserts, got {len(diff.inserts)}"

    # Check inserts
    insert_names = {insert["name"] for insert in diff.inserts}
    assert "Folder 2" in insert_names
    assert "Folder 3" in insert_names

    print("✓ Multiple operations diff captured correctly:")
    print(f"  - {len(diff.inserts)} inserts")
    print(f"  - {len(diff.deletes)} deletes")
    print(f"  - Note: simple_diff for SQLite only tracks inserts/deletes")

    # Cleanup
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


if __name__ == "__main__":
    # Run tests directly with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
