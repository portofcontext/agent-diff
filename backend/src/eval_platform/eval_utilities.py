"""
Evaluation Utilities - State management for AI agent testing.

This module provides clean, typed interfaces for:
1. Seeding test environments with baseline data
2. Clearing/resetting state between test runs
3. Capturing diffs (database changes) for assertions

Use these utilities to write evals that:
- Start from a known baseline state (seed)
- Run agent actions (your test code)
- Capture what changed (diff)
- Assert against expected changes
- Clean up for next test (clear)

Example:
    # Setup: Seed baseline state
    env = seed_box_environment(session, user_email="test@example.com")

    # Capture before state
    snapshot_id = create_snapshot(session, env.schema_name, "before")

    # Run agent action
    agent.execute("Create a folder named 'Reports' in the root")

    # Capture after state
    create_snapshot(session, env.schema_name, "after")

    # Get diff
    diff = get_diff(session, env.schema_name, "before", "after")

    # Assert
    assert len(diff.inserts) == 1
    assert diff.inserts[0]['name'] == 'Reports'

    # Cleanup
    clear_environment(session, env.schema_name)
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import text

from eval_platform.evaluationEngine.differ import Differ
from eval_platform.evaluationEngine.models import DiffResult
from eval_platform.isolationEngine.session import SessionManager

# Export new clean API (import at end to avoid circular dependencies)
__all__ = [
    # New clean API
    'EvalEnvironment',
    'DiffTracker',
    'ChangeRecord',
    'setup_eval',
    # Legacy API
    'EnvironmentInfo',
    'SnapshotInfo',
    'SeedResult',
    'create_environment',
    'clear_environment',
    'delete_environment',
    'create_snapshot',
    'delete_snapshot',
    'get_diff',
    'get_inserts_only',
    'get_updates_only',
    'get_deletes_only',
    'seed_box_baseline',
    'seed_calendar_baseline',
    'seed_slack_baseline',
    'seed_linear_baseline',
    'EvalContext',
]


# ==============================================================================
# DATA CLASSES FOR TYPED RETURNS
# ==============================================================================

@dataclass
class EnvironmentInfo:
    """Information about a test environment."""
    id: UUID
    service: Literal["box", "calendar", "slack", "linear"]
    schema_name: str
    status: str
    template_id: Optional[UUID]
    impersonate_user_id: Optional[str]
    impersonate_email: Optional[str]
    created_at: datetime


@dataclass
class SnapshotInfo:
    """Information about a database snapshot."""
    snapshot_id: str
    schema_name: str
    table_count: int
    total_rows: int
    created_at: datetime


@dataclass
class SeedResult:
    """Result of seeding an environment."""
    environment: EnvironmentInfo
    users_created: int
    folders_created: int
    files_created: int
    other_entities: Dict[str, int]


# ==============================================================================
# ENVIRONMENT MANAGEMENT
# ==============================================================================

def create_environment(
    session_manager: SessionManager,
    *,
    service: Literal["box", "calendar", "slack", "linear"],
    template_name: Optional[str] = None,
    impersonate_user_id: Optional[str] = None,
    impersonate_email: Optional[str] = None
) -> EnvironmentInfo:
    """
    Create a new isolated test environment.

    Args:
        session_manager: SessionManager instance
        service: Service name ("box", "calendar", "slack", "linear")
        template_name: Optional template to copy from (uses default if not provided)
        impersonate_user_id: Optional user ID to impersonate in this environment
        impersonate_email: Optional user email to impersonate

    Returns:
        EnvironmentInfo with details about the created environment

    Example:
        env = create_environment(
            session_manager,
            service="box",
            impersonate_email="test@example.com"
        )
        print(f"Environment {env.schema_name} ready")
    """
    # This would integrate with your existing isolation engine
    # For now, returning a typed structure
    raise NotImplementedError("Integrate with isolation engine")


def clear_environment(session: Session, schema_name: str = "main") -> None:
    """
    Clear all data from an environment (delete all rows, keep schema).

    Args:
        session: SQLAlchemy session
        schema_name: Schema name (for PostgreSQL) or "main" for SQLite

    Example:
        clear_environment(session)
    """
    # Detect if using SQLite or PostgreSQL
    dialect = session.bind.dialect.name

    if dialect == "sqlite":
        # SQLite: Get all tables from sqlite_master
        result = session.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE '%_snapshot_%'
        """))
        tables = [row[0] for row in result]

        # Delete from all tables
        for table in tables:
            session.execute(text(f'DELETE FROM "{table}"'))
    else:
        # PostgreSQL: Get all tables in the schema
        result = session.execute(text(f"""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = '{schema_name}'
        """))
        tables = [row[0] for row in result]

        # Truncate all tables
        for table in tables:
            session.execute(text(f'TRUNCATE TABLE {schema_name}."{table}" CASCADE'))

    session.commit()


