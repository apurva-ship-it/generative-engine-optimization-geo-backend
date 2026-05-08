-- Migration to add avatar_url column to User model

-- Up: add column
ALTER TABLE "users" ADD COLUMN "avatar_url" VARCHAR(255);

-- Down: drop column if exists
ALTER TABLE "users" DROP COLUMN IF EXISTS "avatar_url";
