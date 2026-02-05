"""
Demonstration of comprehensive Linear CRUD operations.

This script shows how to use the LinearOperations class with all major entities
as AI agent tools.
"""

import tempfile
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Linear schema and operations
from services.linear.database.schema import Base
from services.linear.database.typed_operations import LinearOperations


def main():
    # Create temporary SQLite database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Initialize LinearOperations
    ops = LinearOperations(session)

    print("=" * 60)
    print("Linear CRUD Operations Demo")
    print("=" * 60)

    # 1. Organization Operations
    print("\n1. Creating Organization...")
    org = ops.create_organization(
        name="Acme Inc",
        url_key="acme"
    )
    print(f"   ✓ Created organization: {org.name} (ID: {org.id})")
    print(f"   ✓ Organization has sensible defaults for {len([k for k in vars(org) if not k.startswith('_')])} fields")

    # 2. User Operations
    print("\n2. Creating Users...")
    alice = ops.create_user(
        email="alice@acme.com",
        name="Alice Smith",
        display_name="Alice",
        admin=True,
        organizationId=org.id
    )
    bob = ops.create_user(
        email="bob@acme.com",
        name="Bob Jones",
        display_name="Bob",
        organizationId=org.id
    )
    print(f"   ✓ Created users: {alice.name}, {bob.name}")

    # 3. Team Operations
    print("\n3. Creating Teams...")
    eng_team = ops.create_team(
        name="Engineering",
        key="ENG",
        organization_id=org.id,
        description="Engineering team"
    )
    design_team = ops.create_team(
        name="Design",
        key="DES",
        organization_id=org.id
    )
    print(f"   ✓ Created teams: {eng_team.name} ({eng_team.key}), {design_team.name} ({design_team.key})")

    # 4. Workflow State Operations
    print("\n4. Creating Workflow States...")
    todo = ops.create_workflow_state(
        name="Todo",
        team_id=eng_team.id,
        type="unstarted",
        color="#95a2b3"
    )
    in_progress = ops.create_workflow_state(
        name="In Progress",
        team_id=eng_team.id,
        type="started",
        color="#f2c94c"
    )
    done = ops.create_workflow_state(
        name="Done",
        team_id=eng_team.id,
        type="completed",
        color="#5e6ad2"
    )
    print(f"   ✓ Created workflow states: {todo.name}, {in_progress.name}, {done.name}")

    # 5. Issue Operations
    print("\n5. Creating Issues...")
    issue1 = ops.create_issue(
        team_id=eng_team.id,
        title="Implement user authentication",
        description="Add OAuth2 authentication flow",
        priority=2,
        state_id=todo.id,
        assignee_id=alice.id,
        creator_id=alice.id
    )
    issue2 = ops.create_issue(
        team_id=eng_team.id,
        title="Fix login bug",
        description="Users cannot log in with email",
        priority=3,
        state_id=in_progress.id,
        assignee_id=bob.id
    )
    print(f"   ✓ Created issues: ENG-1 '{issue1.title}', ENG-2 '{issue2.title}'")

    # 6. Update Issue
    print("\n6. Updating Issue...")
    updated_issue = ops.update_issue(
        issue_id=issue1.id,
        state_id=in_progress.id,
        description="Add OAuth2 authentication flow with Google and GitHub providers"
    )
    print(f"   ✓ Updated issue state to: {in_progress.name}")

    # 7. Comment Operations
    print("\n7. Creating Comments...")
    comment1 = ops.create_comment(
        issue_id=issue1.id,
        body="Started working on OAuth2 integration",
        user_id=alice.id
    )
    comment2 = ops.create_comment(
        issue_id=issue1.id,
        body="Google provider is ready for review",
        user_id=alice.id
    )
    print(f"   ✓ Created {2} comments on issue")

    # 8. Project Operations
    print("\n8. Creating Project...")
    project = ops.create_project(
        name="Q1 2024 Goals",
        description="Authentication and security improvements",
        lead_id=alice.id,
        target_date=datetime.now() + timedelta(days=90)
    )
    print(f"   ✓ Created project: {project.name}")

    # 9. Project Milestone Operations
    print("\n9. Creating Project Milestones...")
    milestone1 = ops.create_project_milestone(
        name="OAuth Implementation",
        project_id=project.id,
        target_date=datetime.now() + timedelta(days=30)
    )
    milestone2 = ops.create_project_milestone(
        name="Security Audit",
        project_id=project.id,
        target_date=datetime.now() + timedelta(days=60)
    )
    print(f"   ✓ Created milestones: {milestone1.name}, {milestone2.name}")

    # 10. Cycle Operations
    print("\n10. Creating Cycle...")
    cycle = ops.create_cycle(
        team_id=eng_team.id,
        number=1,
        starts_at=datetime.now(),
        ends_at=datetime.now() + timedelta(days=14),
        name="Sprint 1"
    )
    print(f"   ✓ Created cycle: {cycle.name}")

    # 11. Initiative Operations
    print("\n11. Creating Initiative...")
    initiative = ops.create_initiative(
        name="Improve Authentication",
        description="Make authentication more secure and user-friendly",
        target_date=datetime.now() + timedelta(days=90)
    )
    print(f"   ✓ Created initiative: {initiative.name}")

    # 12. Document Operations
    print("\n12. Creating Document...")
    doc = ops.create_document(
        title="Authentication Architecture",
        content="# OAuth2 Implementation\n\nWe will use OAuth2 for authentication..."
    )
    print(f"   ✓ Created document: {doc.title}")

    # 13. Attachment Operations
    print("\n13. Creating Attachment...")
    attachment = ops.create_attachment(
        title="Design Mockup",
        url="https://example.com/mockup.png",
        issue_id=issue1.id
    )
    print(f"   ✓ Created attachment: {attachment.title}")

    # 14. Issue Label Operations
    print("\n14. Creating Issue Labels...")
    bug_label = ops.create_issue_label(
        name="bug",
        color="#d73a4a",
        team_id=eng_team.id
    )
    feature_label = ops.create_issue_label(
        name="feature",
        color="#0e8a16",
        team_id=eng_team.id
    )
    print(f"   ✓ Created labels: {bug_label.name}, {feature_label.name}")

    # 15. Issue Relation Operations
    print("\n15. Creating Issue Relation...")
    relation = ops.create_issue_relation(
        issue_id=issue1.id,
        related_issue_id=issue2.id,
        type="related"
    )
    print(f"   ✓ Created issue relation: {relation.type}")

    # 16. List Operations
    print("\n16. Listing Entities...")
    projects = ops.list_projects(limit=10)
    relations = ops.list_issue_relations(issue1.id)
    print(f"   ✓ Found {len(projects)} projects")
    print(f"   ✓ Found {len(relations)} relations for issue")

    # 17. Pydantic Serialization (for AI agents)
    print("\n17. Pydantic Serialization...")
    issue_dict = issue1.model_dump()
    print(f"   ✓ Serialized issue to dict with {len(issue_dict)} fields")
    issue_json = issue1.model_dump_json()
    print(f"   ✓ Serialized issue to JSON ({len(issue_json)} bytes)")

    print("\n" + "=" * 60)
    print("✅ All CRUD operations completed successfully!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - 1 Organization")
    print(f"  - 2 Users")
    print(f"  - 2 Teams")
    print(f"  - 3 Workflow States")
    print(f"  - 2 Issues (1 updated)")
    print(f"  - 2 Comments")
    print(f"  - 1 Project")
    print(f"  - 2 Project Milestones")
    print(f"  - 1 Cycle")
    print(f"  - 1 Initiative")
    print(f"  - 1 Document")
    print(f"  - 1 Attachment")
    print(f"  - 2 Issue Labels")
    print(f"  - 1 Issue Relation")
    print(f"\nTotal: 22 entities created across 14 entity types")
    print(f"\nAll entities support Pydantic serialization for AI agents!")

    # Cleanup
    session.close()
    engine.dispose()
    import os
    os.close(db_fd)
    os.unlink(db_path)


if __name__ == "__main__":
    # Add src to path
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    main()
