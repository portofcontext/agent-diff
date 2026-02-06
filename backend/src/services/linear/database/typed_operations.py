"""
Typed operations wrapper for Linear API.

This module provides a class-based API for Linear database operations, encapsulating
session management for easier use by AI agents.

These operations are designed to be used as tools for AI agents, with clear type hints
and comprehensive CRUD operations for all major Linear entities.

Note: Linear primarily uses GraphQL resolvers. This wrapper provides direct database
operations for testing and simple use cases. For full GraphQL functionality, use the
resolvers directly.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .entity_defaults import (
    attachment_defaults,
    comment_defaults,
    cycle_defaults,
    document_defaults,
    initiative_defaults,
    issue_defaults,
    issue_label_defaults,
    organization_defaults,
    project_defaults,
    project_milestone_defaults,
    team_defaults,
    user_defaults,
    workflow_state_defaults,
)
from .schema import (
    Attachment,
    Comment,
    Cycle,
    Document,
    Initiative,
    Issue,
    IssueLabel,
    IssueRelation,
    Organization,
    Project,
    ProjectMilestone,
    Team,
    User,
    WorkflowState,
)


class LinearOperations:
    """
    Typed operations for Linear API.

    This class provides direct database operations for Linear entities.
    For full GraphQL functionality, use the GraphQL resolvers.

    Example usage:
        ops = LinearOperations(session)

        # Create an organization
        org = ops.create_organization(name="Acme Inc")

        # Create a user
        user = ops.create_user(
            email="user@acme.com",
            name="John Doe"
        )

        # Create a team
        team = ops.create_team(
            name="Engineering",
            key="ENG",
            organization_id=org.id
        )

        # Create an issue
        issue = ops.create_issue(
            team_id=team.id,
            title="Fix bug in login"
        )
    """

    def __init__(self, session: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    # ========================================================================
    # ORGANIZATION OPERATIONS
    # ========================================================================

    def create_organization(
        self, name: str, *, url_key: Optional[str] = None, **kwargs: Any
    ) -> Organization:
        """
        Create a new organization.

        Args:
            name: Organization name
            url_key: Optional URL key (defaults to lowercase name)
            **kwargs: Additional field overrides

        Returns:
            Organization model
        """
        defaults = organization_defaults(name, url_key, **kwargs)
        org = Organization(**defaults)
        self.session.add(org)
        self.session.flush()
        return org

    def get_organization(self, org_id: str) -> Optional[Organization]:
        """
        Get an organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Organization model or None if not found
        """
        return self.session.get(Organization, org_id)

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def create_user(
        self,
        email: str,
        name: str,
        *,
        display_name: Optional[str] = None,
        admin: bool = False,
        **kwargs: Any,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email
            name: User name
            display_name: Optional display name
            admin: Whether user is admin (default: False)
            **kwargs: Additional field overrides

        Returns:
            User model
        """
        overrides = {"admin": admin, **kwargs}
        if display_name is not None:
            overrides["displayName"] = display_name

        defaults = user_defaults(email, name, **overrides)
        user = User(**defaults)
        self.session.add(user)
        self.session.flush()
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User model or None if not found
        """
        return self.session.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            email: User email

        Returns:
            User model or None if not found
        """
        stmt = select(User).where(User.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    # ========================================================================
    # TEAM OPERATIONS
    # ========================================================================

    def create_team(
        self,
        name: str,
        key: str,
        organization_id: str,
        *,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> Team:
        """
        Create a new team.

        Args:
            name: Team name
            key: Team key (e.g., "ENG")
            organization_id: Organization ID
            description: Optional team description
            **kwargs: Additional field overrides

        Returns:
            Team model
        """
        overrides = kwargs.copy()
        if description is not None:
            overrides["description"] = description

        defaults = team_defaults(name, key, organization_id, **overrides)
        team = Team(**defaults)
        self.session.add(team)
        self.session.flush()
        return team

    def get_team(self, team_id: str) -> Optional[Team]:
        """
        Get a team by ID.

        Args:
            team_id: Team ID

        Returns:
            Team model or None if not found
        """
        return self.session.get(Team, team_id)

    # ========================================================================
    # WORKFLOW STATE OPERATIONS
    # ========================================================================

    def create_workflow_state(
        self,
        name: str,
        team_id: str,
        *,
        color: str = "#000000",
        type: str = "unstarted",
        **kwargs: Any,
    ) -> WorkflowState:
        """
        Create a new workflow state.

        Args:
            name: State name (e.g., "Todo", "In Progress")
            team_id: Team ID
            color: State color (hex)
            type: State type (e.g., "unstarted", "started", "completed", "canceled")
            **kwargs: Additional field overrides

        Returns:
            WorkflowState model
        """
        overrides = {"color": color, **kwargs}
        defaults = workflow_state_defaults(name, team_id, type, **overrides)
        state = WorkflowState(**defaults)
        self.session.add(state)
        self.session.flush()
        return state

    def get_workflow_state(self, state_id: str) -> Optional[WorkflowState]:
        """
        Get a workflow state by ID.

        Args:
            state_id: Workflow state ID

        Returns:
            WorkflowState model or None if not found
        """
        return self.session.get(WorkflowState, state_id)

    # ========================================================================
    # ISSUE OPERATIONS
    # ========================================================================

    def create_issue(
        self,
        team_id: str,
        title: str,
        *,
        description: Optional[str] = None,
        priority: int = 0,
        state_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        creator_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Issue:
        """
        Create a new issue.

        Args:
            team_id: Team ID
            title: Issue title
            description: Optional issue description
            priority: Issue priority (0-4, default: 0)
            state_id: Optional workflow state ID
            assignee_id: Optional assignee user ID
            creator_id: Optional creator user ID
            **kwargs: Additional field overrides

        Returns:
            Issue model
        """
        overrides = {"priority": priority, **kwargs}
        if description is not None:
            overrides["description"] = description
        if state_id is not None:
            overrides["stateId"] = state_id
        if assignee_id is not None:
            overrides["assigneeId"] = assignee_id
        if creator_id is not None:
            overrides["creatorId"] = creator_id

        defaults = issue_defaults(team_id, title, **overrides)
        issue = Issue(**defaults)
        self.session.add(issue)
        self.session.flush()
        return issue

    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """
        Get an issue by ID.

        Args:
            issue_id: Issue ID

        Returns:
            Issue model or None if not found
        """
        return self.session.get(Issue, issue_id)

    def update_issue(
        self,
        issue_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        state_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
    ) -> Optional[Issue]:
        """
        Update an issue.

        Args:
            issue_id: Issue ID to update
            title: New title
            description: New description
            priority: New priority
            state_id: New workflow state ID
            assignee_id: New assignee user ID

        Returns:
            Updated Issue model or None if not found
        """
        issue = self.session.get(Issue, issue_id)
        if issue is None:
            return None

        if title is not None:
            issue.title = title
        if description is not None:
            issue.description = description
        if priority is not None:
            issue.priority = priority
        if state_id is not None:
            issue.stateId = state_id
        if assignee_id is not None:
            issue.assigneeId = assignee_id

        issue.updatedAt = datetime.now()
        self.session.flush()
        return issue

    def delete_issue(self, issue_id: str) -> bool:
        """
        Delete an issue.

        Args:
            issue_id: Issue ID to delete

        Returns:
            True if deleted, False if not found
        """
        issue = self.session.get(Issue, issue_id)
        if issue is None:
            return False

        self.session.delete(issue)
        self.session.flush()
        return True

    # ========================================================================
    # COMMENT OPERATIONS
    # ========================================================================

    def create_comment(
        self, issue_id: str, body: str, *, user_id: Optional[str] = None, **kwargs: Any
    ) -> Comment:
        """
        Create a new comment on an issue.

        Args:
            issue_id: Issue ID
            body: Comment body
            user_id: Optional user ID
            **kwargs: Additional field overrides

        Returns:
            Comment model
        """
        overrides = kwargs.copy()
        if user_id is not None:
            overrides["userId"] = user_id

        defaults = comment_defaults(issue_id, body, **overrides)
        comment = Comment(**defaults)
        self.session.add(comment)
        self.session.flush()
        return comment

    def get_comment(self, comment_id: str) -> Optional[Comment]:
        """
        Get a comment by ID.

        Args:
            comment_id: Comment ID

        Returns:
            Comment model or None if not found
        """
        return self.session.get(Comment, comment_id)

    def update_comment(
        self,
        comment_id: str,
        body: str,
    ) -> Optional[Comment]:
        """
        Update a comment.

        Args:
            comment_id: Comment ID to update
            body: New comment body

        Returns:
            Updated Comment model or None if not found
        """
        comment = self.session.get(Comment, comment_id)
        if comment is None:
            return None

        comment.body = body
        comment.updatedAt = datetime.now()
        self.session.flush()
        return comment

    def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID to delete

        Returns:
            True if deleted, False if not found
        """
        comment = self.session.get(Comment, comment_id)
        if comment is None:
            return False

        self.session.delete(comment)
        self.session.flush()
        return True

    # ========================================================================
    # PROJECT OPERATIONS
    # ========================================================================

    def create_project(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        team_ids: Optional[list[str]] = None,
        lead_id: Optional[str] = None,
        target_date: Optional[datetime] = None,
        **kwargs: Any,
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name
            description: Optional project description
            team_ids: Optional list of team IDs
            lead_id: Optional project lead user ID
            target_date: Optional target completion date
            **kwargs: Additional field overrides

        Returns:
            Project model
        """
        overrides = kwargs.copy()
        if description is not None:
            overrides["description"] = description
        if team_ids is not None:
            overrides["teamIds"] = team_ids
        if lead_id is not None:
            overrides["leadId"] = lead_id
        if target_date is not None:
            overrides["targetDate"] = target_date

        defaults = project_defaults(name, **overrides)
        project = Project(**defaults)
        self.session.add(project)
        self.session.flush()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project model or None if not found
        """
        return self.session.get(Project, project_id)

    def update_project(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        target_date: Optional[datetime] = None,
        **kwargs: Any,
    ) -> Optional[Project]:
        """
        Update a project.

        Args:
            project_id: Project ID to update
            name: New project name
            description: New description
            target_date: New target date
            **kwargs: Additional field updates

        Returns:
            Updated Project model or None if not found
        """
        project = self.session.get(Project, project_id)
        if project is None:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if target_date is not None:
            project.targetDate = target_date

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updatedAt = datetime.now()
        self.session.flush()
        return project

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID to delete

        Returns:
            True if deleted, False if not found
        """
        project = self.session.get(Project, project_id)
        if project is None:
            return False

        self.session.delete(project)
        self.session.flush()
        return True

    def list_projects(
        self, *, team_id: Optional[str] = None, limit: int = 100
    ) -> list[Project]:
        """
        List projects.

        Args:
            team_id: Optional filter by team ID
            limit: Maximum number of projects to return

        Returns:
            List of Project models
        """
        stmt = select(Project).limit(limit)
        # Note: team filtering would require join on team relationship
        return list(self.session.execute(stmt).scalars())

    # ========================================================================
    # PROJECT MILESTONE OPERATIONS
    # ========================================================================

    def create_project_milestone(
        self,
        name: str,
        project_id: str,
        *,
        target_date: Optional[datetime] = None,
        **kwargs: Any,
    ) -> ProjectMilestone:
        """
        Create a new project milestone.

        Args:
            name: Milestone name
            project_id: Project ID
            target_date: Optional target date
            **kwargs: Additional field overrides

        Returns:
            ProjectMilestone model
        """
        overrides = kwargs.copy()
        if target_date is not None:
            overrides["targetDate"] = target_date

        defaults = project_milestone_defaults(name, project_id, **overrides)
        milestone = ProjectMilestone(**defaults)
        self.session.add(milestone)
        self.session.flush()
        return milestone

    def get_project_milestone(self, milestone_id: str) -> Optional[ProjectMilestone]:
        """
        Get a project milestone by ID.

        Args:
            milestone_id: Milestone ID

        Returns:
            ProjectMilestone model or None if not found
        """
        return self.session.get(ProjectMilestone, milestone_id)

    def update_project_milestone(
        self,
        milestone_id: str,
        *,
        name: Optional[str] = None,
        target_date: Optional[datetime] = None,
    ) -> Optional[ProjectMilestone]:
        """
        Update a project milestone.

        Args:
            milestone_id: Milestone ID to update
            name: New milestone name
            target_date: New target date

        Returns:
            Updated ProjectMilestone model or None if not found
        """
        milestone = self.session.get(ProjectMilestone, milestone_id)
        if milestone is None:
            return None

        if name is not None:
            milestone.name = name
        if target_date is not None:
            milestone.targetDate = target_date

        milestone.updatedAt = datetime.now()
        self.session.flush()
        return milestone

    def delete_project_milestone(self, milestone_id: str) -> bool:
        """
        Delete a project milestone.

        Args:
            milestone_id: Milestone ID to delete

        Returns:
            True if deleted, False if not found
        """
        milestone = self.session.get(ProjectMilestone, milestone_id)
        if milestone is None:
            return False

        self.session.delete(milestone)
        self.session.flush()
        return True

    # ========================================================================
    # CYCLE OPERATIONS
    # ========================================================================

    def create_cycle(
        self,
        team_id: str,
        number: int,
        starts_at: datetime,
        ends_at: datetime,
        *,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Cycle:
        """
        Create a new cycle.

        Args:
            team_id: Team ID
            number: Cycle number
            starts_at: Start date
            ends_at: End date
            name: Optional cycle name
            **kwargs: Additional field overrides

        Returns:
            Cycle model
        """
        overrides = kwargs.copy()
        if name is not None:
            overrides["name"] = name

        defaults = cycle_defaults(team_id, number, starts_at, ends_at, **overrides)
        cycle = Cycle(**defaults)
        self.session.add(cycle)
        self.session.flush()
        return cycle

    def get_cycle(self, cycle_id: str) -> Optional[Cycle]:
        """
        Get a cycle by ID.

        Args:
            cycle_id: Cycle ID

        Returns:
            Cycle model or None if not found
        """
        return self.session.get(Cycle, cycle_id)

    def update_cycle(
        self,
        cycle_id: str,
        *,
        name: Optional[str] = None,
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
    ) -> Optional[Cycle]:
        """
        Update a cycle.

        Args:
            cycle_id: Cycle ID to update
            name: New cycle name
            starts_at: New start date
            ends_at: New end date

        Returns:
            Updated Cycle model or None if not found
        """
        cycle = self.session.get(Cycle, cycle_id)
        if cycle is None:
            return None

        if name is not None:
            cycle.name = name
        if starts_at is not None:
            cycle.startsAt = starts_at
        if ends_at is not None:
            cycle.endsAt = ends_at

        cycle.updatedAt = datetime.now()
        self.session.flush()
        return cycle

    def delete_cycle(self, cycle_id: str) -> bool:
        """
        Delete a cycle.

        Args:
            cycle_id: Cycle ID to delete

        Returns:
            True if deleted, False if not found
        """
        cycle = self.session.get(Cycle, cycle_id)
        if cycle is None:
            return False

        self.session.delete(cycle)
        self.session.flush()
        return True

    # ========================================================================
    # INITIATIVE OPERATIONS
    # ========================================================================

    def create_initiative(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        target_date: Optional[datetime] = None,
        **kwargs: Any,
    ) -> Initiative:
        """
        Create a new initiative.

        Args:
            name: Initiative name
            description: Optional description
            target_date: Optional target date
            **kwargs: Additional field overrides

        Returns:
            Initiative model
        """
        overrides = kwargs.copy()
        if description is not None:
            overrides["description"] = description
        if target_date is not None:
            overrides["targetDate"] = target_date

        defaults = initiative_defaults(name, **overrides)
        initiative = Initiative(**defaults)
        self.session.add(initiative)
        self.session.flush()
        return initiative

    def get_initiative(self, initiative_id: str) -> Optional[Initiative]:
        """
        Get an initiative by ID.

        Args:
            initiative_id: Initiative ID

        Returns:
            Initiative model or None if not found
        """
        return self.session.get(Initiative, initiative_id)

    def update_initiative(
        self,
        initiative_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        target_date: Optional[datetime] = None,
    ) -> Optional[Initiative]:
        """
        Update an initiative.

        Args:
            initiative_id: Initiative ID to update
            name: New initiative name
            description: New description
            target_date: New target date

        Returns:
            Updated Initiative model or None if not found
        """
        initiative = self.session.get(Initiative, initiative_id)
        if initiative is None:
            return None

        if name is not None:
            initiative.name = name
        if description is not None:
            initiative.description = description
        if target_date is not None:
            initiative.targetDate = target_date

        initiative.updatedAt = datetime.now()
        self.session.flush()
        return initiative

    def delete_initiative(self, initiative_id: str) -> bool:
        """
        Delete an initiative.

        Args:
            initiative_id: Initiative ID to delete

        Returns:
            True if deleted, False if not found
        """
        initiative = self.session.get(Initiative, initiative_id)
        if initiative is None:
            return False

        self.session.delete(initiative)
        self.session.flush()
        return True

    # ========================================================================
    # DOCUMENT OPERATIONS
    # ========================================================================

    def create_document(
        self, title: str, *, content: Optional[str] = None, **kwargs: Any
    ) -> Document:
        """
        Create a new document.

        Args:
            title: Document title
            content: Optional document content
            **kwargs: Additional field overrides

        Returns:
            Document model
        """
        overrides = kwargs.copy()
        if content is not None:
            overrides["content"] = content

        defaults = document_defaults(title, **overrides)
        document = Document(**defaults)
        self.session.add(document)
        self.session.flush()
        return document

    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document model or None if not found
        """
        return self.session.get(Document, document_id)

    def update_document(
        self,
        document_id: str,
        *,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Optional[Document]:
        """
        Update a document.

        Args:
            document_id: Document ID to update
            title: New document title
            content: New document content

        Returns:
            Updated Document model or None if not found
        """
        document = self.session.get(Document, document_id)
        if document is None:
            return None

        if title is not None:
            document.title = title
        if content is not None:
            document.content = content

        document.updatedAt = datetime.now()
        self.session.flush()
        return document

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deleted, False if not found
        """
        document = self.session.get(Document, document_id)
        if document is None:
            return False

        self.session.delete(document)
        self.session.flush()
        return True

    # ========================================================================
    # ATTACHMENT OPERATIONS
    # ========================================================================

    def create_attachment(
        self, title: str, url: str, *, issue_id: Optional[str] = None, **kwargs: Any
    ) -> Attachment:
        """
        Create a new attachment.

        Args:
            title: Attachment title
            url: Attachment URL
            issue_id: Optional issue ID to attach to
            **kwargs: Additional field overrides

        Returns:
            Attachment model
        """
        overrides = kwargs.copy()
        if issue_id is not None:
            overrides["issueId"] = issue_id

        defaults = attachment_defaults(title, url, **overrides)
        attachment = Attachment(**defaults)
        self.session.add(attachment)
        self.session.flush()
        return attachment

    def get_attachment(self, attachment_id: str) -> Optional[Attachment]:
        """
        Get an attachment by ID.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment model or None if not found
        """
        return self.session.get(Attachment, attachment_id)

    def delete_attachment(self, attachment_id: str) -> bool:
        """
        Delete an attachment.

        Args:
            attachment_id: Attachment ID to delete

        Returns:
            True if deleted, False if not found
        """
        attachment = self.session.get(Attachment, attachment_id)
        if attachment is None:
            return False

        self.session.delete(attachment)
        self.session.flush()
        return True

    # ========================================================================
    # ISSUE LABEL OPERATIONS
    # ========================================================================

    def create_issue_label(
        self,
        name: str,
        *,
        color: Optional[str] = None,
        team_id: Optional[str] = None,
        **kwargs: Any,
    ) -> IssueLabel:
        """
        Create a new issue label.

        Args:
            name: Label name
            color: Optional label color (hex)
            team_id: Optional team ID
            **kwargs: Additional field overrides

        Returns:
            IssueLabel model
        """
        overrides = kwargs.copy()
        if color is not None:
            overrides["color"] = color
        if team_id is not None:
            overrides["teamId"] = team_id

        defaults = issue_label_defaults(name, **overrides)
        label = IssueLabel(**defaults)
        self.session.add(label)
        self.session.flush()
        return label

    def get_issue_label(self, label_id: str) -> Optional[IssueLabel]:
        """
        Get an issue label by ID.

        Args:
            label_id: Label ID

        Returns:
            IssueLabel model or None if not found
        """
        return self.session.get(IssueLabel, label_id)

    def update_issue_label(
        self,
        label_id: str,
        *,
        name: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Optional[IssueLabel]:
        """
        Update an issue label.

        Args:
            label_id: Label ID to update
            name: New label name
            color: New label color

        Returns:
            Updated IssueLabel model or None if not found
        """
        label = self.session.get(IssueLabel, label_id)
        if label is None:
            return None

        if name is not None:
            label.name = name
        if color is not None:
            label.color = color

        label.updatedAt = datetime.now()
        self.session.flush()
        return label

    def delete_issue_label(self, label_id: str) -> bool:
        """
        Delete an issue label.

        Args:
            label_id: Label ID to delete

        Returns:
            True if deleted, False if not found
        """
        label = self.session.get(IssueLabel, label_id)
        if label is None:
            return False

        self.session.delete(label)
        self.session.flush()
        return True

    # ========================================================================
    # ISSUE RELATION OPERATIONS
    # ========================================================================

    def create_issue_relation(
        self,
        issue_id: str,
        related_issue_id: str,
        type: str = "related",
    ) -> IssueRelation:
        """
        Create a relation between two issues.

        Args:
            issue_id: Source issue ID
            related_issue_id: Related issue ID
            type: Relation type (e.g., "blocks", "blocked", "duplicate", "related")

        Returns:
            IssueRelation model
        """
        from uuid import uuid4

        relation = IssueRelation(
            id=str(uuid4()),
            issueId=issue_id,
            relatedIssueId=related_issue_id,
            type=type,
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
        )
        self.session.add(relation)
        self.session.flush()
        return relation

    def get_issue_relation(self, relation_id: str) -> Optional[IssueRelation]:
        """
        Get an issue relation by ID.

        Args:
            relation_id: Relation ID

        Returns:
            IssueRelation model or None if not found
        """
        return self.session.get(IssueRelation, relation_id)

    def delete_issue_relation(self, relation_id: str) -> bool:
        """
        Delete an issue relation.

        Args:
            relation_id: Relation ID to delete

        Returns:
            True if deleted, False if not found
        """
        relation = self.session.get(IssueRelation, relation_id)
        if relation is None:
            return False

        self.session.delete(relation)
        self.session.flush()
        return True

    def list_issue_relations(self, issue_id: str) -> list[IssueRelation]:
        """
        List all relations for an issue.

        Args:
            issue_id: Issue ID

        Returns:
            List of IssueRelation models
        """
        stmt = select(IssueRelation).where(
            (IssueRelation.issueId == issue_id)
            | (IssueRelation.relatedIssueId == issue_id)
        )
        return list(self.session.execute(stmt).scalars())
