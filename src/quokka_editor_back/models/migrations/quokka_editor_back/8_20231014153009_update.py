from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" DROP CONSTRAINT "fk_document_revision_782dc740";
        ALTER TABLE "document" DROP COLUMN "recent_revision_id";
        ALTER TABLE "operation" ADD "from_pos" TEXT NOT NULL;
        ALTER TABLE "operation" ADD "to_pos" TEXT NOT NULL;
        ALTER TABLE "operation" ADD "text" TEXT NOT NULL;
        ALTER TABLE "operation" DROP COLUMN "content";
        ALTER TABLE "operation" DROP COLUMN "pos";
        ALTER TABLE "operation" ALTER COLUMN "type" TYPE VARCHAR(7) USING "type"::VARCHAR(7);
        ALTER TABLE "operation" ALTER COLUMN "type" TYPE VARCHAR(7) USING "type"::VARCHAR(7);
        DROP TABLE IF EXISTS "revisionlog";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" ADD "recent_revision_id" BIGINT;
        ALTER TABLE "operation" ADD "content" VARCHAR(255);
        ALTER TABLE "operation" ADD "pos" INT NOT NULL;
        ALTER TABLE "operation" DROP COLUMN "from_pos";
        ALTER TABLE "operation" DROP COLUMN "to_pos";
        ALTER TABLE "operation" DROP COLUMN "text";
        ALTER TABLE "operation" ALTER COLUMN "type" TYPE VARCHAR(6) USING "type"::VARCHAR(6);
        ALTER TABLE "operation" ALTER COLUMN "type" TYPE VARCHAR(6) USING "type"::VARCHAR(6);
        ALTER TABLE "document" ADD CONSTRAINT "fk_document_revision_782dc740" FOREIGN KEY ("recent_revision_id") REFERENCES "revisionlog" ("id") ON DELETE CASCADE;"""
