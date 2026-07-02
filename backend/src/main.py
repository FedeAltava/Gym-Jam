import logging
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.application.errors import ApplicationError
from backend.src.infrastructure.config import settings
from backend.src.presentation.error_handlers import application_error_handler
from backend.src.presentation.routers.auth import router as auth_router
from backend.src.presentation.routers.workouts import router as workouts_router

_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

logging.config.dictConfig(_LOGGING_CONFIG)


def create_app() -> FastAPI:
    app = FastAPI(title="Gym-Jam API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(workouts_router, prefix="/workouts", tags=["workouts"])
    return app


app = create_app()

