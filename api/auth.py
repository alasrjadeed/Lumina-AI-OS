"""Authentication API — register, login, manage API keys."""

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from api.middleware.auth import verify_request
from core.security.auth import Authentication

router = APIRouter(prefix="/auth", tags=["Authentication"])

auth_engine = Authentication()


class RegisterRequest(BaseModel):
    username: str
    password: str
    roles: list[str] = ["user"]


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str


@router.post("/register")
async def register(req: RegisterRequest):
    try:
        user = auth_engine.register_user(req.username, req.password, req.roles)
        return {
            "id": user.id,
            "username": user.username,
            "roles": user.roles,
            "created": user.created,
        }
    except ValueError as e:
        return {"error": str(e)}


@router.post("/login")
async def login(req: LoginRequest):
    session = auth_engine.authenticate(req.username, req.password)
    if not session:
        return {"error": "Invalid credentials or account locked"}
    return {
        "token": session.token,
        "user_id": session.user_id,
        "expires": session.expires,
    }


@router.post("/logout")
async def logout(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        auth_engine.logout(token)
    return {"status": "ok"}


@router.get("/me")
async def me(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        user = auth_engine.validate_session(token)
        if user:
            return {
                "authenticated": True, "sub": user.id,
                "username": user.username, "roles": user.roles,
            }
        key_user = auth_engine.validate_api_key(token)
        if key_user:
            return {
                "authenticated": True, "sub": key_user.id,
                "username": key_user.username, "method": "api_key",
            }
    return {"authenticated": False}


@router.post("/api-key")
async def create_api_key(username: str, auth: dict = Depends(verify_request)):
    try:
        key = auth_engine.create_api_key(username)
        return {"api_key": key}
    except ValueError as e:
        return {"error": str(e)}


@router.delete("/api-key")
async def revoke_api_key(username: str, key: str, auth: dict = Depends(verify_request)):
    ok = auth_engine.revoke_api_key(username, key)
    return {"revoked": ok}


@router.post("/change-password")
async def change_password(req: ChangePasswordRequest):
    ok = auth_engine.change_password(req.username, req.old_password, req.new_password)
    return {"success": ok}


@router.get("/users")
async def list_users(auth: dict = Depends(verify_request)):
    users = auth_engine.list_users()
    return {
        "users": [
            {"id": u.id, "username": u.username, "roles": u.roles, "enabled": u.enabled}
            for u in users
        ]
    }


@router.post("/users/disable")
async def disable_user(username: str, auth: dict = Depends(verify_request)):
    return {"disabled": auth_engine.disable_user(username)}


@router.post("/users/enable")
async def enable_user(username: str, auth: dict = Depends(verify_request)):
    return {"enabled": auth_engine.enable_user(username)}
