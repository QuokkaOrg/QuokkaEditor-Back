from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "documenttemplate" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(250) NOT NULL,
    "content" BYTEA
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "documenttemplate";"""
