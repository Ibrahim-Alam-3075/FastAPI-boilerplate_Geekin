import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.post.models import Post
from src.modules.post.enums import PostStatus

pytestmark = pytest.mark.asyncio


async def test_create_post_success(auth_client: AsyncClient, test_user: dict):
    """Test successful post creation by an authenticated user."""
    post_data = {
        "title": "My Test Post",
        "body_content": "This is the content of the test post.",
        "published_status": "draft",
    }
    response = await auth_client.post("/api/v1/posts/", json=post_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == post_data["title"]
    assert data["body_content"] == post_data["body_content"]
    assert data["published_status"] == post_data["published_status"]
    assert data["author_id"] == test_user["id"]
    assert "id" in data


async def test_create_post_unauthenticated(client: AsyncClient):
    """Test post creation by an unauthenticated guest user."""
    post_data = {
        "title": "Guest Post",
        "body_content": "Content...",
        "published_status": "published",
    }
    response = await client.post("/api/v1/posts/", json=post_data)
    assert response.status_code == 401


async def test_get_post_by_id(auth_client: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test retrieving a post by its ID."""
    # Create post in database
    post = Post(
        title="Existing Post",
        body_content="Some existing content",
        published_status=PostStatus.PUBLISHED.value,
        author_id=test_user["id"],
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await auth_client.get(f"/api/v1/posts/{post.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == post.id
    assert data["title"] == "Existing Post"
    assert data["author"]["id"] == test_user["id"]


async def test_get_post_not_found(auth_client: AsyncClient):
    """Test retrieving a non-existent post."""
    response = await auth_client.get("/api/v1/posts/99999")
    assert response.status_code == 404


async def test_list_posts(auth_client: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test listing paginated posts."""
    # Create posts
    post1 = Post(title="Post 1", body_content="Content 1", author_id=test_user["id"])
    post2 = Post(title="Post 2", body_content="Content 2", author_id=test_user["id"])
    db_session.add_all([post1, post2])
    await db_session.commit()

    response = await auth_client.get("/api/v1/posts/?limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 2
    titles = [p["title"] for p in data["data"]]
    assert "Post 1" in titles
    assert "Post 2" in titles


async def test_update_post_by_author(auth_client: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test that a post's author can update the post."""
    post = Post(title="Old Title", body_content="Old Content", author_id=test_user["id"])
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    update_data = {
        "title": "New Title",
        "published_status": "published",
    }
    response = await auth_client.patch(f"/api/v1/posts/{post.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "New Title"
    assert data["body_content"] == "Old Content"  # unchanged
    assert data["published_status"] == "published"


async def test_update_post_unauthorized(auth_client_2: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test that editing someone else's post is forbidden."""
    post = Post(title="Old Title", body_content="Old Content", author_id=test_user["id"])
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    update_data = {"title": "Hack Title"}
    response = await auth_client_2.patch(f"/api/v1/posts/{post.id}", json=update_data)
    assert response.status_code == 403


async def test_update_post_by_superuser(superuser_auth_client: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test that a superuser can update any user's post."""
    post = Post(title="Old Title", body_content="Old Content", author_id=test_user["id"])
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    update_data = {"title": "Moderated Title"}
    response = await superuser_auth_client.patch(f"/api/v1/posts/{post.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Moderated Title"


async def test_soft_delete_post_by_author(auth_client: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test that the author can soft delete their own post."""
    post = Post(title="ToDelete", body_content="Content", author_id=test_user["id"])
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await auth_client.delete(f"/api/v1/posts/{post.id}")
    assert response.status_code == 204

    # Verify soft deleted in DB (is_deleted = True, but still in database)
    await db_session.refresh(post)
    assert post.is_deleted is True

    # Verify API no longer lists or serves it
    get_response = await auth_client.get(f"/api/v1/posts/{post.id}")
    assert get_response.status_code == 404


async def test_soft_delete_post_unauthorized(auth_client_2: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test that deleting another user's post is forbidden."""
    post = Post(title="ToDelete", body_content="Content", author_id=test_user["id"])
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await auth_client_2.delete(f"/api/v1/posts/{post.id}")
    assert response.status_code == 403


async def test_permanent_delete_post_by_author(auth_client: AsyncClient, db_session: AsyncSession, test_user: dict):
    """Test that the author can permanently delete their own post."""
    post = Post(title="ToHardDelete", body_content="Content", author_id=test_user["id"])
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await auth_client.delete(f"/api/v1/posts/{post.id}/permanent")
    assert response.status_code == 204

    # Verify fully removed from database
    db_post = await db_session.get(Post, post.id)
    assert db_post is None
