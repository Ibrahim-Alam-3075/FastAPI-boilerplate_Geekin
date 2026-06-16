from typing import Any

from fastapi import APIRouter
from fastcrud import PaginatedListResponse, compute_offset, paginated_response

from ...infrastructure.auth.http_exceptions import HTTPException
from ...infrastructure.dependencies import AsyncSessionDep, CurrentUserDep
from ..common.utils.error_handler import handle_exception
from .dependencies import PostServiceDep
from .schemas import PostCreate, PostRead, PostReadWithAuthor, PostUpdate

router = APIRouter(tags=["Posts"])


@router.post(
    "/",
    status_code=201,
    response_model=PostRead,
    summary="Create New Blog Post",
    response_description="The created blog post",
)
async def create_post(
    post: PostCreate,
    db: AsyncSessionDep,
    current_user: CurrentUserDep,
    post_service: PostServiceDep,
) -> dict[str, Any]:
    """Create a new blog post for the current user."""
    try:
        return await post_service.create(post, author_id=current_user["id"], db=db)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get(
    "/",
    response_model=PaginatedListResponse[PostRead],
    summary="List All Blog Posts",
    response_description="A paginated list of blog posts",
)
async def get_posts(
    db: AsyncSessionDep,
    post_service: PostServiceDep,
    page: int = 1,
    items_per_page: int = 10,
) -> dict[str, Any]:
    """Get paginated list of all non-deleted blog posts."""
    posts_data = await post_service.get_paginated(skip=compute_offset(page, items_per_page), limit=items_per_page, db=db)
    return paginated_response(crud_data=posts_data, page=page, items_per_page=items_per_page)


@router.get(
    "/author/{author_id}",
    response_model=PaginatedListResponse[PostRead],
    summary="List Blog Posts by Author",
    response_description="A paginated list of blog posts by specific author",
)
async def get_posts_by_author(
    author_id: int,
    db: AsyncSessionDep,
    post_service: PostServiceDep,
    page: int = 1,
    items_per_page: int = 10,
) -> dict[str, Any]:
    """Get paginated list of blog posts by author ID."""
    posts_data = await post_service.get_paginated_by_author(
        author_id=author_id, skip=compute_offset(page, items_per_page), limit=items_per_page, db=db
    )
    return paginated_response(crud_data=posts_data, page=page, items_per_page=items_per_page)


@router.get(
    "/{post_id}",
    response_model=PostReadWithAuthor,
    summary="Get Blog Post Details",
    response_description="The blog post details with author information",
)
async def get_post(
    post_id: int,
    db: AsyncSessionDep,
    post_service: PostServiceDep,
) -> dict[str, Any]:
    """Get blog post details by post ID."""
    try:
        return await post_service.get_with_author(post_id=post_id, db=db)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.patch(
    "/{post_id}",
    response_model=PostRead,
    summary="Update Blog Post",
    response_description="The updated blog post",
)
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: AsyncSessionDep,
    current_user: CurrentUserDep,
    post_service: PostServiceDep,
) -> dict[str, Any]:
    """Update a blog post. Only the author or a superuser can update it."""
    try:
        return await post_service.update(
            post_id=post_id,
            post_update=post_update,
            author_id=current_user["id"],
            is_superuser=current_user.get("is_superuser", False),
            db=db,
        )
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.delete(
    "/{post_id}",
    status_code=204,
    summary="Soft Delete Blog Post",
)
async def delete_post(
    post_id: int,
    db: AsyncSessionDep,
    current_user: CurrentUserDep,
    post_service: PostServiceDep,
) -> None:
    """Soft delete a blog post. Only the author or a superuser can perform this action."""
    try:
        await post_service.delete(
            post_id=post_id,
            author_id=current_user["id"],
            is_superuser=current_user.get("is_superuser", False),
            db=db,
        )
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.delete(
    "/{post_id}/permanent",
    status_code=204,
    summary="Permanently Delete Blog Post",
)
async def permanent_delete_post(
    post_id: int,
    db: AsyncSessionDep,
    current_user: CurrentUserDep,
    post_service: PostServiceDep,
) -> None:
    """Permanently delete a blog post from the database."""
    try:
        await post_service.permanent_delete(
            post_id=post_id,
            author_id=current_user["id"],
            is_superuser=current_user.get("is_superuser", False),
            db=db,
        )
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
