import { NextResponse } from "next/server";

import { loadCampaignOrThrow, serializeLine } from "@/lib/campaign";
import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { requireSession } from "@/lib/session";
import { assertCampaignOpen } from "@/lib/window";

// GET /api/recount — flagged lines for this agent to re-count.
export async function GET() {
  try {
    const session = requireSession();
    const campaign = await loadCampaignOrThrow(session.campaignId);
    assertCampaignOpen(campaign);

    const lines = await prisma.countLine.findMany({
      where: { campaignId: campaign.id, agentId: session.agentId, flagged: true },
      orderBy: { itemCode: "asc" },
    });
    return NextResponse.json({ lines: lines.map(serializeLine) });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