def delete_environment(session: Session, schema_name: str = "main") -> None:
    """
    Completely delete an environment (drop schema and all data).

    For SQLite, this drops all tables. For PostgreSQL, this drops the schema.

    Args:
        session: SQLAlchemy session
        schema_name: Schema name (for PostgreSQL) or "main" for SQLite

    Warning:
        This is destructive and cannot be undone!

    Example:
        delete_environment(session)
    """
    dialect = session.bind.dialect.name

    if dialect == "sqlite":
        # SQLite: Drop all tables
        result = session.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
        """))
        tables = [row[0] for row in result]

        for table in tables:
            session.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
    else:
        # PostgreSQL: Drop schema
        session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))

    session.commit()


# ==============================================================================
# SNAPSHOT MANAGEMENT (for diffing)
# ==============================================================================

def create_snapshot(
    session: Session,
    schema_name: str,
    snapshot_suffix: str,
    *,
    tables: Optional[List[str]] = None
) -> SnapshotInfo:
    """
    Create a snapshot of the current database state.

    This copies all tables (or specified tables) to snapshot tables
    with the given suffix. Used for before/after comparisons.

    Args:
        session: SQLAlchemy session
        schema_name: Schema name (for PostgreSQL) or "main" for SQLite
        snapshot_suffix: Suffix for snapshot tables (e.g., "before", "after")
        tables: Optional list of specific tables to snapshot (snapshots all if None)

    Returns:
        SnapshotInfo with details about the snapshot

    Example:
        # Before agent runs
        create_snapshot(session, "main", "before")

        # ... agent executes actions ...

        # After agent runs
        create_snapshot(session, "main", "after")
    """
    dialect = session.bind.dialect.name

    # Get tables to snapshot
    if tables is None:
        if dialect == "sqlite":
            result = session.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE '%_snapshot_%'
            """))
        else:
            result = session.execute(text(f"""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = '{schema_name}'
                AND tablename NOT LIKE '%_snapshot_%'
            """))
        tables = [row[0] for row in result]

    total_rows = 0
    for table in tables:
        # Create snapshot table
        snapshot_table = f"{table}_snapshot_{snapshot_suffix}"

        if dialect == "sqlite":
            session.execute(text(f'DROP TABLE IF EXISTS "{snapshot_table}"'))
            session.execute(text(f'CREATE TABLE "{snapshot_table}" AS SELECT * FROM "{table}"'))
            count_result = session.execute(text(f'SELECT COUNT(*) FROM "{snapshot_table}"'))
        else:
            session.execute(text(f"""
                DROP TABLE IF EXISTS {schema_name}."{snapshot_table}" CASCADE;
                CREATE TABLE {schema_name}."{snapshot_table}" AS
                SELECT * FROM {schema_name}."{table}";
            """))
            count_result = session.execute(text(f'SELECT COUNT(*) FROM {schema_name}."{snapshot_table}"'))

        total_rows += count_result.scalar()

    session.commit()

    return SnapshotInfo(
        snapshot_id=f"{schema_name}_{snapshot_suffix}",
        schema_name=schema_name,
        table_count=len(tables),
        total_rows=total_rows,
        created_at=datetime.now()
    )


def delete_snapshot(
    session: Session,
    schema_name: str,
    snapshot_suffix: str
) -> None:
    """
    Delete a snapshot (drop all snapshot tables with the given suffix).

    Args:
        session: SQLAlchemy session
        schema_name: Schema name (for PostgreSQL) or "main" for SQLite
        snapshot_suffix: Suffix of snapshot tables to delete

    Example:
        delete_snapshot(session, "main", "before")
    """
    dialect = session.bind.dialect.name

    # Find all snapshot tables with this suffix
    if dialect == "sqlite":
        result = session.execute(text(f"""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name LIKE '%_snapshot_{snapshot_suffix}'
        """))
    else:
        result = session.execute(text(f"""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = '{schema_name}'
            AND tablename LIKE '%_snapshot_{snapshot_suffix}'
        """))

    tables = [row[0] for row in result]

    # Drop them
    for table in tables:
        if dialect == "sqlite":
            session.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
        else:
            session.execute(text(f'DROP TABLE IF EXISTS {schema_name}."{table}" CASCADE'))

    session.commit()


