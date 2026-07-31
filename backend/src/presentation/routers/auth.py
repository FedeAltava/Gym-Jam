from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from returns.result import Failure
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import RegisterUserCommand
from backend.src.application.errors import WeakPasswordError
from backend.src.application.services.token_issuer import TokenIssuer
from backend.src.application.use_cases.change_password import ChangePasswordUseCase
from backend.src.application.use_cases.forgot_password import ForgotPasswordUseCase
from backend.src.application.use_cases.logout import LogoutUseCase
from backend.src.application.use_cases.refresh_session import RefreshSessionUseCase
from backend.src.application.use_cases.register_user import RegisterUserUseCase
from backend.src.application.use_cases.reset_password import ResetPasswordUseCase
from backend.src.infrastructure.auth.password import DUMMY_HASH, verify_password
from backend.src.infrastructure.config import settings
from backend.src.infrastructure.database import get_session
from backend.src.infrastructure.email.email_service import send_reset_email
from backend.src.infrastructure.persistence.models import UserModel
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from backend.src.infrastructure.rate_limiter import (
    change_password_limiter,
    forgot_password_limiter,
    login_limiter,
    logout_limiter,
    refresh_limiter,
    register_limiter,
    reset_password_limiter,
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
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _set_refresh_cookie(response: Response, token: str, expire_days: int) -> None:
    _is_prod = settings.environment == "production"
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        samesite="strict" if _is_prod else "lax",
        secure=_is_prod,
        max_age=expire_days * 86400,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    _is_prod = settings.environment == "production"
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
        secure=_is_prod,
        httponly=True,
        samesite="strict" if _is_prod else "lax",
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    uc: RegisterUserUseCase = Depends(get_register_user_uc),
    _rate: None = Depends(register_limiter.dependency),
) -> UserResponse:
    result = await uc.execute(RegisterUserCommand(email=body.email, password=body.password))
    if isinstance(result, Failure):
        error = result.failure()
        if isinstance(error, WeakPasswordError):
            raise HTTPException(status_code=422, detail=error.message)
        raise HTTPException(status_code=409, detail=error.message)
    await session.commit()
    user = result.unwrap()
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        rest_seconds=user.rest_seconds,
        units=user.units,
    )


@router.post("/login", status_code=200)
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
    token_issuer: TokenIssuer = Depends(get_token_issuer),
    _rate: None = Depends(login_limiter.dependency),
) -> Response:
    user = await user_repo.find_by_email(body.email)
    if user is None:
        verify_password(body.password, DUMMY_HASH)
        logger.warning("Failed login attempt for unknown user")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, user.hashed_password):
        logger.warning("Failed login attempt (wrong password)")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    pair = await token_issuer.issue_for_login(
        user.id, password_changed_at=user.password_changed_at
    )
    await session.commit()
    response = JSONResponse(content={"access_token": pair.access_token, "token_type": "bearer"})
    _set_refresh_cookie(response, pair.refresh_token, settings.refresh_token_expire_days)
    return response


@router.post("/refresh", status_code=200)
async def refresh(
    request: Request,
    session: AsyncSession = Depends(get_session),
    use_case: RefreshSessionUseCase = Depends(get_refresh_session_uc),
    _rate: None = Depends(refresh_limiter.dependency),
) -> Response:
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    result = await use_case.execute(raw_token)
    if isinstance(result, Failure):
        resp = JSONResponse(status_code=401, content={"detail": "Invalid refresh token"})
        _clear_refresh_cookie(resp)
        return resp
    await session.commit()
    pair = result.unwrap()
    response = JSONResponse(content={"access_token": pair.access_token, "token_type": "bearer"})
    _set_refresh_cookie(response, pair.refresh_token, settings.refresh_token_expire_days)
    return response


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    body: LogoutRequest | None = None,
    _rate: None = Depends(logout_limiter.dependency),
    user: UserModel | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
    use_case: LogoutUseCase = Depends(get_logout_uc),
) -> Response:
    raw_refresh_token = request.cookies.get("refresh_token")
    if raw_refresh_token is None and user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await use_case.execute(user.id if user is not None else None, raw_refresh_token)
    await session.commit()
    response = Response(status_code=204)
    _clear_refresh_cookie(response)
    return response


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
    result = await uc.execute(body.email)
    await session.commit()
    notification = result.unwrap()
    if notification is not None:
        user_email, reset_url = notification
        try:
            await send_reset_email(user_email, reset_url)
        except Exception:
            logger.warning("Failed to send password reset email to %s", user_email)
    return Response(status_code=204)


@router.post("/reset-password", status_code=204)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
    uc: ResetPasswordUseCase = Depends(get_reset_password_uc),
    _rate: None = Depends(reset_password_limiter.dependency),
) -> Response:
    result = await uc.execute(body.token, body.new_password)
    if isinstance(result, Failure):
        error = result.failure()
        if isinstance(error, WeakPasswordError):
            raise HTTPException(status_code=422, detail=error.message)
        raise HTTPException(status_code=400, detail=error.message)
    await session.commit()
    return Response(status_code=204)


@router.patch("/password", status_code=204)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    uc: ChangePasswordUseCase = Depends(get_change_password_uc),
    _rate: None = Depends(change_password_limiter.dependency),
) -> Response:
    result = await uc.execute(user.id, body.current_password, body.new_password)
    if isinstance(result, Failure):
        error = result.failure()
        if isinstance(error, WeakPasswordError):
            raise HTTPException(status_code=422, detail=error.message)
        raise HTTPException(status_code=400, detail=error.message)
    await session.commit()
    return Response(status_code=204)
