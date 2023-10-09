import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker


rabbitmq_broker = RabbitmqBroker(url="amqp://guest:guest@rabbitmq:5672")
dramatiq.set_broker(rabbitmq_broker)

from quokka_editor_back.utils.actors.task import (
    transform_document,
)  # noqa: E402

__all__ = ("transform_document",)
