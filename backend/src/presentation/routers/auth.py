from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infrastructure.database import get_session
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from backend.src.infrastructure.persistence.models import UserModel
from backend.src.infrastructure.auth.jwt import create_access_token
from backend.src.infrastructure.auth.password import hash_password, verify_password
from backend.src.presentation.dependencies import get_current_user
from backend.src.presentation.schemas.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()
_user_repo = SqlAlchemyUserRepository()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    existing = await _user_repo.find_by_email(body.email, session)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = UserModel(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    await _user_repo.save(user, session)
    await session.commit()
    return UserResponse(id=user.id, email=user.email, created_at=user.created_at)


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await _user_repo.find_by_email(body.email, session)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(
    user: UserModel = Depends(get_current_user),
) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, created_at=user.created_at)
