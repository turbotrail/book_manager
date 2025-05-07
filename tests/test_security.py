import pytest
from datetime import timedelta, datetime
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

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_token["sub"] == "testuser"
    assert "exp" in decoded_token

def test_create_access_token_with_expiry():
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=5)
    token = create_access_token(data, expires_delta)
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_token["sub"] == "testuser"
    assert "exp" in decoded_token
    assert datetime.utcfromtimestamp(decoded_token["exp"]) <= datetime.utcnow() + expires_delta

def test_get_current_user_valid_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    username = get_current_user(token)
    assert username == "testuser"

def test_get_current_user_invalid_token():
    invalid_token = "invalid.token.here"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(invalid_token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_hash_password():
    password = "mysecretpassword"
    hashed = hash_password(password)
    assert hashed != password
    assert isinstance(hashed, str)

def test_verify_password():
    password = "mysecretpassword"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False