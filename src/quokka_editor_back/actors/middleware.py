import asyncio

from dramatiq.middleware import Middleware
from tortoise import Tortoise

from quokka_editor_back.settings import TORTOISE_ORM


class DBConnectionMiddleware(Middleware):
    def before_process_message(self, broker, message):
        asyncio.run(self.configure_db())
        return super().before_process_message(broker, message)

    async def configure_db(self):
        await Tortoise.init(config=TORTOISE_ORM)
