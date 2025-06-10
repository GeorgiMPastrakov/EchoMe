from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    @property
    def db_uri(self):
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()
