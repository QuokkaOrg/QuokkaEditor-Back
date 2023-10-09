import dramatiq
from dramatiq.brokers.redis import RedisBroker


redis_broker = RedisBroker(host="redis")
dramatiq.set_broker(redis_broker)
from quokka_editor_back.utils.actors.task import (
    transform_document,
)  # noqa: E402

__all__ = ("transform_document",)
