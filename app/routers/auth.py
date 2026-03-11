import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.user import TokenPair, TokenRefresh, UserCreate, UserLogin, UserRead
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit(f"{settings.RATE_LIMIT_TIMES}/{settings.RATE_LIMIT_SECONDS}second")
async def register(
    request: Request,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    if await get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    if await get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    user = await create_user(db, payload.email, payload.username, payload.password)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login and receive access + refresh tokens",
)
@limiter.limit(f"{settings.RATE_LIMIT_TIMES}/{settings.RATE_LIMIT_SECONDS}second")
async def login(
    request: Request,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        subject=str(user.id),
        extra={"email": user.email, "is_admin": user.is_admin},
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    logger.info("user_logged_in", user_id=str(user.id))
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh access token using a refresh token",
)
async def refresh_token(
    payload: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise credentials_exception

    if data.get("type") != "refresh":
        raise credentials_exception

    user_id: str | None = data.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise credentials_exception

    new_access = create_access_token(
        subject=str(user.id),
        extra={"email": user.email, "is_admin": user.is_admin},
    )
    new_refresh = create_refresh_token(subject=str(user.id))
    logger.info("token_refreshed", user_id=str(user.id))
    return TokenPair(access_token=new_access, refresh_token=new_refresh)
