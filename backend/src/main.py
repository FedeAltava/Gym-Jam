from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.src.presentation.error_handlers import application_error_handler
from backend.src.application.errors import ApplicationError
from backend.src.presentation.routers.workouts import router as workouts_router
from backend.src.presentation.routers.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="Gym-Jam API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(workouts_router, prefix="/workouts", tags=["workouts"])
    return app


app = create_app()

