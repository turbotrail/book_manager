

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, status
from jose import jwt
from app.core.config import settings
from app.api.dependencies import get_current_user

@pytest.mark.asyncio
@patch("app.api.dependencies.get_db")
async def test_get_current_user_success(mock_get_db):
    fake_token = jwt.encode({"sub": "testuser"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    mock_user = MagicMock()
    mock_user.username = "testuser"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override():
        yield mock_session

    mock_get_db.side_effect = override

    username = await get_current_user(token=fake_token, db=mock_session)
    assert username == "testuser"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token="invalid.token.here", db=MagicMock())

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
@patch("app.api.dependencies.get_db")
async def test_get_current_user_no_sub_claim(mock_get_db):
    token = jwt.encode({}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    mock_session = MagicMock()

    async def override():
        yield mock_session

    mock_get_db.side_effect = override

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=mock_session)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
@patch("app.api.dependencies.get_db")
async def test_get_current_user_user_not_found(mock_get_db):
    token = jwt.encode({"sub": "ghostuser"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override():
        yield mock_session

    mock_get_db.side_effect = override

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=mock_session)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED