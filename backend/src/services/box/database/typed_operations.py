"""
Typed operations for Box service - Pydantic-compatible wrappers for CRUD operations.

This module provides type-safe wrappers around the existing operations.py functions.
All inputs and outputs use Pydantic models for validation and serialization, making
them compatible with AI agent SDKs (Anthropic, OpenAI, LangChain, etc.).

Usage:
    from services.box.database.typed_operations import BoxOperations
    from sqlalchemy.orm import Session

    # Initialize with session (typically from your eval framework)
    ops = BoxOperations(session)

    # Call methods without passing session each time
    user = ops.get_user(user_id="123")
    user_dict = user.model_dump()  # Serialize to dict

    folder = ops.create_folder(
        name="My Folder",
        parent_id="0",
        user_id="user-123"
    )

    # All returned models have Pydantic methods:
    # - .model_dump() - serialize to dict
    # - .model_dump_json() - serialize to JSON string
    # - .model_json_schema() - get JSON schema
"""

from typing import Optional, Literal, List
from sqlalchemy.orm import Session

# Import existing operations - we're wrapping these
from . import operations as ops
from .schema import User, Folder, File, FileVersion, Comment


class BoxOperations:
    """
    Type-safe operations for Box service.

    This class wraps the operations.py functions to provide a cleaner interface
    for AI agents. The session is encapsulated so AI tools don't need to manage it.

    Example:
        ops = BoxOperations(session)

        # Create a folder
        folder = ops.create_folder(
            name="Reports",
            parent_id="0",
            user_id="user-123"
        )

        # Serialize for AI agent
        folder_data = folder.model_dump()
    """

    def __init__(self, session: Session):
        """
        Initialize operations with a database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    # ==========================================================================
    # USER OPERATIONS
    # ==========================================================================

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: Box user ID

        Returns:
            User model with Pydantic serialization methods, or None if not found

        Example:
            user = ops.get_user("123")
            if user:
                print(user.model_dump())
        """
        return ops.get_user_by_id(self.session, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by login/email.

        Args:
            email: User's email address

        Returns:
            User model or None if not found
        """
        return ops.get_user_by_login(self.session, email)

    def create_user(
        self,
        *,
        name: str,
        login: str,
        user_id: Optional[str] = None,
        status: str = "active",
        job_title: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        language: Optional[str] = None,
    ) -> User:
        """
        Create a new Box user.

        Args:
            name: User's display name
            login: User's email/login
            user_id: Optional custom user ID (auto-generated if not provided)
            status: User status (default: "active")
            job_title: User's job title
            phone: User's phone number
            address: User's address
            language: User's language preference

        Returns:
            Created User model with Pydantic methods

        Example:
            user = ops.create_user(
                name="John Doe",
                login="john@example.com",
                job_title="Engineer"
            )
            user_data = user.model_dump()
        """
        return ops.create_user(
            self.session,
            name=name,
            login=login,
            user_id=user_id,
            status=status,
            job_title=job_title,
            phone=phone,
            address=address,
            language=language,
        )

    # ==========================================================================
    # FOLDER OPERATIONS
    # ==========================================================================

    def get_folder(self, folder_id: str) -> Optional[Folder]:
        """
        Get a folder by ID.

        Args:
            folder_id: Box folder ID

        Returns:
            Folder model or None if not found
        """
        return ops.get_folder_by_id(self.session, folder_id)

    def create_folder(
        self,
        *,
        name: str,
        parent_id: str,
        user_id: str,
        folder_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Folder:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID ("0" for root)
            user_id: Owner user ID
            folder_id: Optional custom folder ID (auto-generated if not provided)
            description: Optional folder description

        Returns:
            Created Folder model

        Raises:
            BoxAPIError: If parent not found, name invalid, or other errors

        Example:
            folder = ops.create_folder(
                name="Documents",
                parent_id="0",
                user_id="user-123"
            )
            print(folder.model_dump_json())
        """
        return ops.create_folder(
            self.session,
            name=name,
            parent_id=parent_id,
            user_id=user_id,
            folder_id=folder_id,
            description=description,
        )

    def update_folder(
        self,
        folder_id: str,
        *,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Folder:
        """
        Update a folder.

        Args:
            folder_id: Folder ID to update
            user_id: User ID making the update
            name: New name (optional)
            description: New description (optional)
            parent_id: New parent folder ID (optional, for moving)

        Returns:
            Updated Folder model

        Raises:
            BoxAPIError: If folder not found or validation fails
        """
        update_data = {'user_id': user_id}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        if parent_id is not None:
            update_data['parent_id'] = parent_id

        return ops.update_folder(self.session, folder_id, **update_data)

    def delete_folder(self, folder_id: str, *, recursive: bool = False) -> None:
        """
        Delete a folder.

        Args:
            folder_id: Folder ID to delete
            recursive: If True, delete all contents recursively

        Raises:
            BoxAPIError: If folder not found or not empty (when recursive=False)
        """
        ops.delete_folder(self.session, folder_id, recursive=recursive)

    def list_folder_items(
        self,
        folder_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[str] = None,
        direction: Literal["ASC", "DESC"] = "ASC",
        fields: Optional[List[str]] = None
    ) -> dict:
        """
        List items in a folder (files and subfolders).

        Args:
            folder_id: Parent folder ID
            limit: Maximum items to return (default 100)
            offset: Number of items to skip (for pagination)
            sort: Sort field (name, id, date, size, etc.)
            direction: Sort direction ("ASC" or "DESC")
            fields: Optional list of fields to include

        Returns:
            Dictionary with 'entries', 'total_count', 'offset', 'limit'
            All entry models have Pydantic methods

        Example:
            result = ops.list_folder_items("0", limit=50)
            for item in result['entries']:
                print(item.model_dump())
        """
        return ops.list_folder_items(
            self.session,
            folder_id=folder_id,
            limit=limit,
            offset=offset,
            sort=sort,
            direction=direction,
            fields=fields
        )

    # ==========================================================================
    # FILE OPERATIONS
    # ==========================================================================

    def get_file(self, file_id: str) -> Optional[File]:
        """
        Get a file by ID.

        Args:
            file_id: Box file ID

        Returns:
            File model or None if not found
        """
        return ops.get_file_by_id(self.session, file_id)

    def create_file(
        self,
        *,
        name: str,
        parent_id: str,
        user_id: str,
        content: Optional[bytes] = None,
        size: Optional[int] = None,
        file_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> File:
        """
        Create a new file (upload).

        Args:
            name: File name
            parent_id: Parent folder ID
            user_id: Owner user ID
            content: File content bytes (optional)
            size: File size in bytes (optional)
            file_id: Optional custom file ID (auto-generated if not provided)
            description: Optional file description

        Returns:
            Created File model

        Example:
            file = ops.create_file(
                name="document.pdf",
                parent_id="0",
                user_id="user-123",
                content=pdf_bytes
            )
            file_info = file.model_dump()
        """
        return ops.create_file(
            self.session,
            name=name,
            parent_id=parent_id,
            user_id=user_id,
            content=content,
            size=size,
            file_id=file_id,
            description=description,
        )

    def update_file(
        self,
        file_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> File:
        """
        Update a file's metadata.

        Args:
            file_id: File ID to update
            name: New name (optional)
            description: New description (optional)
            parent_id: New parent folder ID (optional, for moving)

        Returns:
            Updated File model
        """
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        if parent_id is not None:
            update_data['parent_id'] = parent_id

        return ops.update_file(self.session, file_id, **update_data)

    def delete_file(self, file_id: str) -> None:
        """
        Delete a file.

        Args:
            file_id: File ID to delete

        Raises:
            BoxAPIError: If file not found
        """
        ops.delete_file(self.session, file_id)

    def upload_file_version(
        self,
        file_id: str,
        *,
        content: bytes,
        size: Optional[int] = None
    ) -> FileVersion:
        """
        Upload a new version of an existing file.

        Args:
            file_id: File ID to upload new version for
            content: New file content bytes
            size: File size in bytes (optional)

        Returns:
            Created FileVersion model

        Example:
            version = ops.upload_file_version(
                file_id="456",
                content=new_content_bytes
            )
            print(version.model_dump())
        """
        return ops.upload_file_version(
            self.session,
            file_id=file_id,
            content=content,
            size=size
        )

    # ==========================================================================
    # COMMENT OPERATIONS
    # ==========================================================================

    def create_comment(
        self,
        *,
        item_id: str,
        item_type: Literal["file", "comment"],
        message: str,
        user_id: str,
        comment_id: Optional[str] = None,
    ) -> Comment:
        """
        Create a comment on a file or another comment (reply).

        Args:
            item_id: ID of file or comment to comment on
            item_type: "file" or "comment"
            message: Comment text
            user_id: User ID creating the comment
            comment_id: Optional custom comment ID

        Returns:
            Created Comment model

        Example:
            comment = ops.create_comment(
                item_id="file-123",
                item_type="file",
                message="Great document!",
                user_id="user-456"
            )
        """
        return ops.create_comment(
            self.session,
            item_id=item_id,
            item_type=item_type,
            message=message,
            user_id=user_id,
            comment_id=comment_id,
        )

    def get_comment(self, comment_id: str) -> Optional[Comment]:
        """
        Get a comment by ID.

        Args:
            comment_id: Comment ID

        Returns:
            Comment model or None if not found
        """
        return ops.get_comment_by_id(self.session, comment_id)

    def update_comment(
        self,
        comment_id: str,
        *,
        message: str
    ) -> Comment:
        """
        Update a comment's message.

        Args:
            comment_id: Comment ID to update
            message: New message text

        Returns:
            Updated Comment model
        """
        return ops.update_comment(self.session, comment_id, message=message)

    def delete_comment(self, comment_id: str) -> None:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID to delete
        """
        ops.delete_comment(self.session, comment_id)

    # ==========================================================================
    # SEARCH OPERATIONS
    # ==========================================================================

    def search_content(
        self,
        query: str,
        *,
        limit: int = 30,
        offset: int = 0,
        content_types: Optional[List[str]] = None,
        ancestor_folder_ids: Optional[List[str]] = None
    ) -> dict:
        """
        Search for files and folders by name/content.

        Args:
            query: Search query string
            limit: Maximum results to return
            offset: Number of results to skip
            content_types: Optional list of types to filter
            ancestor_folder_ids: Optional list of folder IDs to search within

        Returns:
            Dictionary with 'entries', 'total_count', 'offset', 'limit'

        Example:
            results = ops.search_content("contract", limit=50)
            for item in results['entries']:
                print(f"{item['type']}: {item['name']}")
        """
        return ops.search_content(
            self.session,
            query=query,
            limit=limit,
            offset=offset,
            content_types=content_types,
            ancestor_folder_ids=ancestor_folder_ids
        )
