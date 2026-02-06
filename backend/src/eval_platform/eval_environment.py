"""
Clean, ergonomic API for AI agent evaluations.

This module provides a simplified interface for testing AI agents that:
- Starts from a known state
- Tracks changes automatically
- Makes assertions easy

Example:
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            folder = env.ops.create_folder(
                name="Reports",
                parent_id="0",
                user_id=env.default_user.id
            )

        # Assert changes
        tracker.assert_created(count=1, table="box_folders")
        assert tracker.created_folder("Reports")
"""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Type

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from eval_platform.eval_utilities import create_snapshot, delete_snapshot
from eval_platform.evaluationEngine.models import DiffResult
from services.box.database.schema import Base as BoxBase

# Import service operations
from services.box.database.typed_operations import BoxOperations
from services.calendar.database.schema import Base as CalendarBase
from services.calendar.database.typed_operations import CalendarOperations
from services.linear.database.schema import Base as LinearBase
from services.linear.database.typed_operations import LinearOperations
from services.slack.database.schema import Base as SlackBase
from services.slack.database.typed_operations import SlackOperations

ServiceType = Literal["box", "calendar", "slack", "linear"]


@dataclass
class ChangeRecord:
    """Typed record of a database change."""

    table: str
    data: Dict[str, Any]

    def __getattr__(self, name: str) -> Any:
        """Allow accessing data fields as attributes."""
        if name in ("table", "data"):
            return object.__getattribute__(self, name)
        return self.data.get(name)


class DiffTracker:
    """
    Tracks database changes with type-safe access and assertion helpers.

    Example:
        tracker.assert_created(count=1, table="box_folders")
        assert tracker.created_folder("Reports")
        assert len(tracker.created) == 1
    """

    def __init__(self, diff: DiffResult):
        self._diff = diff
        self._created = [
            ChangeRecord(table=r["__table__"], data=r) for r in diff.inserts
        ]
        self._updated = [
            ChangeRecord(table=r["__table__"], data=r["after"]) for r in diff.updates
        ]
        self._deleted = [
            ChangeRecord(table=r["__table__"], data=r) for r in diff.deletes
        ]

    @property
    def created(self) -> List[ChangeRecord]:
        """List of created records."""
        return self._created

    @property
    def updated(self) -> List[ChangeRecord]:
        """List of updated records."""
        return self._updated

    @property
    def deleted(self) -> List[ChangeRecord]:
        """List of deleted records."""
        return self._deleted

    @property
    def created_count(self) -> int:
        """Number of records created."""
        return len(self._created)

    @property
    def updated_count(self) -> int:
        """Number of records updated."""
        return len(self._updated)

    @property
    def deleted_count(self) -> int:
        """Number of records deleted."""
        return len(self._deleted)

    def assert_created(self, count: int, table: Optional[str] = None) -> None:
        """
        Assert the number of created records.

        Args:
            count: Expected number of created records
            table: Optional table name to filter by
        """
        if table:
            actual = len([r for r in self._created if r.table == table])
            assert actual == count, f"Expected {count} inserts in {table}, got {actual}"
        else:
            assert len(self._created) == count, (
                f"Expected {count} inserts, got {len(self._created)}"
            )

    def assert_updated(self, count: int, table: Optional[str] = None) -> None:
        """Assert the number of updated records."""
        if table:
            actual = len([r for r in self._updated if r.table == table])
            assert actual == count, f"Expected {count} updates in {table}, got {actual}"
        else:
            assert len(self._updated) == count, (
                f"Expected {count} updates, got {len(self._updated)}"
            )

    def assert_deleted(self, count: int, table: Optional[str] = None) -> None:
        """Assert the number of deleted records."""
        if table:
            actual = len([r for r in self._deleted if r.table == table])
            assert actual == count, f"Expected {count} deletes in {table}, got {actual}"
        else:
            assert len(self._deleted) == count, (
                f"Expected {count} deletes, got {len(self._deleted)}"
            )

    def created_folder(self, name: str) -> bool:
        """Check if a folder with the given name was created."""
        return any(
            r.table == "box_folders" and r.data.get("name") == name
            for r in self._created
        )

    def assert_created_folder(self, name: str) -> None:
        """Assert that a folder with the given name was created."""
        assert self.created_folder(name), f"Expected folder '{name}' to be created"

    def created_file(self, name: str) -> bool:
        """Check if a file with the given name was created."""
        return any(
            r.table == "box_files" and r.data.get("name") == name for r in self._created
        )

    def assert_created_file(self, name: str) -> None:
        """Assert that a file with the given name was created."""
        assert self.created_file(name), f"Expected file '{name}' to be created"

    def get_created_by_table(self, table: str) -> List[ChangeRecord]:
        """Get all created records for a specific table."""
        return [r for r in self._created if r.table == table]

    def get_updated_by_table(self, table: str) -> List[ChangeRecord]:
        """Get all updated records for a specific table."""
        return [r for r in self._updated if r.table == table]

    def get_deleted_by_table(self, table: str) -> List[ChangeRecord]:
        """Get all deleted records for a specific table."""
        return [r for r in self._deleted if r.table == table]