# ==============================================================================
# DIFF OPERATIONS
# ==============================================================================

def get_diff(
    session_manager: SessionManager,
    schema_name: str,
    before_suffix: str,
    after_suffix: str,
    *,
    exclude_columns: Optional[List[str]] = None
) -> DiffResult:
    """
    Get the diff between two snapshots (what changed).

    Returns:
        DiffResult with:
        - inserts: List of rows that were added
        - updates: List of rows that were modified
        - deletes: List of rows that were removed

    Each item includes a '__table__' key identifying which table it came from.

    Args:
        session_manager: SessionManager instance
        schema_name: PostgreSQL schema name
        before_suffix: Suffix of "before" snapshot
        after_suffix: Suffix of "after" snapshot
        exclude_columns: Optional list of column names to exclude from comparison
                        (e.g., ['modified_at'] to ignore timestamp changes)

    Returns:
        DiffResult with inserts, updates, and deletes

    Example:
        diff = get_diff(session_manager, "test_env", "before", "after")

        print(f"Inserted: {len(diff.inserts)} rows")
        for insert in diff.inserts:
            print(f"  {insert['__table__']}: {insert}")

        print(f"Updated: {len(diff.updates)} rows")
        for update in diff.updates:
            print(f"  {update['__table__']}: {update['before']} -> {update['after']}")

        print(f"Deleted: {len(diff.deletes)} rows")
    """
    # Get environment ID from schema name (you may need to query this)
    environment_id = schema_name  # Placeholder

    differ = Differ(
        schema=schema_name,
        environment_id=environment_id,
        session_manager=session_manager
    )

    return differ.get_diff(
        before_suffix=before_suffix,
        after_suffix=after_suffix
    )


def get_inserts_only(
    session_manager: SessionManager,
    schema_name: str,
    before_suffix: str,
    after_suffix: str
) -> List[Dict[str, Any]]:
    """
    Get only the inserted rows (convenience function).

    Args:
        session_manager: SessionManager instance
        schema_name: PostgreSQL schema name
        before_suffix: Suffix of "before" snapshot
        after_suffix: Suffix of "after" snapshot

    Returns:
        List of inserted rows, each with '__table__' key

    Example:
        inserts = get_inserts_only(session_manager, "test_env", "before", "after")
        folders = [r for r in inserts if r['__table__'] == 'box_folders']
        assert len(folders) == 1
        assert folders[0]['name'] == 'Reports'
    """
    diff = get_diff(session_manager, schema_name, before_suffix, after_suffix)
    return diff.inserts


def get_updates_only(
    session_manager: SessionManager,
    schema_name: str,
    before_suffix: str,
    after_suffix: str
) -> List[Dict[str, Any]]:
    """
    Get only the updated rows (convenience function).

    Returns list of dicts with '__table__', 'before', and 'after' keys.
    """
    diff = get_diff(session_manager, schema_name, before_suffix, after_suffix)
    return diff.updates


def get_deletes_only(
    session_manager: SessionManager,
    schema_name: str,
    before_suffix: str,
    after_suffix: str
) -> List[Dict[str, Any]]:
    """
    Get only the deleted rows (convenience function).

    Returns list of deleted rows, each with '__table__' key.
    """
    diff = get_diff(session_manager, schema_name, before_suffix, after_suffix)
    return diff.deletes


# ==============================================================================
# SEEDING HELPERS (wrappers around existing seed scripts)
# ==============================================================================

def seed_box_baseline(
    session: Session,
    schema_name: str,
    *,
    admin_email: str = "admin@box.local",
    num_users: int = 3,
    num_folders: int = 5,
    num_files: int = 10
) -> SeedResult:
    """
    Seed a Box environment with baseline test data.

    Creates a typical Box environment with users, folders, and files.

    Args:
        session: SQLAlchemy session
        schema_name: PostgreSQL schema name to seed
        admin_email: Email for admin user
        num_users: Number of users to create
        num_folders: Number of folders to create
        num_files: Number of files to create

    Returns:
        SeedResult with counts of created entities

    Example:
        result = seed_box_baseline(
            session,
            "test_env",
            admin_email="test@example.com",
            num_users=5
        )
        print(f"Created {result.users_created} users")
    """
    # This would call your existing seed scripts or replicate their logic
    # For now, showing the interface
    raise NotImplementedError("Integrate with existing seed scripts")


