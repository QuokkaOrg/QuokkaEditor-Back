from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" ADD "user_id" UUID NOT NULL;
        ALTER TABLE "document" ALTER COLUMN "content" DROP NOT NULL;
        CREATE TABLE IF NOT EXISTS "user" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "username" VARCHAR(250) NOT NULL UNIQUE,
    "email" VARCHAR(250) NOT NULL UNIQUE,
    "first_name" VARCHAR(250) NOT NULL  DEFAULT '',
    "last_name" VARCHAR(250) NOT NULL  DEFAULT '',
    "hashed_password" VARCHAR(250) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT False
);
CREATE INDEX IF NOT EXISTS "idx_user_usernam_9987ab" ON "user" ("username");
CREATE INDEX IF NOT EXISTS "idx_user_email_1b4f1c" ON "user" ("email");;
        ALTER TABLE "document" ADD CONSTRAINT "fk_document_user_9d856bc0" FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" DROP CONSTRAINT "fk_document_user_9d856bc0";
        ALTER TABLE "document" DROP COLUMN "user_id";
        ALTER TABLE "document" ALTER COLUMN "content" SET NOT NULL;
        DROP TABLE IF EXISTS "user";"""
