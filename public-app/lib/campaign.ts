import { prisma } from "./db";
import { ApiError } from "./http";

// Load the campaign window fields or throw 404. Shared by field routes.
export async function loadCampaignOrThrow(campaignId: string) {
  const campaign = await prisma.campaign.findUnique({
    where: { id: campaignId },
    select: { id: true, code: true, status: true, openAt: true, closeAt: true },
  });
  if (!campaign) {
    throw new ApiError(404, "campaign_not_found", "Campaign not found.");
  }
  return campaign;
}

// CountLine -> API shape. qty fields are agent-entered counts (allowed on public).
export function serializeLine(line: {
  lineUid: string;
  warehouseId: string;
  itemCode: string;
  sku: string;
  qtyUnits: unknown;
  qtyPacks: unknown;
  agentId: string;
  isRecount: boolean;
  flagged: boolean;
  version: number;
  updatedAt: Date;
}) {
  return {
    line_uid: line.lineUid,
    warehouse_id: line.warehouseId,
    item_code: line.itemCode,
    sku: line.sku,
    qty_units: Number(line.qtyUnits),
    qty_packs: Number(line.qtyPacks),
    agent_id: line.agentId,
    is_recount: line.isRecount,
    flagged: line.flagged,
    version: line.version,
    updated_at: line.updatedAt,
  };
}
