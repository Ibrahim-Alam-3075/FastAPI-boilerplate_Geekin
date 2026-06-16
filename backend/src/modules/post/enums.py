"""Post status enums."""

from enum import StrEnum


class PostStatus(StrEnum):
    """Post published status."""

    DRAFT = "draft"
    PUBLISHED = "published"
