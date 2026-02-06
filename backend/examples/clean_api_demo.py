"""
Demo: Clean API for AI Agent Evaluations

This example shows the new ergonomic API for testing AI agents.
It demonstrates:
1. Zero-config setup with EvalEnvironment
2. Automatic state tracking
3. Type-safe assertions
4. Clear test boundaries

Compare this to the old API which required 40+ lines of setup!
"""

from eval_platform.eval_utilities import EvalEnvironment


def test_agent_creates_folder():
    """
    Example: Testing an AI agent that creates a folder.

    This is what it SHOULD look like - clean and simple!
    """

    with EvalEnvironment("box") as env:
        # Environment is ready - root folder exists, default user created
        print(f"Default user: {env.default_user.name} ({env.default_user.login})")

        with env.track_changes() as tracker:
            # Agent does its thing (or simulate it here)
            folder = env.ops.create_folder(
                name="Reports",
                parent_id="0",
                user_id=env.default_user.user_id
            )
            print(f"Created folder: {folder.name} (ID: {folder.folder_id})")

        # Simple assertions - tracker is now populated
        print(f"\nCreated {tracker.created_count} records")

        # Assertion helpers
        tracker.assert_created(1, table="box_folders")
        tracker.assert_created_folder("Reports")

        # Or more detailed access
        assert len(tracker.created) == 1
        assert tracker.created[0].name == "Reports"
        assert tracker.created[0].table == "box_folders"

        print("✅ All assertions passed!")


def test_agent_creates_and_updates():
    """
    Example: Testing an agent that creates then updates a folder.
    """

    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            # Create folder
            folder = env.ops.create_folder(
                name="Q1 Reports",
                parent_id="0",
                user_id=env.default_user.user_id
            )

            # Update folder
            updated = env.ops.update_folder(
                folder_id=folder.folder_id,
                name="Q1-Q2 Reports"
            )

        # Check what changed
        print(f"Created: {tracker.created_count} records")
        print(f"Updated: {tracker.updated_count} records")

        # Assertions
        tracker.assert_created(1, "box_folders")
        tracker.assert_updated(1, "box_folders")

        # Access the data
        created_folder = tracker.created[0]
        print(f"Created: {created_folder.name}")

        updated_folder = tracker.updated[0]
        print(f"Updated to: {updated_folder.name}")

        print("✅ All assertions passed!")


def test_multiple_operations():
    """
    Example: Testing an agent that performs multiple operations.
    """

    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            # Create a folder
            folder = env.ops.create_folder(
                name="Documents",
                parent_id="0",
                user_id=env.default_user.user_id
            )

            # Create a file in that folder
            file = env.ops.create_file(
                name="report.pdf",
                parent_id=folder.folder_id,
                user_id=env.default_user.user_id
            )

            # Create another user
            user2 = env.ops.create_user(
                name="Jane Doe",
                login="jane@example.com",
                job_title="Manager"
            )

        # Assertions
        tracker.assert_created(3)  # Total: 1 folder + 1 file + 1 user

        # Check by table
        folders = tracker.get_created_by_table("box_folders")
        files = tracker.get_created_by_table("box_files")
        users = tracker.get_created_by_table("box_users")

        assert len(folders) == 1
        assert len(files) == 1
        assert len(users) == 1

        print(f"Created:")
        print(f"  - Folder: {folders[0].name}")
        print(f"  - File: {files[0].name}")
        print(f"  - User: {users[0].name}")

        print("✅ All assertions passed!")


def test_calendar_service():
    """
    Example: The same clean API works for all services!
    """

    with EvalEnvironment("calendar") as env:
        # Create a calendar first
        calendar = env.ops.create_calendar(
            summary="Team Calendar",
            owner_id=env.default_user.user_id
        )

        with env.track_changes() as tracker:
            # Create an event
            event = env.ops.create_event(
                calendar_id=calendar.calendar_id,
                user_id=env.default_user.user_id,
                summary="Team Meeting",
                start={"dateTime": "2024-01-15T10:00:00Z"},
                end={"dateTime": "2024-01-15T11:00:00Z"}
            )

        # Assertions
        tracker.assert_created(1, "calendar_events")
        assert tracker.created[0].summary == "Team Meeting"

        print("✅ Calendar test passed!")


def test_slack_service():
    """
    Example: Slack service with the clean API.
    """

    with EvalEnvironment("slack") as env:
        # Default team and user are already created
        print(f"Default user: {env.default_user.name}")

        # Create a channel first
        channel = env.ops.create_channel(
            name="general",
            team_id=env.default_user.team_id
        )

        with env.track_changes() as tracker:
            # Send a message
            message = env.ops.send_message(
                channel_id=channel.channel_id,
                user_id=env.default_user.user_id,
                text="Hello team!"
            )

        # Assertions
        tracker.assert_created(1, "messages")
        assert tracker.created[0].text == "Hello team!"

        print("✅ Slack test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Clean API Demo")
    print("=" * 60)

    print("\n" + "─" * 60)
    print("Test 1: Agent Creates Folder")
    print("─" * 60)
    test_agent_creates_folder()

    print("\n" + "─" * 60)
    print("Test 2: Agent Creates and Updates")
    print("─" * 60)
    test_agent_creates_and_updates()

    print("\n" + "─" * 60)
    print("Test 3: Multiple Operations")
    print("─" * 60)
    test_multiple_operations()

    print("\n" + "─" * 60)
    print("Test 4: Calendar Service")
    print("─" * 60)
    test_calendar_service()

    print("\n" + "─" * 60)
    print("Test 5: Slack Service")
    print("─" * 60)
    test_slack_service()

    print("\n" + "=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)
    print("\nLines of code comparison:")
    print("  Old API: ~40 lines of setup + test")
    print("  New API: ~10 lines total")
    print("=" * 60)
