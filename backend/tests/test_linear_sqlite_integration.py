"""
Real SQLite integration test for Linear service.

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

# Import Linear models and operations
from services.linear.database.schema import Base, Issue, Organization, Team, User
from services.linear.database.typed_operations import LinearOperations

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

        # Get primary key column (assume 'id' for simplicity)
        pk_col = "id"

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
    ops = LinearOperations(session)

    # Create an organization
    org = ops.create_organization(name="Acme Inc")

    # Verify organization was created
    assert org.id is not None
    assert org.name == "Acme Inc"

    # Test Pydantic serialization
    org_dict = org.model_dump()
    assert org_dict["name"] == "Acme Inc"

    # Create a user
    user = ops.create_user(email="user@acme.com", name="John Doe", display_name="John")

    # Verify user was created
    assert user.id is not None
    assert user.email == "user@acme.com"
    assert user.name == "John Doe"

    # Test user serialization
    user_json = user.model_dump_json()
    assert "John Doe" in user_json

    # Create a team
    team = ops.create_team(
        name="Engineering",
        key="ENG",
        organization_id=org.id,
        description="Engineering team",
    )

    # Verify team was created
    assert team.id is not None
    assert team.name == "Engineering"
    assert team.key == "ENG"

    # Create an issue
    issue = ops.create_issue(
        team_id=team.id,
        title="Fix login bug",
        description="Users cannot log in",
        priority=2,
    )

    # Verify issue was created
    assert issue.id is not None
    assert issue.title == "Fix login bug"
    assert issue.teamId == team.id

    # Retrieve user by ID
    retrieved_user = ops.get_user(user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id


def test_state_management_with_snapshots(sqlite_db):
    """Test state management utilities: snapshots and diffs."""
    session, session_manager, db_path = sqlite_db

    ops = LinearOperations(session)

    # Step 1: Create baseline state
    org = ops.create_organization(name="Test Org")
    _user = ops.create_user(email="agent@example.com", name="Agent User")
    team = ops.create_team(name="Test Team", key="TEST", organization_id=org.id)

    # Step 2: Take "before" snapshot
    before_snapshot = create_snapshot(session, "main", "before")
    assert before_snapshot.table_count > 0
    print(
        f"✓ Created before snapshot: {before_snapshot.table_count} tables, {before_snapshot.total_rows} rows"
    )

    # Step 3: Simulate agent action - create an issue
    _issue = ops.create_issue(
        team_id=team.id,
        title="Implement feature X",
        description="Need to implement feature X",
    )
    session.commit()

    # Step 4: Take "after" snapshot
    after_snapshot = create_snapshot(session, "main", "after")
    print(
        f"✓ Created after snapshot: {after_snapshot.table_count} tables, {after_snapshot.total_rows} rows"
    )

    # Step 5: Get diff
    diff = simple_diff(session, "before", "after")

    # Step 6: Verify the diff captured the issue creation
    assert len(diff.inserts) == 1, f"Expected 1 insert, got {len(diff.inserts)}"

    insert = diff.inserts[0]
    assert insert["__table__"] == "issues"
    assert insert["title"] == "Implement feature X"
    assert insert["teamId"] == team.id

    print("✓ Diff captured correctly:")
    print(f"  - Inserts: {len(diff.inserts)}")
    print(f"  - Updates: {len(diff.updates)}")
    print(f"  - Deletes: {len(diff.deletes)}")
    print(f"  - Created issue: {insert['title']}")

    # Cleanup snapshots
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


def test_clear_environment(sqlite_db):
    """Test clearing environment state."""
    session, session_manager, db_path = sqlite_db

    ops = LinearOperations(session)

    # Create some data
    org = ops.create_organization(name="Org 1")
    user1 = ops.create_user(email="user1@example.com", name="User 1")
    user2 = ops.create_user(email="user2@example.com", name="User 2")
    team = ops.create_team(name="Team 1", key="T1", organization_id=org.id)
    issue = ops.create_issue(team_id=team.id, title="Issue 1")
    session.commit()

    # Verify data exists
    assert ops.get_user(user1.id) is not None
    assert ops.get_user(user2.id) is not None

    # Store IDs before clearing
    user1_id = user1.id
    user2_id = user2.id
    org_id = org.id
    team_id = team.id
    issue_id = issue.id

    # Clear environment
    clear_environment(session)

    # Verify all data was deleted (query fresh from database)
    from sqlalchemy import select

    assert (
        session.execute(select(User).where(User.id == user1_id)).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(select(User).where(User.id == user2_id)).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(Organization).where(Organization.id == org_id)
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(select(Team).where(Team.id == team_id)).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(select(Issue).where(Issue.id == issue_id)).scalar_one_or_none()
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

    ops = LinearOperations(session)

    print("\n=== AI Agent Eval: Create Issue Task ===")

    # Setup: Create baseline organization, user, and team
    org = ops.create_organization(name="Test Org")
    user = ops.create_user(email="agent@test.com", name="Test Agent")
    team = ops.create_team(name="Engineering", key="ENG", organization_id=org.id)
    session.commit()
    print(f"✓ Setup: Created org {org.id}, user {user.id}, team {team.id}")

    # Before snapshot
    create_snapshot(session, "main", "before")
    print("✓ Captured 'before' snapshot")

    # AGENT ACTION: Create an issue titled "Fix authentication bug"
    # (This is where the AI agent would use its tool)
    print("\n→ Agent action: Creating issue 'Fix authentication bug'...")
    issue = ops.create_issue(
        team_id=team.id,
        title="Fix authentication bug",
        description="Users cannot authenticate properly",
        priority=3,
    )
    session.commit()
    print(f"✓ Agent created issue {issue.id}")

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

        # Check it was an issue
        insert = diff.inserts[0]
        assert insert["__table__"] == "issues", (
            f"Expected issues, got {insert['__table__']}"
        )
        print("✓ Assertion passed: Entity is an issue")

        # Check issue title
        assert insert["title"] == "Fix authentication bug", (
            f"Expected 'Fix authentication bug', got {insert['title']}"
        )
        print("✓ Assertion passed: Issue title is 'Fix authentication bug'")

        # Check issue description
        assert insert["description"] == "Users cannot authenticate properly"
        print("✓ Assertion passed: Issue description is correct")

        # Check team ID
        assert insert["teamId"] == team.id
        print("✓ Assertion passed: Issue is in correct team")

        print("\n🎉 EVAL PASSED: Agent successfully created the issue!")

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

    ops = LinearOperations(session)

    # Setup baseline
    org = ops.create_organization(name="Org")
    _user = ops.create_user(email="user@example.com", name="User")
    team = ops.create_team(name="Team", key="T", organization_id=org.id)
    issue1 = ops.create_issue(team_id=team.id, title="Issue 1")
    session.commit()

    # Before snapshot
    create_snapshot(session, "main", "before")

    # Multiple agent actions
    _issue2 = ops.create_issue(team_id=team.id, title="Issue 2")
    _issue3 = ops.create_issue(team_id=team.id, title="Issue 3")
    ops.update_issue(issue1.id, title="Updated Issue 1")
    session.commit()

    # After snapshot
    create_snapshot(session, "main", "after")

    # Get diff
    diff = simple_diff(session, "before", "after")

    # Verify (note: simple_diff doesn't track updates, only inserts/deletes)
    assert len(diff.inserts) == 2, f"Expected 2 inserts, got {len(diff.inserts)}"

    # Check inserts
    insert_titles = {insert["title"] for insert in diff.inserts}
    assert "Issue 2" in insert_titles
    assert "Issue 3" in insert_titles

    print("✓ Multiple operations diff captured correctly:")
    print(f"  - {len(diff.inserts)} inserts")
    print(f"  - {len(diff.deletes)} deletes")
    print("  - Note: simple_diff for SQLite only tracks inserts/deletes")

    # Cleanup
    delete_snapshot(session, "main", "before")
    delete_snapshot(session, "main", "after")


def test_comment_operations(sqlite_db):
    """Test comment operations."""
    session, session_manager, db_path = sqlite_db

    ops = LinearOperations(session)

    # Setup
    org = ops.create_organization(name="Org")
    user = ops.create_user(email="user@example.com", name="User")
    team = ops.create_team(name="Team", key="T", organization_id=org.id)
    issue = ops.create_issue(team_id=team.id, title="Issue with comments")
    session.commit()

    # Create a comment
    comment = ops.create_comment(
        issue_id=issue.id, body="This is a comment", user_id=user.id
    )
    session.commit()

    # Verify comment was created
    assert comment.id is not None
    assert comment.body == "This is a comment"
    assert comment.issueId == issue.id

    # Update comment
    updated_comment = ops.update_comment(comment.id, "Updated comment")
    session.commit()

    assert updated_comment.body == "Updated comment"

    # Retrieve comment
    retrieved_comment = ops.get_comment(comment.id)
    assert retrieved_comment is not None
    assert retrieved_comment.body == "Updated comment"

    print("✓ Comment operations working correctly")


if __name__ == "__main__":
    # Run tests directly with pytest
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
