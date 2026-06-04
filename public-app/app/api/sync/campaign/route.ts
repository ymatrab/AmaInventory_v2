import { NextRequest, NextResponse } from "next/server";

import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { verifySyncAuth } from "@/lib/sync-auth";
import { syncCampaignSchema } from "@/lib/sync-validation";

// POST /api/sync/campaign — gestion upserts the campaign window + status.
export async function POST(req: NextRequest) {
  try {
    const raw = await req.text();
    verifySyncAuth(req.headers, raw);
    const c = syncCampaignSchema.parse(JSON.parse(raw));

    const data = {
      code: c.code,
      status: c.status,
      openAt: c.open_at ? new Date(c.open_at) : null,
      closeAt: c.close_at ? new Date(c.close_at) : null,
    };
    await prisma.campaign.upsert({
      where: { id: c.id },
      update: data,
      create: { id: c.id, ...data },
    });
    return NextResponse.json({ ok: true, id: c.id });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
