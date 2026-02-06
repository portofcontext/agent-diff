# Diff the Universe

**Typed database operations and state tracking for building AI agent evaluation frameworks.**

This package provides typed CRUD operations for Box, Google Calendar, Slack, and Linear that work as AI agent tools, along with utilities for capturing and diffing state changes during agent execution.

## Installation

Install directly from GitHub using uv:

```bash
uv pip install git+https://github.com/portofcontext/agent-diff.git#subdirectory=backend
```

Or add to your project's `pyproject.toml`:

```toml
[project]
dependencies = [
    "diff-the-universe @ git+https://github.com/portofcontext/agent-diff.git#subdirectory=backend"
]
```

## Quick Start

### New Clean API (Recommended)

```python
from eval_platform.eval_utilities import EvalEnvironment

# One-liner setup - everything handled automatically!
with EvalEnvironment("box") as env:
    with env.track_changes() as tracker:
        # Agent does its thing
        folder = env.ops.create_folder(
            name="Reports",
            parent_id="0",
            user_id=env.default_user.user_id
        )

    # Simple, type-safe assertions
    tracker.assert_created(1, table="box_folders")
    assert tracker.created_folder("Reports")
    assert tracker.created[0].name == "Reports"
```

**Lines of code:** ~10 lines vs ~40 lines with the old API

**Key Benefits:**
- ✅ Zero-config defaults - Works out of the box
- ✅ Automatic state tracking - No manual snapshots needed
- ✅ Type-safe results - No dict lookups, use proper objects
- ✅ Clear boundaries - Setup vs test vs verification are explicit
- ✅ Ergonomic assertions - One-liners for common checks
- ✅ Service consistency - Same API across Box/Calendar/Slack/Linear

### Legacy API (Still Supported)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.box.database.typed_operations import BoxOperations
from eval_platform.eval_utilities import EvalContext

# Setup database
engine = create_engine("sqlite:///test.db")
session = sessionmaker(bind=engine)()

# Use typed operations as AI agent tools
ops = BoxOperations(session)

# Track state changes automatically
with EvalContext(session, "test_env") as ctx:
    # Agent actions
    user = ops.create_user(
        name="John Doe",
        login="john@example.com",
        job_title="Engineer"
    )
    folder = ops.create_folder(
        name="Reports",
        parent_id="0",
        user_id=user.user_id
    )

    # Automatic diff tracking
    assert len(ctx.inserts) == 2  # User and folder created
    assert ctx.inserts[0]['__table__'] == 'box_users'
    assert ctx.inserts[1]['__table__'] == 'box_folders'
```

## New Clean API Features

### EvalEnvironment - One-Liner Setup

The `EvalEnvironment` class provides automatic setup and cleanup:

```python
with EvalEnvironment("box") as env:
    # Everything is ready:
    # ✅ Database created (temp SQLite by default)
    # ✅ Tables created
    # ✅ Root folder exists (for Box)
    # ✅ Default user created
    # ✅ Operations class initialized

    folder = env.ops.create_folder(
        name="Reports",
        parent_id="0",
        user_id=env.default_user.user_id
    )
```

**Automatic cleanup:** Database is automatically cleaned up when the context exits.

### DiffTracker - Type-Safe Change Tracking

Track changes with type-safe access and assertion helpers:

```python
with env.track_changes() as tracker:
    # Perform operations
    folder = env.ops.create_folder(name="Reports", ...)

# Tracker is populated after the block exits
print(f"Created {tracker.created_count} records")

# Assertion helpers
tracker.assert_created(1, table="box_folders")
tracker.assert_created_folder("Reports")

# Type-safe access (no dict lookups!)
assert tracker.created[0].name == "Reports"
assert tracker.created[0].table == "box_folders"

# Access data as attributes
folder_name = tracker.created[0].name  # Not tracker.created[0]['name']!
```

### Service-Agnostic API

Works the same way for all services:

```python
# Box
with EvalEnvironment("box") as env:
    with env.track_changes() as tracker:
        folder = env.ops.create_folder(...)

# Calendar
with EvalEnvironment("calendar") as env:
    with env.track_changes() as tracker:
        event = env.ops.create_event(...)

