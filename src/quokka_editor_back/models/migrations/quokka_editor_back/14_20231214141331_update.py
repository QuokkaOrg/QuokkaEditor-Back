from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" DROP COLUMN "shared_by_link";
        ALTER TABLE "document" DROP COLUMN "shared_role";
        ALTER TABLE "project" ADD "shared_by_link" BOOL NOT NULL  DEFAULT False;
        ALTER TABLE "project" ADD "shared_role" VARCHAR(7) NOT NULL  DEFAULT 'READ';
        ALTER TABLE "project" ALTER COLUMN "images" TYPE JSONB USING "images"::JSONB;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "project" DROP COLUMN "shared_by_link";
        ALTER TABLE "project" DROP COLUMN "shared_role";
        ALTER TABLE "project" ALTER COLUMN "images" TYPE TEXT USING "images"::TEXT;
        ALTER TABLE "document" ADD "shared_by_link" BOOL NOT NULL  DEFAULT False;
        ALTER TABLE "document" ADD "shared_role" VARCHAR(7) NOT NULL  DEFAULT 'READ';"""
