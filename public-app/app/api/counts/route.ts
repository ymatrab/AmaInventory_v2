import { randomUUID } from "node:crypto";

import { NextRequest, NextResponse } from "next/server";

import { loadCampaignOrThrow, serializeLine } from "@/lib/campaign";
import { prisma } from "@/lib/db";
import { ApiError, errorResponse } from "@/lib/http";
import { requireSession } from "@/lib/session";
import { countSubmitSchema } from "@/lib/validation";
import { assertCampaignOpen } from "@/lib/window";

// POST /api/counts — create or update a count line (version++ on edit).
// Window-enforced. Lines are attributed to the session agent.
export async function POST(req: NextRequest) {
  try {
    const session = requireSession();
    const campaign = await loadCampaignOrThrow(session.campaignId);
    assertCampaignOpen(campaign);

    const body = countSubmitSchema.parse(await req.json());

    const warehouse = await prisma.warehouse.findFirst({
      where: { id: body.warehouse_id, campaignId: campaign.id },
    });
    if (!warehouse) {
      throw new ApiError(400, "invalid_warehouse", "Warehouse not in this campaign.");
    }

    if (body.line_uid) {
      const existing = await prisma.countLine.findUnique({
        where: { lineUid: body.line_uid },
      });
      if (!existing || existing.agentId !== session.agentId) {
        throw new ApiError(404, "line_not_found", "Count line not found for this agent.");
      }
      const updated = await prisma.countLine.update({
        where: { lineUid: body.line_uid },
        data: {
          qtyUnits: body.qty_units,
          qtyPacks: body.qty_packs,
          version: { increment: 1 },
        },
      });
      return NextResponse.json({ line: serializeLine(updated) }, { status: 200 });
    }

    const created = await prisma.countLine.create({
      data: {
        lineUid: randomUUID(),
        campaignId: campaign.id,
        warehouseId: warehouse.id,
        itemCode: body.item_code,
        qtyUnits: body.qty_units,
        qtyPacks: body.qty_packs,
        agentId: session.agentId,
        isRecount: campaign.status === "RECOUNT",
      },
    });
    return NextResponse.json({ line: serializeLine(created) }, { status: 201 });
  } catch (err) {
    return errorResponse(err);
  }
}