# Slack
with EvalEnvironment("slack") as env:
    with env.track_changes() as tracker:
        message = env.ops.send_message(...)

# Linear
with EvalEnvironment("linear") as env:
    with env.track_changes() as tracker:
        issue = env.ops.create_issue(...)
```

### Assertion Helpers

Built-in assertion methods for common checks:

```python
# Count assertions
tracker.assert_created(count=1, table="box_folders")
tracker.assert_updated(count=2)
tracker.assert_deleted(count=0)

# Specific entity assertions
tracker.assert_created_folder("Reports")
tracker.assert_created_file("document.pdf")

# Custom checks
assert tracker.created_folder("Reports")  # Returns bool
assert tracker.created_file("document.pdf")

# Get by table
folders = tracker.get_created_by_table("box_folders")
files = tracker.get_created_by_table("box_files")
```

### Pre-Seeded Test Data

Default user and root entities are created automatically:

```python
with EvalEnvironment("box") as env:
    # env.default_user is already created
    print(env.default_user.name)  # "Test User"
    print(env.default_user.login)  # "test@example.com"

    # Root folder (ID "0") already exists
    folder = env.ops.create_folder(
        name="Reports",
        parent_id="0",  # Root folder
        user_id=env.default_user.user_id
    )
```

## Available Operations

### Box Operations

```python
from services.box.database.typed_operations import BoxOperations

ops = BoxOperations(session)

# User operations
user = ops.create_user(name="Alice", login="alice@example.com", job_title="PM")
user = ops.get_user(user_id)

# Folder operations
folder = ops.create_folder(name="Q1 Reports", parent_id="0", user_id=user.user_id)
folder = ops.update_folder(folder_id, name="Q1-Q2 Reports")
ops.delete_folder(folder_id)

# File operations
file = ops.create_file(name="report.pdf", parent_id=folder.folder_id, user_id=user.user_id)
```

### Google Calendar Operations

```python
from services.calendar.database.typed_operations import CalendarOperations

ops = CalendarOperations(session)

# Calendar operations
calendar = ops.create_calendar(
    summary="Team Calendar",
    owner_id=user.user_id
)

# Event operations (require user_id for permissions)
event = ops.create_event(
    calendar_id=calendar.calendar_id,
    user_id=user.user_id,
    summary="Team Meeting",
    start={"dateTime": "2024-01-15T10:00:00Z"},
    end={"dateTime": "2024-01-15T11:00:00Z"}
)
events = ops.list_events(calendar_id, user_id)
ops.update_event(event_id, user_id, summary="Team Standup")
```

### Slack Operations

```python
from services.slack.database.typed_operations import SlackOperations

ops = SlackOperations(session)

# Team and channel operations
team = ops.create_team(name="Engineering", domain="eng")
channel = ops.create_channel(name="general", team_id=team.team_id)

# Message operations
message = ops.send_message(
    channel_id=channel.channel_id,
    user_id=user.user_id,
    text="Hello team!"
)
ops.add_emoji_reaction(message_id=message.message_id, name="thumbsup", user_id=user.user_id)
```

### Linear Operations

Linear provides **80+ operations** across 14 entity types with an entity defaults pattern to handle the complex auto-generated schema:

```python
from services.linear.database.typed_operations import LinearOperations

ops = LinearOperations(session)

# Organization (102 required fields handled automatically)
org = ops.create_organization(name="Acme Inc")

# Users and teams
user = ops.create_user(email="alice@acme.com", name="Alice Smith", organizationId=org.id)
team = ops.create_team(name="Engineering", key="ENG", organization_id=org.id)

# Workflow states
todo = ops.create_workflow_state(name="Todo", team_id=team.id, type="unstarted")
in_progress = ops.create_workflow_state(name="In Progress", team_id=team.id, type="started")

# Issues
issue = ops.create_issue(
    team_id=team.id,
    title="Implement authentication",
    description="Add OAuth2 flow",
    state_id=todo.id,
    assignee_id=user.id
)
ops.update_issue(issue.id, state_id=in_progress.id)

