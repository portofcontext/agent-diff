"""
Tests for the new clean EvalEnvironment API.

Tests the simplified interface for AI agent evaluations.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from eval_platform.eval_utilities import EvalEnvironment


def test_eval_environment_box_basic():
    """Test basic EvalEnvironment setup for Box."""
    with EvalEnvironment("box") as env:
        # Check that environment is setup
        assert env.session is not None
        assert env.ops is not None
        assert env.default_user is not None

        # Check default user is created
        assert env.default_user.name == "Test User"
        assert env.default_user.login == "test@example.com"


def test_eval_environment_creates_folder():
    """Test that we can create a folder and it works."""
    with EvalEnvironment("box") as env:
        folder = env.ops.create_folder(
            name="Reports",
            parent_id="0",
            user_id=env.default_user.id
        )

        assert folder is not None
        assert folder.name == "Reports"
        assert folder.parent_id == "0"


def test_track_changes_basic():
    """Test that track_changes captures folder creation."""
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            folder = env.ops.create_folder(
                name="Reports",
                parent_id="0",
                user_id=env.default_user.id
            )

        # Tracker should be populated after the block
        assert tracker.created_count == 1
        assert len(tracker.created) == 1

        # Check the created record
        created_folder = tracker.created[0]
        assert created_folder.table == "box_folders"
        assert created_folder.name == "Reports"


def test_track_changes_multiple_operations():
    """Test tracking multiple operations."""
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            # Create a folder
            folder = env.ops.create_folder(
                name="Documents",
                parent_id="0",
                user_id=env.default_user.id
            )

            # Create a file
            file = env.ops.create_file(
                name="report.pdf",
                parent_id=folder.id,
                user_id=env.default_user.id
            )

        # Should have at least 2 created records (folder + file, possibly more for versions/etc)
        assert tracker.created_count >= 2

        # Check by table
        folders = tracker.get_created_by_table("box_folders")
        files = tracker.get_created_by_table("box_files")

        assert len(folders) == 1
        assert len(files) == 1

        assert folders[0].name == "Documents"
        assert files[0].name == "report.pdf"


def test_track_changes_with_update():
    """Test tracking folder updates."""
    with EvalEnvironment("box") as env:
        # Create folder first (outside tracking)
        folder = env.ops.create_folder(
            name="Q1 Reports",
            parent_id="0",
            user_id=env.default_user.id
        )

        # Track the update
        with env.track_changes() as tracker:
            updated = env.ops.update_folder(
                folder_id=folder.id,
                user_id=env.default_user.id,
                name="Q1-Q2 Reports"
            )

        # Should have 1 update
        assert tracker.updated_count == 1
        assert tracker.created_count == 0

        # Check the update
        updated_folder = tracker.updated[0]
        assert updated_folder.name == "Q1-Q2 Reports"


def test_assertion_helpers():
    """Test the assertion helper methods."""
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            folder = env.ops.create_folder(
                name="Reports",
                parent_id="0",
                user_id=env.default_user.id
            )

        # Test assertion helpers
        tracker.assert_created(1)
        tracker.assert_created(1, table="box_folders")
        tracker.assert_created_folder("Reports")

        # Test boolean helpers
        assert tracker.created_folder("Reports") is True
        assert tracker.created_folder("NonExistent") is False


def test_assertion_helpers_failure():
    """Test that assertions fail correctly."""
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            folder = env.ops.create_folder(
                name="Reports",
                parent_id="0",
                user_id=env.default_user.id
            )

        # This should raise AssertionError
        with pytest.raises(AssertionError):
            tracker.assert_created(2)  # We only created 1

        with pytest.raises(AssertionError):
            tracker.assert_created_folder("NonExistent")


def test_no_changes_tracked():
    """Test that tracker works even when no changes are made."""
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            # Don't do anything
            pass

        # Should have zero changes
        assert tracker.created_count == 0
        assert tracker.updated_count == 0
        assert tracker.deleted_count == 0


def test_calendar_service():
    """Test that EvalEnvironment works with Calendar service."""
    with EvalEnvironment("calendar") as env:
        assert env.session is not None
        assert env.ops is not None

        # Create a calendar
        calendar = env.ops.create_calendar(
            summary="Test Calendar",
            owner_id=env.default_user.user_id
        )

        assert calendar is not None
        assert calendar.summary == "Test Calendar"


def test_slack_service():
    """Test that EvalEnvironment works with Slack service."""
    with EvalEnvironment("slack") as env:
        assert env.session is not None
        assert env.ops is not None
        assert env.default_user is not None

        # Should have a default team
        assert hasattr(env.default_user, 'team_id')


def test_linear_service():
    """Test that EvalEnvironment works with Linear service."""
    with EvalEnvironment("linear") as env:
        assert env.session is not None
        assert env.ops is not None
        assert env.default_user is not None

        # Should have email
        assert env.default_user.email == "test@example.com"


def test_multiple_folders():
    """Test creating multiple folders and tracking them."""
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            folder1 = env.ops.create_folder(
                name="Folder1",
                parent_id="0",
                user_id=env.default_user.id
            )
            folder2 = env.ops.create_folder(
                name="Folder2",
                parent_id="0",
                user_id=env.default_user.id
            )
            folder3 = env.ops.create_folder(
                name="Folder3",
                parent_id=folder1.id,
                user_id=env.default_user.id
            )

        assert tracker.created_count == 3

        folders = tracker.get_created_by_table("box_folders")
        assert len(folders) == 3

        folder_names = {f.name for f in folders}
        assert folder_names == {"Folder1", "Folder2", "Folder3"}


def test_change_record_attribute_access():
    """Test that ChangeRecord allows attribute access to data."""
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            folder = env.ops.create_folder(
                name="TestFolder",
                parent_id="0",
                user_id=env.default_user.id
            )

        # Access via attribute (not dict lookup)
        created = tracker.created[0]
        assert created.name == "TestFolder"
        assert created.parent_id == "0"
        assert hasattr(created, 'folder_id')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
