from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE "document_operation" (
    "document_id" UUID NOT NULL REFERENCES "document" ("id") ON DELETE CASCADE,
    "operation_id" UUID NOT NULL REFERENCES "operation" ("id") ON DELETE SET NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "document_operation";"""
