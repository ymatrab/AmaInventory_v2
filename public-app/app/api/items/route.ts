import { NextResponse } from "next/server";

import { loadCampaignOrThrow } from "@/lib/campaign";
import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { requireSession } from "@/lib/session";
import { assertCampaignOpen } from "@/lib/window";

// GET /api/items?warehouse={id} — item reference for counting (no quantities).
// Window-enforced: rejects with 423 when the campaign is not open.
export async function GET() {
  try {
    const session = requireSession();
    const campaign = await loadCampaignOrThrow(session.campaignId);
    assertCampaignOpen(campaign);

    const items = await prisma.itemRef.findMany({
      where: { campaignId: campaign.id },
      orderBy: [{ itemCode: "asc" }, { sku: "asc" }],
    });
    return NextResponse.json({
      items: items.map((i) => ({
        item_code: i.itemCode,
        sku: i.sku,
        description: i.description,
        color_parfum: i.colorParfum,
        base_unit: i.baseUnit,
        units_per_pack: i.unitsPerPack,
      })),
    });
  } catch (err) {
    return errorResponse(err);
  }
}
