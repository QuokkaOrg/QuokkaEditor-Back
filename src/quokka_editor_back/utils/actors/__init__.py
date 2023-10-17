import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from quokka_editor_back.utils.actors.middleware import DBConnectionMiddleware

rabbitmq_broker = RabbitmqBroker(url="amqp://guest:guest@rabbitmq:5672")
rabbitmq_broker.add_middleware(DBConnectionMiddleware())
dramatiq.set_broker(rabbitmq_broker)

from quokka_editor_back.utils.actors.task import transform_document  # noqa: E402

__all__ = ("transform_document",)
