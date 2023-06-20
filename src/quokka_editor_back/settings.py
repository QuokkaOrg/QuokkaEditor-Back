from pathlib import Path
from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):
    debug: bool = False
    database_dsn: PostgresDsn
    rich_logging: bool = False
    root_log_level: str = "ERROR"
    log_level: str = "DEBUG"
    secret_key: str
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
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