class EvalEnvironment:
    """
    One-liner setup for AI agent evaluation environments.

    Provides:
    - Automatic database setup
    - Pre-seeded test data (users, root folders, etc.)
    - Typed operations for the service
    - Automatic state tracking

    Example:
        with EvalEnvironment("box") as env:
            # Environment ready, root folder exists
            with env.track_changes() as tracker:
                folder = env.ops.create_folder(
                    name="Reports",
                    parent_id="0",
                    user_id=env.default_user.id
                )

            # Assert changes
            tracker.assert_created(1, "box_folders")
    """

    def __init__(
        self,
        service: ServiceType,
        *,
        database_url: Optional[str] = None,
        seed_users: int = 1,
        cleanup: bool = True,
    ):
        """
        Initialize an evaluation environment.

        Args:
            service: Service type ("box", "calendar", "slack", "linear")
            database_url: Optional database URL (creates temp SQLite if not provided)
            seed_users: Number of default users to create (default: 1)
            cleanup: Whether to cleanup database on exit (default: True)
        """
        self.service = service
        self.seed_users = seed_users
        self.cleanup = cleanup

        # Setup database
        if database_url:
            self.database_url = database_url
            self._temp_db = None
        else:
            # Create temporary SQLite database
            self._temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            self.database_url = f"sqlite:///{self._temp_db.name}"

        self.engine: Optional[Engine] = None
        self.session: Optional[Session] = None
        self.ops: Optional[Any] = None
        self.default_user: Optional[Any] = None
        self._session_factory: Optional[sessionmaker] = None

    def __enter__(self) -> EvalEnvironment:
        """Setup the environment."""
        # Create engine and session
        self.engine = create_engine(self.database_url, echo=False)
        self._session_factory = sessionmaker(bind=self.engine)
        self.session = self._session_factory()

        # Create tables based on service
        base_class = self._get_base_class()
        base_class.metadata.create_all(self.engine)

        # Setup operations
        ops_class = self._get_operations_class()
        self.ops = ops_class(self.session)

        # Seed default data
        self._seed_defaults()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup the environment."""
        if self.session:
            self.session.close()

        if self.cleanup and self._temp_db:
            # Close and delete temp database
            self._temp_db.close()
            Path(self._temp_db.name).unlink(missing_ok=True)

    @contextmanager
    def track_changes(self):
        """
        Context manager for tracking database changes.

        The tracker is populated after the context exits, so access it
        after the with block.

        Usage:
            with env.track_changes() as tracker:
                # Perform operations
                env.ops.create_folder(...)

            # Check what changed (tracker is now populated)
            tracker.assert_created(1, "box_folders")
        """
        # Create before snapshot
        create_snapshot(self.session, "main", "before")

        # Create a mutable container that will hold the tracker
        class TrackerContainer:
            def __init__(self):
                self._tracker: Optional[DiffTracker] = None

            def __getattr__(self, name: str):
                if self._tracker is None:
                    raise RuntimeError(
                        "Tracker not yet available. Access it after the 'with' block exits."
                    )
                return getattr(self._tracker, name)

            def _set_tracker(self, tracker: DiffTracker):
                self._tracker = tracker

        container = TrackerContainer()

        try:
            yield container
        finally:
            # Create after snapshot
            create_snapshot(self.session, "main", "after")

            # Get diff - use simplified diff for SQLite
            diff = self._get_simple_diff("before", "after")

            # Cleanup snapshots
            delete_snapshot(self.session, "main", "before")
            delete_snapshot(self.session, "main", "after")

            # Populate the container with the tracker
            container._set_tracker(DiffTracker(diff))

    def _get_base_class(self) -> Type:
        """Get the SQLAlchemy Base class for the service."""
        if self.service == "box":
            return BoxBase
        elif self.service == "calendar":
            return CalendarBase
        elif self.service == "slack":
            return SlackBase
        elif self.service == "linear":
            return LinearBase
        else:
            raise ValueError(f"Unknown service: {self.service}")

    def _get_operations_class(self) -> Type:
        """Get the operations class for the service."""
        if self.service == "box":
            return BoxOperations
        elif self.service == "calendar":
            return CalendarOperations
        elif self.service == "slack":
            return SlackOperations
        elif self.service == "linear":
            return LinearOperations
        else:
            raise ValueError(f"Unknown service: {self.service}")

    def _seed_defaults(self) -> None:
        """Seed default data based on service type."""
        if self.service == "box":
            self._seed_box_defaults()
        elif self.service == "calendar":
            self._seed_calendar_defaults()
        elif self.service == "slack":
            self._seed_slack_defaults()
        elif self.service == "linear":
            self._seed_linear_defaults()

    def _seed_box_defaults(self) -> None:
        """Seed default Box data."""
        # Create default user
        if self.seed_users >= 1:
            self.default_user = self.ops.create_user(
                name="Test User", login="test@example.com", job_title="Tester"
            )

        # Create root folder (special case for Box)
        # Use raw SQL to avoid field validation issues
        from sqlalchemy import text

        self.session.execute(
            text("""
            INSERT INTO box_folders (id, type, name, parent_id, item_status, size)
            VALUES ('0', 'folder', 'All Files', '0', 'active', 0)
        """)
        )
        self.session.commit()

    def _seed_calendar_defaults(self) -> None:
        """Seed default Calendar data."""
        if self.seed_users >= 1:
            # Calendar operations have create_user if needed
            # For now, store in a simple way
            self.default_user = type(
                "User", (), {"user_id": "default-user", "email": "test@example.com"}
            )()

    def _seed_slack_defaults(self) -> None:
        """Seed default Slack data."""
        if self.seed_users >= 1:
            # Create default team first
            self.ops.create_team(team_name="Test Team")

            # Create default user
            self.default_user = self.ops.create_user(
                user_id="U001",
                username="Test-User",
                real_name="Test User",
                email="test@example.com",
            )

    def _seed_linear_defaults(self) -> None:
        """Seed default Linear data."""
        if self.seed_users >= 1:
            # Create organization first
            org = self.ops.create_organization(name="Test Org")

            # Create default user
            self.default_user = self.ops.create_user(
                email="test@example.com", name="Test User", organizationId=org.id
            )

    def _get_simple_diff(self, before_suffix: str, after_suffix: str) -> DiffResult:
        """
        Simple diff implementation for SQLite that doesn't require SessionManager.

        Args:
            before_suffix: Suffix of before snapshot
            after_suffix: Suffix of after snapshot

        Returns:
            DiffResult with inserts, updates, and deletes
        """
        # Get all tables
        result = self.session.execute(
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

            # Check if snapshot tables exist
            check_result = self.session.execute(
                text(f"""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name IN ('{before_table}', '{after_table}')
            """)
            )
            existing_tables = [row[0] for row in check_result]

            if (
                before_table not in existing_tables
                or after_table not in existing_tables
            ):
                continue

            # Get primary key column (assume 'id' for simplicity)
            pk_col = "id"

            # Find inserts (rows in after but not in before)
            insert_query = text(f"""
                SELECT * FROM "{after_table}"
                WHERE {pk_col} NOT IN (SELECT {pk_col} FROM "{before_table}")
            """)
            insert_results = self.session.execute(insert_query)
            columns = list(insert_results.keys())
            for row in insert_results:
                row_dict = dict(zip(columns, row))
                row_dict["__table__"] = table
                inserts.append(row_dict)

            # Find deletes (rows in before but not in after)
            delete_query = text(f"""
                SELECT * FROM "{before_table}"
                WHERE {pk_col} NOT IN (SELECT {pk_col} FROM "{after_table}")
            """)
            delete_results = self.session.execute(delete_query)
            columns = list(delete_results.keys())
            for row in delete_results:
                row_dict = dict(zip(columns, row))
                row_dict["__table__"] = table
                deletes.append(row_dict)

            # Find updates (rows with same ID but different values)
            # For simplicity, compare all columns as JSON
            update_query = text(f"""
                SELECT a.*, b.*
                FROM "{after_table}" a
                JOIN "{before_table}" b ON a.{pk_col} = b.{pk_col}
            """)
            try:
                update_results = self.session.execute(update_query)
                columns = list(update_results.keys())
                half = len(columns) // 2
                after_cols = columns[:half]
                before_cols = columns[half:]

                for row in update_results:
                    after_dict = dict(zip(after_cols, row[:half]))
                    before_dict = dict(zip(before_cols, row[half:]))

                    # Check if anything changed (ignoring __table__)
                    if after_dict != before_dict:
                        after_dict["__table__"] = table
                        before_dict["__table__"] = table
                        updates.append(
                            {
                                "__table__": table,
                                "after": after_dict,
                                "before": before_dict,
                            }
                        )
            except Exception:
                # Skip updates if there's an issue with the query
                pass

        return DiffResult(inserts=inserts, updates=updates, deletes=deletes)


# Convenience function for quick setup
def setup_eval(service: ServiceType, **kwargs) -> EvalEnvironment:
    """
    Quick setup function for evaluations.

    Usage:
        env = setup_eval("box")
        folder = env.ops.create_folder(...)
    """
    env = EvalEnvironment(service, **kwargs)
    env.__enter__()
    return env
