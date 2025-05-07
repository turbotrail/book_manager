import pytest
from datetime import timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    SECRET_KEY,
    ALGORITHM,
)

# Test for create_access_token
def test_create_access_token():
    data = {"sub": "test_user"}
    token = create_access_token(data)
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_token["sub"] == "test_user"
    assert "exp" in decoded_token

    # Test with custom expiration
    expires_delta = timedelta(minutes=60)
    token_with_exp = create_access_token(data, expires_delta)
    decoded_token_with_exp = jwt.decode(token_with_exp, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_token_with_exp["sub"] == "test_user"

# Test for get_current_user
def test_get_current_user():
    data = {"sub": "test_user"}
    token = create_access_token(data)
    username = get_current_user(token)
    assert username == "test_user"

    # Test with invalid token
    with pytest.raises(HTTPException) as exc_info:
        get_current_user("invalid_token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

# Test for hash_password and verify_password
def test_password_hashing():
    password = "secure_password"
    hashed_password = hash_password(password)
    assert hashed_password != password  # Ensure the password is hashed

    # Verify the password
    assert verify_password(password, hashed_password)
    assert not verify_password("wrong_password", hashed_password)