def seed_calendar_baseline(
    session: Session,
    schema_name: str,
    *,
    user_email: str = "user@calendar.local",
    num_calendars: int = 2,
    num_events: int = 10
) -> SeedResult:
    """Seed a Calendar environment with baseline test data."""
    raise NotImplementedError("Integrate with existing seed scripts")


def seed_slack_baseline(
    session: Session,
    schema_name: str,
    *,
    team_name: str = "Test Team",
    num_channels: int = 5,
    num_users: int = 10
) -> SeedResult:
    """Seed a Slack environment with baseline test data."""
    raise NotImplementedError("Integrate with existing seed scripts")


def seed_linear_baseline(
    session: Session,
    schema_name: str,
    *,
    team_name: str = "Engineering",
    num_projects: int = 3,
    num_issues: int = 20
) -> SeedResult:
    """Seed a Linear environment with baseline test data."""
    raise NotImplementedError("Integrate with existing seed scripts")


# ==============================================================================
# EVALUATION WORKFLOW HELPER
# ==============================================================================

class EvalContext:
    """
    Context manager for running a single evaluation test.

    Handles setup (snapshot before), teardown (cleanup), and provides
    easy access to diff results.

    Usage:
        with EvalContext(session_manager, "test_env") as ctx:
            # Agent executes here
            agent.execute("Create folder 'Reports'")

            # Get diff automatically
            diff = ctx.get_diff()

            # Assert
            assert len(diff.inserts) == 1
            assert diff.inserts[0]['name'] == 'Reports'

        # Snapshots automatically cleaned up
    """

    def __init__(
        self,
        session_manager: SessionManager,
        schema_name: str,
        *,
        before_suffix: str = "before",
        after_suffix: str = "after",
        cleanup_snapshots: bool = True
    ):
        """
        Initialize eval context.

        Args:
            session_manager: SessionManager instance
            schema_name: Schema name to monitor
            before_suffix: Suffix for before snapshot (default: "before")
            after_suffix: Suffix for after snapshot (default: "after")
            cleanup_snapshots: Whether to delete snapshots on exit (default: True)
        """
        self.session_manager = session_manager
        self.schema_name = schema_name
        self.before_suffix = before_suffix
        self.after_suffix = after_suffix
        self.cleanup_snapshots = cleanup_snapshots
        self._diff: Optional[DiffResult] = None

    def __enter__(self) -> 'EvalContext':
        """Create before snapshot."""
        # For SQLite, use the direct session; for PostgreSQL, use schema-specific session
        session = self.session_manager.get_session(self.schema_name)
        create_snapshot(session, self.schema_name, self.before_suffix)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Create after snapshot and cleanup."""
        session = self.session_manager.get_session(self.schema_name)

        # Create after snapshot
        create_snapshot(session, self.schema_name, self.after_suffix)

        # Cleanup if requested
        if self.cleanup_snapshots:
            delete_snapshot(session, self.schema_name, self.before_suffix)
            delete_snapshot(session, self.schema_name, self.after_suffix)

    def get_diff(self) -> DiffResult:
        """Get the diff between before and after snapshots."""
        if self._diff is None:
            self._diff = get_diff(
                self.session_manager,
                self.schema_name,
                self.before_suffix,
                self.after_suffix
            )
        return self._diff

    @property
    def inserts(self) -> List[Dict[str, Any]]:
        """Convenience property for getting inserts."""
        return self.get_diff().inserts

    @property
    def updates(self) -> List[Dict[str, Any]]:
        """Convenience property for getting updates."""
        return self.get_diff().updates

    @property
    def deletes(self) -> List[Dict[str, Any]]:
        """Convenience property for getting deletes."""
        return self.get_diff().deletes


# ==============================================================================
# NEW CLEAN API IMPORTS (at end to avoid circular dependencies)
# ==============================================================================

try:
    from eval_platform.eval_environment import (
        EvalEnvironment,
        DiffTracker,
        ChangeRecord,
        setup_eval
    )
except ImportError:
    # If eval_environment can't be imported, stub them out
    EvalEnvironment = None  # type: ignore
    DiffTracker = None  # type: ignore
    ChangeRecord = None  # type: ignore
    setup_eval = None  # type: ignore
