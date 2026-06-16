from typing import Annotated

from fastapi import Depends

from .service import PostService


def get_post_service() -> PostService:
    """Dependency injection to get the PostService."""
    return PostService()


PostServiceDep = Annotated[PostService, Depends(get_post_service)]
