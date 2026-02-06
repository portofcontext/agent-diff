#!/usr/bin/env python3
"""
Verification script to test that the package is properly installed.

Run this AFTER installing the package to verify imports work correctly.

Usage:
    python verify_install.py
"""

def test_imports():
    """Test that all main imports work."""
    print("Testing imports...")

    # Test new clean API
    print("  ✓ Importing EvalEnvironment...", end=" ")
    from eval_platform.eval_utilities import EvalEnvironment
    print("OK")

    print("  ✓ Importing DiffTracker...", end=" ")
    from eval_platform.eval_utilities import DiffTracker
    print("OK")

    # Test service operations
    print("  ✓ Importing BoxOperations...", end=" ")
    from services.box.database.typed_operations import BoxOperations
    print("OK")

    print("  ✓ Importing CalendarOperations...", end=" ")
    from services.calendar.database.typed_operations import CalendarOperations
    print("OK")

    print("  ✓ Importing SlackOperations...", end=" ")
    from services.slack.database.typed_operations import SlackOperations
    print("OK")

    print("  ✓ Importing LinearOperations...", end=" ")
    from services.linear.database.typed_operations import LinearOperations
    print("OK")

    # Test legacy API
    print("  ✓ Importing create_snapshot...", end=" ")
    from eval_platform.eval_utilities import create_snapshot, delete_snapshot, get_diff
    print("OK")

    print("\n✅ All imports successful!")
    print("\nNo sys.path manipulation needed - package is properly installed!")


def test_basic_functionality():
    """Test basic functionality works."""
    print("\nTesting basic functionality...")

    from eval_platform.eval_utilities import EvalEnvironment

    print("  ✓ Creating EvalEnvironment...", end=" ")
    with EvalEnvironment("box") as env:
        print("OK")

        print("  ✓ Checking default user exists...", end=" ")
        assert env.default_user is not None
        assert env.default_user.name == "Test User"
        print("OK")

        print("  ✓ Creating a folder...", end=" ")
        folder = env.ops.create_folder(
            name="Test Folder",
            parent_id="0",
            user_id=env.default_user.id
        )
        assert folder.name == "Test Folder"
        print("OK")

        print("  ✓ Tracking changes...", end=" ")
        with env.track_changes() as tracker:
            folder2 = env.ops.create_folder(
                name="Test Folder 2",
                parent_id="0",
                user_id=env.default_user.id
            )

        assert tracker.created_count == 1
        assert tracker.created[0].name == "Test Folder 2"
        print("OK")

    print("\n✅ All functionality tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Diff-the-Universe Package Verification")
    print("=" * 60)
    print()

    try:
        test_imports()
        test_basic_functionality()

        print("\n" + "=" * 60)
        print("✅ VERIFICATION SUCCESSFUL")
        print("=" * 60)
        print("\nThe package is properly installed and ready to use!")
        print("\nYou can now import directly without sys.path hacks:")
        print("  from eval_platform.eval_utilities import EvalEnvironment")

    except ImportError as e:
        print("\n" + "=" * 60)
        print("❌ VERIFICATION FAILED")
        print("=" * 60)
        print(f"\nImport error: {e}")
        print("\nPlease reinstall the package:")
        print("  uv pip uninstall diff-the-universe")
        print("  uv pip install git+https://github.com/portofcontext/agent-diff.git#subdirectory=backend")
        exit(1)

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ VERIFICATION FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
