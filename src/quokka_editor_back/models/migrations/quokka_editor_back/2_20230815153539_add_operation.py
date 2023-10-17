from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "operation" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "pos" INT NOT NULL,
    "char" VARCHAR(1),
    "type" VARCHAR(6) NOT NULL
);
COMMENT ON COLUMN "operation"."type" IS 'INSERT: INSERT\nDELETE: DELETE';;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "operation";"""
