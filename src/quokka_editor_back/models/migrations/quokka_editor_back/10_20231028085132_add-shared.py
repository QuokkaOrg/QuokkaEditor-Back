from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" ADD "shared_role" VARCHAR(7) NOT NULL  DEFAULT 'READ';
        ALTER TABLE "document" ADD "shared_by_link" BOOL NOT NULL  DEFAULT False;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" DROP COLUMN "shared_role";
        ALTER TABLE "document" DROP COLUMN "shared_by_link";"""
