import { NextRequest, NextResponse } from "next/server";

import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { verifySyncAuth } from "@/lib/sync-auth";
import { syncAgentsSchema } from "@/lib/sync-validation";

// POST /api/sync/agents — gestion upserts agents + their per-campaign credentials.
// Only the PIN hash is received here (never plaintext); no stock data.
export async function POST(req: NextRequest) {
  try {
    const raw = await req.text();
    verifySyncAuth(req.headers, raw);
    const agents = syncAgentsSchema.parse(JSON.parse(raw));

    for (const a of agents) {
      await prisma.agent.upsert({
        where: { id: a.agent_id },
        update: { fullName: a.full_name, role: a.role },
        create: { id: a.agent_id, fullName: a.full_name, role: a.role },
      });
      const cred = {
        token: a.token,
        pinHash: a.pin_hash,
        expiresAt: a.expires_at ? new Date(a.expires_at) : null,
        active: true,
      };
      await prisma.agentCredential.upsert({
        where: { agentId_campaignId: { agentId: a.agent_id, campaignId: a.campaign_id } },
        update: cred,
        create: { agentId: a.agent_id, campaignId: a.campaign_id, ...cred },
      });
    }
    return NextResponse.json({ ok: true, count: agents.length });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
