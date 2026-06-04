/*
  Warnings:

  - Added the required column `sku` to the `count_line` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "count_line" ADD COLUMN     "sku" TEXT NOT NULL;
