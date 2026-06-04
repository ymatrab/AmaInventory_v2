import { NextResponse } from "next/server";

import { loadCampaignOrThrow, serializeLine } from "@/lib/campaign";
import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { requireSession } from "@/lib/session";
import { assertCampaignOpen } from "@/lib/window";

// GET /api/counts/mine — the agent's own lines + a small progress summary.
export async function GET() {
  try {
    const session = requireSession();
    const campaign = await loadCampaignOrThrow(session.campaignId);
    assertCampaignOpen(campaign);

    const lines = await prisma.countLine.findMany({
      where: { campaignId: campaign.id, agentId: session.agentId },
      orderBy: { itemCode: "asc" },
    });
    return NextResponse.json({
      lines: lines.map(serializeLine),
      progress: {
        total: lines.length,
        flagged: lines.filter((l) => l.flagged).length,
      },
    });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
