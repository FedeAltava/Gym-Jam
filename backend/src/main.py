from fastapi import FastAPI
from backend.src.presentation.error_handlers import application_error_handler
from backend.src.application.errors import ApplicationError
from backend.src.presentation.routers.workouts import router as workouts_router


def create_app() -> FastAPI:
    app = FastAPI(title="Gym-Jam API", version="0.1.0")
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.include_router(workouts_router, prefix="/workouts", tags=["workouts"])
    return app


app = create_app()


app = create_app()
