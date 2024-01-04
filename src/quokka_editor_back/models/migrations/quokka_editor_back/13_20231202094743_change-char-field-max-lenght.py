from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "document" ALTER COLUMN "title" TYPE VARCHAR(255) USING "title"::VARCHAR(255);
        ALTER TABLE "documenttemplate" ALTER COLUMN "title" TYPE VARCHAR(255) USING "title"::VARCHAR(255);
        ALTER TABLE "project" ALTER COLUMN "title" TYPE VARCHAR(255) USING "title"::VARCHAR(255);
        ALTER TABLE "user" ALTER COLUMN "hashed_password" TYPE VARCHAR(255) USING "hashed_password"::VARCHAR(255);
        ALTER TABLE "user" ALTER COLUMN "first_name" TYPE VARCHAR(255) USING "first_name"::VARCHAR(255);
        ALTER TABLE "user" ALTER COLUMN "email" TYPE VARCHAR(255) USING "email"::VARCHAR(255);
        ALTER TABLE "user" ALTER COLUMN "username" TYPE VARCHAR(255) USING "username"::VARCHAR(255);
        ALTER TABLE "user" ALTER COLUMN "last_name" TYPE VARCHAR(255) USING "last_name"::VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "hashed_password" TYPE VARCHAR(250) USING "hashed_password"::VARCHAR(250);
        ALTER TABLE "user" ALTER COLUMN "first_name" TYPE VARCHAR(250) USING "first_name"::VARCHAR(250);
        ALTER TABLE "user" ALTER COLUMN "email" TYPE VARCHAR(250) USING "email"::VARCHAR(250);
        ALTER TABLE "user" ALTER COLUMN "username" TYPE VARCHAR(250) USING "username"::VARCHAR(250);
        ALTER TABLE "user" ALTER COLUMN "last_name" TYPE VARCHAR(250) USING "last_name"::VARCHAR(250);
        ALTER TABLE "project" ALTER COLUMN "title" TYPE VARCHAR(250) USING "title"::VARCHAR(250);
        ALTER TABLE "document" ALTER COLUMN "title" TYPE VARCHAR(252) USING "title"::VARCHAR(252);
        ALTER TABLE "documenttemplate" ALTER COLUMN "title" TYPE VARCHAR(250) USING "title"::VARCHAR(250);"""
