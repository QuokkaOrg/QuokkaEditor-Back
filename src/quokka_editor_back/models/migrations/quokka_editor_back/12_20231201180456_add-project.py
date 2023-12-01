from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" ADD "project_id" UUID NOT NULL;
        CREATE TABLE IF NOT EXISTS "project" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(250) NOT NULL,
    "images" TEXT,
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
        ALTER TABLE "document" ADD CONSTRAINT "fk_document_project_d5717276" FOREIGN KEY ("project_id") REFERENCES "project" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" DROP CONSTRAINT "fk_document_project_d5717276";
        ALTER TABLE "document" DROP COLUMN "project_id";
        DROP TABLE IF EXISTS "project";"""
