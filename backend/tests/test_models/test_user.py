import pytest
from sqlalchemy import select
from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(username="testuser", password_hash="hashed_pw", role="admin")
    db_session.add(user)
    await db_session.commit()
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    found = result.scalar_one()
    assert found.username == "testuser"
    assert found.role == "admin"
    assert found.created_at is not None


@pytest.mark.asyncio
async def test_user_unique_username(db_session):
    user1 = User(username="duplicate", password_hash="hash1", role="user")
    user2 = User(username="duplicate", password_hash="hash2", role="user")
    db_session.add(user1)
    await db_session.commit()
    db_session.add(user2)
    with pytest.raises(Exception):
        await db_session.commit()
