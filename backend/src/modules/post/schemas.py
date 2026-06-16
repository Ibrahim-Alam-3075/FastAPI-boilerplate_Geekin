from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..common.schemas import PersistentDeletion, TimestampSchema
from ..user.schemas import UserRead


class PostBase(BaseModel):
    """Base schema for Post model."""

    title: Annotated[str, Field(min_length=1, max_length=100, examples=["My first blog post"])]
    body_content: Annotated[str, Field(min_length=1, examples=["This is the content of the blog post."])]
    published_status: Annotated[str, Field(default="draft", examples=["draft", "published"])]


class Post(TimestampSchema, PostBase, PersistentDeletion):
    """Complete post schema with all database fields."""

    id: int
    author_id: int


class PostRead(PostBase):
    """Schema for reading post data."""

    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool = False


class PostReadWithAuthor(PostRead):
    """Schema for reading post data along with its author."""

    author: UserRead | None = None


class PostCreate(PostBase):
    """Schema for creating a post."""

    model_config = ConfigDict(extra="forbid")


class PostCreateInternal(PostBase):
    """Internal schema for post creation with author_id."""

    author_id: int


class PostUpdate(BaseModel):
    """Schema for updating post data."""

    model_config = ConfigDict(extra="forbid")

    title: Annotated[str | None, Field(min_length=1, max_length=100, default=None)]
    body_content: Annotated[str | None, Field(min_length=1, default=None)]
    published_status: Annotated[str | None, Field(default=None, examples=["draft", "published"])]


class PostUpdateInternal(PostUpdate):
    """Internal schema for post updates."""

    updated_at: datetime
