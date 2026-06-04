-- CreateEnum
CREATE TYPE "CampaignStatus" AS ENUM ('DRAFT', 'ARMED', 'OPEN', 'RECOUNT', 'CLOSED', 'ARCHIVED');

-- CreateEnum
CREATE TYPE "AgentRole" AS ENUM ('AGENT', 'WAREHOUSEMAN');

-- CreateTable
CREATE TABLE "campaign" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "status" "CampaignStatus" NOT NULL DEFAULT 'ARMED',
    "open_at" TIMESTAMP(3),
    "close_at" TIMESTAMP(3),

    CONSTRAINT "campaign_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "warehouse" (
    "id" TEXT NOT NULL,
    "whs_code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "city" TEXT NOT NULL DEFAULT '',
    "campaign_id" TEXT NOT NULL,

    CONSTRAINT "warehouse_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "item_ref" (
    "id" TEXT NOT NULL,
    "item_code" TEXT NOT NULL,
    "sku" TEXT NOT NULL,
    "description" TEXT NOT NULL DEFAULT '',
    "color_parfum" TEXT NOT NULL DEFAULT '',
    "base_unit" TEXT NOT NULL DEFAULT 'unit',
    "units_per_pack" INTEGER NOT NULL DEFAULT 1,
    "campaign_id" TEXT NOT NULL,

    CONSTRAINT "item_ref_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "agent" (
    "id" TEXT NOT NULL,
    "full_name" TEXT NOT NULL,
    "role" "AgentRole" NOT NULL,

    CONSTRAINT "agent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "agent_credential" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "campaign_id" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "pin_hash" TEXT NOT NULL,
    "expires_at" TIMESTAMP(3),
    "active" BOOLEAN NOT NULL DEFAULT true,
    "failed_attempts" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "agent_credential_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "count_line" (
    "line_uid" TEXT NOT NULL,
    "campaign_id" TEXT NOT NULL,
    "warehouse_id" TEXT NOT NULL,
    "item_code" TEXT NOT NULL,
    "qty_units" DECIMAL(65,30) NOT NULL DEFAULT 0,
    "qty_packs" DECIMAL(65,30) NOT NULL DEFAULT 0,
    "agent_id" TEXT NOT NULL,
    "is_recount" BOOLEAN NOT NULL DEFAULT false,
    "flagged" BOOLEAN NOT NULL DEFAULT false,
    "version" INTEGER NOT NULL DEFAULT 1,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "count_line_pkey" PRIMARY KEY ("line_uid")
);

-- CreateIndex
CREATE UNIQUE INDEX "campaign_code_key" ON "campaign"("code");

-- CreateIndex
CREATE UNIQUE INDEX "warehouse_campaign_id_whs_code_key" ON "warehouse"("campaign_id", "whs_code");

-- CreateIndex
CREATE UNIQUE INDEX "item_ref_campaign_id_item_code_sku_key" ON "item_ref"("campaign_id", "item_code", "sku");

-- CreateIndex
CREATE UNIQUE INDEX "agent_credential_token_key" ON "agent_credential"("token");

-- CreateIndex
CREATE UNIQUE INDEX "agent_credential_agent_id_campaign_id_key" ON "agent_credential"("agent_id", "campaign_id");

-- CreateIndex
CREATE INDEX "count_line_campaign_id_updated_at_idx" ON "count_line"("campaign_id", "updated_at");

-- CreateIndex
CREATE INDEX "count_line_campaign_id_agent_id_idx" ON "count_line"("campaign_id", "agent_id");

-- AddForeignKey
ALTER TABLE "warehouse" ADD CONSTRAINT "warehouse_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "campaign"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "item_ref" ADD CONSTRAINT "item_ref_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "campaign"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "agent_credential" ADD CONSTRAINT "agent_credential_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agent"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "agent_credential" ADD CONSTRAINT "agent_credential_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "campaign"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "count_line" ADD CONSTRAINT "count_line_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "campaign"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "count_line" ADD CONSTRAINT "count_line_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "warehouse"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "count_line" ADD CONSTRAINT "count_line_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agent"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
