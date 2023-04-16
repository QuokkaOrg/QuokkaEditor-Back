import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    pass


settings = Settings()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("ROOT_LOG_LEVEL", "DEBUG")},
    "loggers": {
        "quokka_editor_back": {
            "handlers": ["console"],
            "level": os.getenv("LOG_LEVEL", "ERROR"),
            "propagate": False,
        }
    },
}
