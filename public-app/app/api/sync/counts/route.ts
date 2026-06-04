import { NextRequest, NextResponse } from "next/server";

import { serializeLine } from "@/lib/campaign";
import { prisma } from "@/lib/db";
import { ApiError, errorResponse } from "@/lib/http";
import { verifySyncAuth } from "@/lib/sync-auth";

// GET /api/sync/counts?campaign={id}&since={cursor}&limit={n}
// Returns count lines changed since the cursor, ordered by (updated_at, line_uid).
// Compound cursor "iso|line_uid" so rows sharing a timestamp are never skipped.
// Gestion upserts by line_uid + version, so re-fetching is harmless (idempotent).
export async function GET(req: NextRequest) {
  try {
    verifySyncAuth(req.headers, ""); // GET: no body
    const url = new URL(req.url);
    const campaignId = url.searchParams.get("campaign");
    if (!campaignId) {
      throw new ApiError(400, "missing_campaign", "campaign query param is required.");
    }
    const since = url.searchParams.get("since");
    const limit = Math.min(Math.max(Number(url.searchParams.get("limit")) || 200, 1), 500);

    let where: Record<string, unknown> = { campaignId };
    if (since) {
      const idx = since.lastIndexOf("|");
      const cursorTime = new Date(since.slice(0, idx));
      const cursorUid = since.slice(idx + 1);
      where = {
        campaignId,
        OR: [
          { updatedAt: { gt: cursorTime } },
          { updatedAt: cursorTime, lineUid: { gt: cursorUid } },
        ],
      };
    }

    const lines = await prisma.countLine.findMany({
      where,
      orderBy: [{ updatedAt: "asc" }, { lineUid: "asc" }],
      take: limit,
    });

    const last = lines.at(-1);
    const nextCursor = last ? `${last.updatedAt.toISOString()}|${last.lineUid}` : (since ?? null);

    return NextResponse.json({ lines: lines.map(serializeLine), next_cursor: nextCursor });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
