from __future__ import annotations

import base64
import json
import os
import time
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.middleware.auth import require_admin, verify_request


@pytest.fixture(autouse=True)
def disable_auth():
    with patch("api.middleware.auth.settings") as mock:
        mock.auth_enabled = True
        mock.api_keys = "test-key-1,test-key-2"
        yield mock


@pytest.mark.asyncio
class TestVerifyRequest:
    async def test_no_auth_raises(self):
        with patch("api.middleware.auth.settings.auth_enabled", True):
            with pytest.raises(HTTPException) as exc:
                await verify_request(None)
            assert exc.value.status_code == 401

    async def test_valid_api_key(self):
        with patch("api.middleware.auth.settings") as mock:
            mock.auth_enabled = True
            mock.api_keys = "sk-test-key"
            result = await verify_request(None, x_api_key="sk-test-key")
            assert result["role"] == "user"
            assert result["method"] == "api_key"

    async def test_invalid_api_key(self):
        with patch("api.middleware.auth.settings") as mock:
            mock.auth_enabled = True
            mock.api_keys = "valid-key"
            with pytest.raises(HTTPException) as exc:
                await verify_request(None, x_api_key="invalid-key")
            assert exc.value.status_code == 401

    async def test_master_key_from_env(self):
        with patch.dict(os.environ, {"LUMINA_MASTER_KEY": "super-secret"}):
            result = await verify_request(
                None, HTTPAuthorizationCredentials(scheme="Bearer", credentials="super-secret"),
            )
            assert result["role"] == "admin"
            assert result["method"] == "master_key"

    async def test_bearer_token(self):
        with patch("api.middleware.auth.settings") as mock:
            mock.auth_enabled = True
            mock.api_keys = "valid-key"
            result = await verify_request(
                None, HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-key"),
            )
            assert result is not None

    async def test_auth_disabled(self):
        with patch("api.middleware.auth.settings.auth_enabled", False):
            result = await verify_request(None)
            assert result is None

    async def test_jwt_valid(self):
        payload = {"sub": "user1", "role": "admin", "exp": time.time() + 3600}
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        jwt = f"header.{encoded}.signature"
        result = await verify_request(None, x_api_key=jwt)
        assert result["role"] == "admin"
        assert result["sub"] == "user1"

    async def test_jwt_expired(self):
        payload = {"sub": "user1", "exp": time.time() - 10}
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        jwt = f"header.{encoded}.signature"
        with pytest.raises(HTTPException):
            await verify_request(None, x_api_key=jwt)

    async def test_invalid_jwt_format(self):
        with pytest.raises(HTTPException):
            await verify_request(None, x_api_key="not-a-jwt")


@pytest.mark.asyncio
class TestRequireAdmin:
    async def test_admin_access_with_master_key(self):
        with patch.dict(os.environ, {"LUMINA_MASTER_KEY": "admin-key"}):
            result = await require_admin(
                None, HTTPAuthorizationCredentials(scheme="Bearer", credentials="admin-key"),
            )
            assert result["role"] == "admin"

    async def test_non_admin_raises(self):
        with patch("api.middleware.auth.settings.auth_enabled", True), \
             patch("api.middleware.auth.settings.api_keys", ""):
            with pytest.raises(HTTPException) as exc:
                await require_admin(None, x_api_key="any-key")
            assert exc.value.status_code in (401, 403)
