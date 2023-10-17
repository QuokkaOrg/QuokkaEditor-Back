from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "operation" RENAME COLUMN "char" TO "content";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "operation" RENAME COLUMN "content" TO "char";"""
