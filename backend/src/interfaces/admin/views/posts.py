"""Admin view for Post model."""

from sqladmin import ModelView
from starlette.requests import Request
from wtforms import SelectField

from ....infrastructure.database.session import local_session
from ....modules.post.crud import crud_posts
from ....modules.post.enums import PostStatus
from ....modules.post.models import Post
from ..mixins import DataclassModelMixin

POST_STATUS_CHOICES = [(s.value, s.value.title()) for s in PostStatus]


class PostAdmin(DataclassModelMixin, ModelView, model=Post):
    """Admin view for Post model."""

    name = "Post"
    name_plural = "Posts"
    icon = "fa-solid fa-file-lines"
    category = "Content"

    column_list = [
        Post.id,
        Post.title,
        Post.published_status,
        Post.author_id,
        Post.author,
        Post.created_at,
        Post.is_deleted,
    ]
    column_details_list = "__all__"
    column_searchable_list = [Post.title, Post.body_content]
    column_sortable_list = [Post.id, Post.title, Post.published_status, Post.author_id, Post.created_at]
    column_default_sort = [(Post.id, True)]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True

    form_create_rules = ["title", "body_content", "published_status", "author"]
    form_edit_rules = ["title", "body_content", "published_status", "author", "is_deleted"]

    form_overrides = {"published_status": SelectField}
    form_args = {"published_status": {"choices": POST_STATUS_CHOICES}}

    async def delete_model(self, request: Request, pk: str) -> None:
        """Soft delete a post when deleted from the admin panel."""
        async with local_session() as db:
            await crud_posts.delete(db=db, id=int(pk))
