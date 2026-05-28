from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./gym_jam.db"

    class Config:
        env_file = ".env"


settings = Settings()
