import { NextRequest, NextResponse } from "next/server";

import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { verifySyncAuth } from "@/lib/sync-auth";
import { syncRecountSchema } from "@/lib/sync-validation";

// POST /api/sync/recount — gestion flags lines for re-count (by line_uid or item_code).
// Flagged lines surface to the agent via /api/recount.
export async function POST(req: NextRequest) {
  try {
    const raw = await req.text();
    verifySyncAuth(req.headers, raw);
    const body = syncRecountSchema.parse(JSON.parse(raw));

    const where = body.line_uids?.length
      ? { campaignId: body.campaign_id, lineUid: { in: body.line_uids } }
      : { campaignId: body.campaign_id, itemCode: { in: body.item_codes ?? [] } };

    const result = await prisma.countLine.updateMany({ where, data: { flagged: true } });
    return NextResponse.json({ ok: true, flagged: result.count });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
