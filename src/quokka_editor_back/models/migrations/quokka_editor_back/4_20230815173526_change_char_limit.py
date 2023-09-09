from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "operation" ALTER COLUMN "char" TYPE VARCHAR(255) USING "char"::VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "operation" ALTER COLUMN "char" TYPE VARCHAR(1) USING "char"::VARCHAR(1);"""
