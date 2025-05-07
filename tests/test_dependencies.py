import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from jose import JWTError
from app.api.dependencies import get_current_user
from app.db import models

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    mock_token = "valid_token"
    mock_username = "test_user"

    # Mock the User object
    mock_user = MagicMock()
    mock_user.username = mock_username

    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none = AsyncMock(return_value=mock_user)

    with patch("app.api.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": mock_username}

        result = await get_current_user(token=mock_token, db=mock_db)

        assert result == mock_username
        mock_decode.assert_called_once_with(mock_token, "your_secret_key", algorithms=["HS256"])
        mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    mock_token = "invalid_token"
    mock_db = AsyncMock()

    with patch("app.api.dependencies.jwt.decode", side_effect=JWTError):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_no_username_in_token():
    mock_token = "valid_token_without_username"
    mock_db = AsyncMock()

    with patch("app.api.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": None}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    mock_token = "valid_token"
    mock_username = "non_existent_user"

    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)

    with patch("app.api.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": mock_username}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_token_with_extra_claims():
    mock_token = "valid_token_with_extra_claims"
    mock_username = "test_user"

    # Mock the User object
    mock_user = MagicMock()
    mock_user.username = mock_username

    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none = AsyncMock(return_value=mock_user)

    with patch("app.api.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": mock_username, "role": "admin"}

        result = await get_current_user(token=mock_token, db=mock_db)

        assert result == mock_username
        mock_decode.assert_called_once_with(mock_token, "your_secret_key", algorithms=["HS256"])
        mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    mock_token = "expired_token"
    mock_db = AsyncMock()

    with patch("app.api.dependencies.jwt.decode", side_effect=JWTError):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"
    mock_db = AsyncMock()

    with patch("app.api.dependencies.jwt.decode", side_effect=JWTError):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_no_username_in_token():
    mock_token = "valid_token_without_username"
    mock_db = AsyncMock()

    with patch("app.api.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": None}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    mock_token = "valid_token"
    mock_username = "non_existent_user"

    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)

    with patch("app.api.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": mock_username}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"