import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from jose import JWTError
from app.api.dependencies import get_current_user
from app.db import models
from unittest.mock import AsyncMock, MagicMock, patch, ANY

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    # Mock dependencies
    mock_token = "valid_token"
    mock_db = AsyncMock()
    mock_user = models.User(username="testuser")
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

    # Mock JWT decode
    with patch("app.api.dependencies.jwt.decode") as mock_jwt_decode:
        mock_jwt_decode.return_value = {"sub": "testuser"}

        # Call the function
        result = await get_current_user(token=mock_token, db=mock_db)

        # Assertions
        assert result == "testuser"
        mock_jwt_decode.assert_called_once_with(mock_token, ANY, algorithms=ANY)
        mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    # Mock dependencies
    mock_token = "invalid_token"
    mock_db = AsyncMock()

    # Mock JWT decode to raise JWTError
    with patch("app.api.dependencies.jwt.decode", side_effect=JWTError):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    # Mock dependencies
    mock_token = "valid_token"
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    # Mock JWT decode
    with patch("app.api.dependencies.jwt.decode") as mock_jwt_decode:
        mock_jwt_decode.return_value = {"sub": "testuser"}

        # Call the function and expect an exception
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"
        mock_jwt_decode.assert_called_once_with(mock_token, ANY, algorithms=ANY)
        mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_current_user_missing_username_in_token():
    # Mock dependencies
    mock_token = "valid_token"
    mock_db = AsyncMock()

    # Mock JWT decode
    with patch("app.api.dependencies.jwt.decode") as mock_jwt_decode:
        mock_jwt_decode.return_value = {"sub": None}

        # Call the function and expect an exception
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"
        mock_jwt_decode.assert_called_once_with(mock_token, ANY, algorithms=ANY)
        mock_db.execute.assert_not_called()
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token():
        # Mock dependencies
        mock_token = "valid_token"
        mock_db = AsyncMock()
        mock_user = models.User(username="testuser")
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock JWT decode
        with patch("app.api.dependencies.jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = {"sub": "testuser"}

            # Call the function
            result = await get_current_user(token=mock_token, db=mock_db)

            # Assertions
            assert result == "testuser"
            mock_jwt_decode.assert_called_once_with(mock_token, ANY, algorithms=ANY)
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token():
        # Mock dependencies
        mock_token = "invalid_token"
        mock_db = AsyncMock()

        # Mock JWT decode to raise JWTError
        with patch("app.api.dependencies.jwt.decode", side_effect=JWTError):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=mock_token, db=mock_db)

            # Assertions
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found():
        # Mock dependencies
        mock_token = "valid_token"
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Mock JWT decode
        with patch("app.api.dependencies.jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = {"sub": "testuser"}

            # Call the function and expect an exception
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=mock_token, db=mock_db)

            # Assertions
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.detail == "Could not validate credentials"
            mock_jwt_decode.assert_called_once_with(mock_token, ANY, algorithms=ANY)
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_missing_username_in_token():
        # Mock dependencies
        mock_token = "valid_token"
        mock_db = AsyncMock()

        # Mock JWT decode
        with patch("app.api.dependencies.jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = {"sub": None}

            # Call the function and expect an exception
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=mock_token, db=mock_db)

            # Assertions
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.detail == "Could not validate credentials"
            mock_jwt_decode.assert_called_once_with(mock_token, ANY, algorithms=ANY)
            mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_jwt_decode_error():
        # Mock dependencies
        mock_token = "valid_token"
        mock_db = AsyncMock()

        # Mock JWT decode to raise a generic JWTError
        with patch("app.api.dependencies.jwt.decode", side_effect=JWTError):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=mock_token, db=mock_db)

            # Assertions
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.detail == "Could not validate credentials"
