import { NextRequest, NextResponse } from "next/server";

import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { verifySyncAuth } from "@/lib/sync-auth";
import { syncItemsSchema } from "@/lib/sync-validation";

// POST /api/sync/items — gestion upserts the campaign's item reference (no quantities).
export async function POST(req: NextRequest) {
  try {
    const raw = await req.text();
    verifySyncAuth(req.headers, raw);
    const items = syncItemsSchema.parse(JSON.parse(raw));

    for (const i of items) {
      const data = {
        description: i.description,
        colorParfum: i.color_parfum,
        baseUnit: i.base_unit,
        unitsPerPack: i.units_per_pack,
      };
      await prisma.itemRef.upsert({
        where: {
          campaignId_itemCode_sku: { campaignId: i.campaign_id, itemCode: i.item_code, sku: i.sku },
        },
        update: data,
        create: { campaignId: i.campaign_id, itemCode: i.item_code, sku: i.sku, ...data },
      });
    }
    return NextResponse.json({ ok: true, count: items.length });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
