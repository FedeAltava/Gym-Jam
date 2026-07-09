from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from returns.result import Failure
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import RegisterUserCommand
from backend.src.application.services.token_issuer import TokenIssuer
from backend.src.application.use_cases.change_password import ChangePasswordUseCase
from backend.src.application.use_cases.forgot_password import ForgotPasswordUseCase
from backend.src.application.use_cases.logout import LogoutUseCase
from backend.src.application.use_cases.refresh_session import RefreshSessionUseCase
from backend.src.application.use_cases.register_user import RegisterUserUseCase
from backend.src.application.use_cases.reset_password import ResetPasswordUseCase
from backend.src.infrastructure.auth.password import DUMMY_HASH, verify_password
from backend.src.infrastructure.database import get_session
from backend.src.infrastructure.persistence.models import UserModel
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from backend.src.infrastructure.rate_limiter import (
    forgot_password_limiter,
    login_limiter,
    logout_limiter,
    refresh_limiter,
    register_limiter,
)
from backend.src.presentation.dependencies import (
    get_change_password_uc,
    get_current_user,
    get_current_user_optional,
    get_forgot_password_uc,
    get_logout_uc,
    get_refresh_session_uc,
    get_register_user_uc,
    get_reset_password_uc,
    get_token_issuer,
    get_user_repository,
)
from backend.src.presentation.schemas.auth_schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    uc: RegisterUserUseCase = Depends(get_register_user_uc),
    _rate: None = Depends(register_limiter.dependency),
) -> UserResponse:
    result = await uc.execute(RegisterUserCommand(email=body.email, password=body.password))
    await session.commit()
    if isinstance(result, Failure):
        raise HTTPException(status_code=409, detail=result.failure().message)
    user = result.unwrap()
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        rest_seconds=user.rest_seconds,
        units=user.units,
    )


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
    token_issuer: TokenIssuer = Depends(get_token_issuer),
    _rate: None = Depends(login_limiter.dependency),
) -> TokenResponse:
    user = await user_repo.find_by_email(body.email)
    if user is None:
        verify_password(body.password, DUMMY_HASH)
        logger.warning("Failed login attempt for unknown user")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, user.hashed_password):
        logger.warning("Failed login attempt (wrong password)")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    pair = await token_issuer.issue_for_login(user.id)
    await session.commit()
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh(
    request: Request,
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
    use_case: RefreshSessionUseCase = Depends(get_refresh_session_uc),
    _rate: None = Depends(refresh_limiter.dependency),
) -> TokenResponse:
    result = await use_case.execute(body.refresh_token)
    await session.commit()
    if isinstance(result, Failure):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    pair = result.unwrap()
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    body: LogoutRequest | None = None,
    _rate: None = Depends(logout_limiter.dependency),
    user: UserModel | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
    use_case: LogoutUseCase = Depends(get_logout_uc),
) -> Response:
    raw_refresh_token = body.refresh_token if body is not None else None
    if raw_refresh_token is None and user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await use_case.execute(user.id if user is not None else None, raw_refresh_token)
    await session.commit()
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
async def me(
    user: UserModel = Depends(get_current_user),
) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        rest_seconds=user.rest_seconds,
        units=user.units,
    )


@router.post("/forgot-password", status_code=204)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
    uc: ForgotPasswordUseCase = Depends(get_forgot_password_uc),
    _rate: None = Depends(forgot_password_limiter.dependency),
) -> Response:
    await uc.execute(body.email)
    await session.commit()
    return Response(status_code=204)


@router.post("/reset-password", status_code=204)
async def reset_password(
    body: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
    uc: ResetPasswordUseCase = Depends(get_reset_password_uc),
) -> Response:
    result = await uc.execute(body.token, body.new_password)
    await session.commit()
    if isinstance(result, Failure):
        error = result.failure()
        raise HTTPException(status_code=400, detail=error.message)
    return Response(status_code=204)


@router.patch("/password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    uc: ChangePasswordUseCase = Depends(get_change_password_uc),
) -> Response:
    result = await uc.execute(user.id, body.current_password, body.new_password)
    await session.commit()
    if isinstance(result, Failure):
        error = result.failure()
        raise HTTPException(status_code=400, detail=error.message)
    return Response(status_code=204)
