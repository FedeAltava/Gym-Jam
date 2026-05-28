from fastapi import Request
from fastapi.responses import JSONResponse
from backend.src.application.errors import (
    ApplicationError,
    WorkoutNotFoundError,
    UnauthorizedError,
)


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    if isinstance(exc, WorkoutNotFoundError):
        status_code = 404
    elif isinstance(exc, UnauthorizedError):
        status_code = 403
    else:
        status_code = 422
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )
