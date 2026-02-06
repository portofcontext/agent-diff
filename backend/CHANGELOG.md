# Changelog

## [Unreleased]

### Fixed

#### Import Issues (Breaking when installed as package)

**Problem:** All imports used `from src.` prefix, which broke when the package was installed via pip/uv.

**Solution:** Fixed 22 files by removing `src.` prefix:
- `from src.eval_platform.isolationEngine.session import SessionManager`
- → `from eval_platform.isolationEngine.session import SessionManager`

Files fixed:
- All `eval_platform/` modules
- All `services/` modules
- API, database migrations, and test manager modules

### Added

#### New Clean API for AI Agent Evaluations

**Problem:** Consumers reported the old API required:
- 40+ lines of boilerplate setup
- Manual database management
- Complex snapshot/diff management
- Dict-based results requiring string lookups
- No built-in assertions

**Solution:** Implemented `EvalEnvironment` and `DiffTracker` classes providing:

##### 1. One-Liner Environment Setup

```python
# Old way (40+ lines):
db_fd, db_path = tempfile.mkstemp(suffix=".db")
database_url = f"sqlite:///{db_path}"
engine = create_engine(database_url, echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
ops = BoxOperations(session)
# + manual root folder creation!

# New way (1 line):
with EvalEnvironment("box") as env:
    # Ready to go!
```

##### 2. Automatic State Tracking

```python
# Old way:
create_snapshot(session, "test_env", "before")
# ... do stuff ...
create_snapshot(session, "test_env", "after")
inserts = simple_diff(session, "before", "after")

# New way:
with env.track_changes() as tracker:
    # Any operations here are automatically tracked
    folder = env.ops.create_folder(...)

# Diff is automatically captured
assert tracker.created_count == 1
```

##### 3. Pre-Seeded Test Data

```python
# Old way:
user = ops.create_user(...)
root = Folder(id="0", parent_id="0", ...)  # Special case!
session.add(root)
session.commit()

# New way:
env.default_user  # Already exists
# Root folder already exists by default
```

##### 4. Assertion Helpers

```python
# Old way:
inserts = simple_diff(session, "before", "after")
assert len(inserts) == 1
assert inserts[0]['__table__'] == 'box_folders'
assert inserts[0]['name'] == 'Reports'

# New way:
tracker.assert_created(count=1, table="box_folders")
tracker.assert_created_folder("Reports")

# Or even simpler:
assert tracker.created_folder("Reports")
```

##### 5. Service-Agnostic API

Works the same for Box, Calendar, Slack, and Linear:

```python
with EvalEnvironment("calendar") as env:
    with env.track_changes() as tracker:
        event = env.ops.create_event(...)

with EvalEnvironment("slack") as env:
    with env.track_changes() as tracker:
        message = env.ops.send_message(...)
```

##### 6. Typed Results (No Dict Lookups!)

```python
# Old way:
inserts[0]['__table__']  # string lookup
inserts[0]['name']       # string lookup

# New way:
tracker.created[0].table  # typed attribute
tracker.created[0].name   # typed attribute
```

##### 7. Clear Separation of Setup vs Test

```python
# Old way: Setup mixed with test
ops = BoxOperations(session)
user = ops.create_user(...)
root = Folder(...)  # Setup
create_snapshot(...)  # Test boundary
folder = ops.create_folder(...)  # Test action

# New way: Clear phases
with EvalEnvironment("box") as env:  # Setup automatic
    with env.track_changes() as tracker:  # Test boundary
        folder = env.ops.create_folder(...)  # Test action

    # Verification
    tracker.assert_created(1)
```

#### Code Reduction

- **Old API:** ~40 lines of setup + test
- **New API:** ~10 lines total

#### New Modules

- `eval_platform/eval_environment.py` - New `EvalEnvironment` and `DiffTracker` classes
- `examples/clean_api_demo.py` - Complete demonstration of new API
- `CHANGELOG.md` - This file

#### Updated Documentation

- `README.md` - Added "New Clean API" section at the top
- Updated Quick Start to showcase new API first
- Added detailed feature documentation
- Kept legacy API documentation for backward compatibility

### Backward Compatibility

All existing APIs remain functional:
- `create_snapshot()`, `get_diff()`, `EvalContext` still work
- No breaking changes to existing code
- New API is opt-in via `EvalEnvironment`

### Example Usage

See [examples/clean_api_demo.py](examples/clean_api_demo.py) for complete examples.

**Basic usage:**

```python
from eval_platform.eval_utilities import EvalEnvironment

def test_agent_creates_folder():
    with EvalEnvironment("box") as env:
        with env.track_changes() as tracker:
            folder = env.ops.create_folder(
                name="Reports",
                parent_id="0",
                user_id=env.default_user.user_id
            )

        tracker.assert_created(1, table="box_folders")
        assert tracker.created_folder("Reports")
```

### Migration Guide

To migrate from old API to new API:

**Before:**
```python
# Setup
db_fd, db_path = tempfile.mkstemp(suffix=".db")
database_url = f"sqlite:///{db_path}"
engine = create_engine(database_url, echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
ops = BoxOperations(session)

# Seed
user = ops.create_user(name="Test", login="test@example.com", job_title="Tester")
root = Folder(id="0", parent_id="0", name="All Files", created_by="system", modified_by="system")
session.add(root)
session.commit()

# Test
create_snapshot(session, "main", "before")
folder = ops.create_folder(name="Reports", parent_id="0", user_id=user.user_id)
create_snapshot(session, "main", "after")

# Assert
inserts = simple_diff(session, "before", "after")
assert len(inserts) == 1
assert inserts[0]['name'] == 'Reports'
```

**After:**
```python
with EvalEnvironment("box") as env:
    with env.track_changes() as tracker:
        folder = env.ops.create_folder(
            name="Reports",
            parent_id="0",
            user_id=env.default_user.user_id
        )

    tracker.assert_created_folder("Reports")
```

## Previous Versions

No previous releases documented.
