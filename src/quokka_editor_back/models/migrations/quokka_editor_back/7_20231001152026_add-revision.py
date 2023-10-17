from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" ADD "recent_revision_id" BIGINT;
        ALTER TABLE "operation" ALTER COLUMN "revision" SET NOT NULL;
        CREATE TABLE IF NOT EXISTS "revisionlog" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "operationType" VARCHAR(6) NOT NULL
);
COMMENT ON COLUMN "revisionlog"."operationType" IS 'INSERT: INSERT\nDELETE: DELETE';;
        ALTER TABLE "document" ADD CONSTRAINT "fk_document_revision_782dc740" FOREIGN KEY ("recent_revision_id") REFERENCES "revisionlog" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" DROP CONSTRAINT "fk_document_revision_782dc740";
        ALTER TABLE "document" DROP COLUMN "recent_revision_id";
        ALTER TABLE "operation" ALTER COLUMN "revision" DROP NOT NULL;
        DROP TABLE IF EXISTS "revisionlog";"""