# Comments, projects, cycles, initiatives, documents, attachments, labels, relations...
# See LINEAR_CRUD_SUMMARY.md for all 80+ operations
```

## AI Agent Tool Integration

All operations are designed for use as AI agent tools with:

- **Clear type hints** - `Optional` returns, typed parameters
- **Comprehensive docstrings** - Parameter descriptions and examples
- **Pydantic serialization** - `.model_dump()` and `.model_dump_json()` on all models
- **Session management** - Encapsulated in operation classes

### Example: Anthropic Claude Tool

```python
tools = [
    {
        "name": "create_folder",
        "description": "Create a new folder in Box",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Folder name"},
                "parent_id": {"type": "string", "description": "Parent folder ID"},
                "user_id": {"type": "string", "description": "Owner user ID"}
            },
            "required": ["name", "parent_id", "user_id"]
        }
    }
]

def execute_tool(tool_name, arguments):
    ops = BoxOperations(session)

    if tool_name == "create_folder":
        folder = ops.create_folder(**arguments)
        return folder.model_dump()  # Serialize for agent
```

## State Management for Evaluations

Track agent actions using snapshots and diffs:

### Using EvalContext (Recommended)

```python
from eval_platform.eval_utilities import EvalContext

with EvalContext(session, "test_env") as ctx:
    # Agent executes operations
    ops = SlackOperations(session)
    message = ops.send_message(
        channel_id=channel_id,
        user_id=user_id,
        text="Hello world"
    )

    # Automatic diff tracking
    assert len(ctx.inserts) == 1
    assert ctx.inserts[0]['message_text'] == 'Hello world'
    assert ctx.inserts[0]['__table__'] == 'messages'

# Snapshots automatically cleaned up
```

### Manual Snapshots

```python
from eval_platform.eval_utilities import create_snapshot, get_diff

# Before agent runs
create_snapshot(session, "test_env", "before")

# Agent executes actions...
ops = BoxOperations(session)
folder = ops.create_folder(name="Reports", parent_id="0", user_id=user_id)

# After agent runs
create_snapshot(session, "test_env", "after")

# Get diff
diff = get_diff(session_manager, "test_env", "before", "after")

print(f"Inserts: {len(diff.inserts)}")  # New rows
print(f"Updates: {len(diff.updates)}")  # Modified rows
print(f"Deletes: {len(diff.deletes)}")  # Deleted rows

# Each change includes __table__ to identify origin
for insert in diff.inserts:
    print(f"Created {insert['__table__']}: {insert['name']}")
```

### Clearing State Between Tests

```python
from eval_platform.eval_utilities import clear_environment

# Clear all data (keeps schema structure)
clear_environment(session, "test_env")
```

## Database Compatibility

All services support both PostgreSQL and SQLite:

- **PostgreSQL** - Production use with full schema isolation
- **SQLite** - Fast, isolated testing and development

```python
# PostgreSQL
engine = create_engine("postgresql://user:pass@localhost/dbname")

# SQLite
engine = create_engine("sqlite:///test.db")
```

## Running Tests

```bash
cd backend
DATABASE_URL=sqlite:///dummy.db PYTHONPATH=src uv run pytest tests/test_sqlite_integration.py tests/test_calendar_sqlite_integration.py tests/test_slack_sqlite_integration.py -v
```


## Documentation

- **[AI_AGENT_INTEGRATION.md](backend/AI_AGENT_INTEGRATION.md)** - Complete integration guide
- **[LINEAR_CRUD_SUMMARY.md](backend/LINEAR_CRUD_SUMMARY.md)** - Linear operations details
- **[entity_defaults.py](backend/src/services/linear/database/entity_defaults.py)** - Entity defaults pattern
- **[linear_crud_demo.py](backend/examples/linear_crud_demo.py)** - Usage demonstration

## Architecture

**Service Structure:**
- `services/{service}/database/schema.py` - SQLAlchemy models with Pydantic serialization
- `services/{service}/database/typed_operations.py` - Typed CRUD operations
- `services/{service}/database/entity_defaults.py` - Default value factories (Linear only)

**Eval Platform:**
- `eval_platform/eval_utilities.py` - Snapshot and diff utilities
- Supports both PostgreSQL and SQLite
- Schema isolation for parallel testing

