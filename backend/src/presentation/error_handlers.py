from fastapi import Request
from fastapi.responses import JSONResponse
from backend.src.application.errors import (
    ApplicationError,
    ExerciseNotFoundError,
    InvalidRefreshTokenError,
    LogNotFoundError,
    SessionAlreadyCompletedError,
    SessionAlreadyInProgressError,
    SessionNotFoundError,
    SetAlreadyLoggedError,
    SetExceedsPlanError,
    UnauthorizedError,
    WorkoutNotFoundError,
)


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    if isinstance(exc, (WorkoutNotFoundError, ExerciseNotFoundError, SessionNotFoundError, LogNotFoundError)):
        status_code = 404
    elif isinstance(exc, UnauthorizedError):
        status_code = 403
    elif isinstance(exc, InvalidRefreshTokenError):
        status_code = 401
    elif isinstance(exc, (SessionAlreadyCompletedError, SessionAlreadyInProgressError, SetAlreadyLoggedError)):
        status_code = 409
    elif isinstance(exc, SetExceedsPlanError):
        status_code = 422
    else:
        status_code = 422
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )
