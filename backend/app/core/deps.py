from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from backend.app.core.database import get_db
from backend.app.core.security import verify_token
from backend.app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return {"id": user_id, "username": payload.get("username", "unknown")}


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return {"id": None, "username": "anonymous"}
