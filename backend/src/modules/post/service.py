from typing import Any

from fastcrud import JoinConfig
from fastcrud.types import GetMultiResponseDict
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import PermissionDeniedError, ResourceNotFoundError, ValidationError
from ..user.models import User
from ..user.schemas import UserRead
from .crud import crud_posts
from .models import Post
from .schemas import PostCreate, PostCreateInternal, PostRead, PostUpdate


class PostService:
    """Service class for post-related operations."""

    async def create(self, post: PostCreate, author_id: int, db: AsyncSession) -> dict[str, Any]:
        """Create a new blog post."""
        post_internal = PostCreateInternal(**post.model_dump(), author_id=author_id)
        created_post = await crud_posts.create(db=db, object=post_internal, schema_to_select=PostRead)
        if not created_post:
            raise ValidationError("Failed to create post")
        return created_post

    async def get(self, post_id: int, db: AsyncSession) -> dict[str, Any]:
        """Get post details by ID."""
        post = await crud_posts.get(db=db, schema_to_select=PostRead, id=post_id, is_deleted=False)
        if not post:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")
        return post

    async def get_with_author(self, post_id: int, db: AsyncSession) -> dict[str, Any]:
        """Get post details along with its author."""
        joins_config = [
            JoinConfig(
                model=User,
                join_on=Post.author_id == User.id,
                join_prefix="author_",
                schema_to_select=UserRead,
                join_type="left",
            )
        ]
        post = await crud_posts.get_joined(
            db=db,
            schema_to_select=PostRead,
            joins_config=joins_config,
            nest_joins=True,
            id=post_id,
            is_deleted=False,
        )
        if not post:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")
        return post

    async def get_paginated(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> GetMultiResponseDict:
        """Retrieve a paginated list of posts."""
        return await crud_posts.get_multi(
            db=db,
            offset=skip,
            limit=limit,
            schema_to_select=PostRead,
            is_deleted=False,
        )

    async def get_paginated_by_author(
        self, author_id: int, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> GetMultiResponseDict:
        """Retrieve a paginated list of posts by a specific author."""
        return await crud_posts.get_multi(
            db=db,
            offset=skip,
            limit=limit,
            schema_to_select=PostRead,
            author_id=author_id,
            is_deleted=False,
        )

    async def update(
        self, post_id: int, post_update: PostUpdate, author_id: int, is_superuser: bool, db: AsyncSession
    ) -> dict[str, Any]:
        """Update a post. Only the author or a superuser can perform this action."""
        existing_post = await crud_posts.get(db=db, id=post_id, is_deleted=False)
        if not existing_post:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")

        if existing_post["author_id"] != author_id and not is_superuser:
            raise PermissionDeniedError("You don't have permission to update this post")

        updated_post = await crud_posts.update(
            db=db, object=post_update, id=post_id, return_columns=list(PostRead.model_fields.keys())
        )
        if not updated_post:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")
        return updated_post

    async def delete(self, post_id: int, author_id: int, is_superuser: bool, db: AsyncSession) -> None:
        """Soft delete a post. Only the author or a superuser can perform this action."""
        existing_post = await crud_posts.get(db=db, id=post_id, is_deleted=False)
        if not existing_post:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")

        if existing_post["author_id"] != author_id and not is_superuser:
            raise PermissionDeniedError("You don't have permission to delete this post")

        try:
            await crud_posts.delete(db=db, id=post_id)
        except NoResultFound:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")
        except MultipleResultsFound:
            raise ValidationError("Multiple posts found with same ID")

    async def permanent_delete(self, post_id: int, author_id: int, is_superuser: bool, db: AsyncSession) -> None:
        """Permanently delete a post. Only the author or a superuser can perform this action."""
        existing_post = await crud_posts.get(db=db, id=post_id)
        if not existing_post:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")

        if existing_post["author_id"] != author_id and not is_superuser:
            raise PermissionDeniedError("You don't have permission to permanently delete this post")

        try:
            await crud_posts.db_delete(db=db, id=post_id)
        except NoResultFound:
            raise ResourceNotFoundError(f"Post with ID {post_id} not found")
        except MultipleResultsFound:
            raise ValidationError("Multiple posts found with same ID")
