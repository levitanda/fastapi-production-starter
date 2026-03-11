from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRead
from app.services.auth import decode_token, get_user_by_id

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user",
)
async def read_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get(
    "/",
    response_model=list[UserRead],
    summary="List all users (admin only)",
)
async def list_users(
    _: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[UserRead]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]
