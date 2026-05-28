from fastapi import FastAPI
from backend.src.presentation.error_handlers import application_error_handler
from backend.src.application.errors import ApplicationError


def create_app() -> FastAPI:
    app = FastAPI(title="Gym-Jam API", version="0.1.0")
    app.add_exception_handler(ApplicationError, application_error_handler)
    # Router will be added in slice 2
    return app


app = create_app()
