import { NextResponse } from "next/server";

import { loadCampaignOrThrow } from "@/lib/campaign";
import { prisma } from "@/lib/db";
import { ApiError, errorResponse } from "@/lib/http";
import { requireSession } from "@/lib/session";
import { isCampaignOpen } from "@/lib/window";

// GET /api/me — agent + campaign status + countable warehouses.
// Allowed regardless of window so the UI can show the closed/waiting state.
export async function GET() {
  try {
    const session = requireSession();
    const [agent, campaign] = await Promise.all([
      prisma.agent.findUnique({ where: { id: session.agentId } }),
      loadCampaignOrThrow(session.campaignId),
    ]);
    if (!agent) {
      throw new ApiError(404, "agent_not_found", "Agent not found.");
    }
    const warehouses = await prisma.warehouse.findMany({
      where: { campaignId: campaign.id },
      orderBy: { whsCode: "asc" },
    });
    return NextResponse.json({
      agent: { id: agent.id, full_name: agent.fullName, role: agent.role },
      campaign: {
        id: campaign.id,
        code: campaign.code,
        status: campaign.status,
        open_at: campaign.openAt,
        close_at: campaign.closeAt,
        open: isCampaignOpen(campaign),
      },
      warehouses: warehouses.map((w) => ({
        id: w.id,
        whs_code: w.whsCode,
        name: w.name,
        city: w.city,
      })),
    });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
