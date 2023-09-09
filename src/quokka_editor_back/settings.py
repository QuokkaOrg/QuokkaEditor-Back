from pathlib import Path
from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):
    debug: bool = False
    database_dsn: PostgresDsn
    rich_logging: bool = False
    root_log_level: str = "ERROR"
    log_level: str = "DEBUG"
    secret_key: str = "cbf2eba1064f98a3c8f3a239ae257176444cfcbebdf7c7bc038b85b409df5bfb"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()

BASE_PATH = Path(__file__).parent.resolve()

TORTOISE_ORM = {
    "connections": {"default": settings.database_dsn},
    "apps": {
        "quokka_editor_back": {
            "models": [
                "quokka_editor_back.models.document",
                "quokka_editor_back.models.user",
                "quokka_editor_back.models.operation",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
