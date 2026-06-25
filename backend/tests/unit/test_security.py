"""Unit tests for security module."""
import pytest
from app.core.security import security
from app.core.permissions import Role


def test_hash_and_verify_password():
    password = "SecurePass@1"
    hashed = security.hash_password(password)
    assert hashed != password
    assert security.verify_password(password, hashed)
    assert not security.verify_password("WrongPass", hashed)


def test_create_and_decode_access_token():
    import uuid
    user_id = uuid.uuid4()
    token = security.create_access_token(subject=user_id, role=Role.ENGINEER.value)
    payload = security.decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == Role.ENGINEER.value
    assert payload["type"] == "access"


def test_create_refresh_token():
    import uuid
    user_id = uuid.uuid4()
    token = security.create_refresh_token(subject=user_id)
    payload = security.decode_token(token)
    assert payload["type"] == "refresh"


def test_invalid_token_raises():
    with pytest.raises(ValueError):
        security.decode_token("invalid.token.here")
