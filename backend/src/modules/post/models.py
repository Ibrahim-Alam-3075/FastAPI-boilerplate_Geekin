from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...infrastructure.database.models import SoftDeleteMixin, TimestampMixin
from ...infrastructure.database.session import Base
from .enums import PostStatus

if TYPE_CHECKING:
    from ..user.models import User


class Post(Base, TimestampMixin, SoftDeleteMixin):
    """Post model representing blog posts."""

    __tablename__ = "post"

    id: Mapped[int] = mapped_column(
        "id",
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body_content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        index=True,
        nullable=False,
    )

    published_status: Mapped[str] = mapped_column(String(20), default=PostStatus.DRAFT.value)

    author: Mapped["User"] = relationship("User", back_populates="posts", lazy="selectin", init=False)

    def __repr__(self) -> str:
        return f"Post('{self.title}', status='{self.published_status}')"
