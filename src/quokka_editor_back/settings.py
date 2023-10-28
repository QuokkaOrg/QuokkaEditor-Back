from pathlib import Path

from pydantic import BaseSettings, PostgresDsn


class MonitoringSettings(BaseSettings):
    rich_logging: bool = False
    sentry_dsn: str | None = None
    root_log_level: str = "DEBUG"
    app_log_level: str = "INFO"


class DatabaseSettings(BaseSettings):
    database_dsn: PostgresDsn


class JwtSettings(BaseSettings):
    secret_key: str = "cbf2eba1064f98a3c8f3a239ae257176444cfcbebdf7c7bc038b85b409df5bfb"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class RuntimeSettings(BaseSettings):
    debug: bool = False


class Settings(
    RuntimeSettings,
    DatabaseSettings,
    MonitoringSettings,
    JwtSettings,
):
    pass


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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler"
            if settings.rich_logging
            else "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": settings.root_log_level,
    },
    "loggers": {
        "quokka_editor_back": {
            "handlers": ["console"],
            "level": settings.app_log_level,
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
