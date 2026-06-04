import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

import { prisma } from "@/lib/db";
import { ApiError, errorResponse } from "@/lib/http";
import { verifyPin } from "@/lib/pin";
import { SESSION_COOKIE, SESSION_MAX_AGE_SECONDS, signSession } from "@/lib/session";
import { isCampaignOpen } from "@/lib/window";

const loginSchema = z.object({ token: z.string().min(1), pin: z.string().min(1) });
const MAX_ATTEMPTS = Number(process.env.LOGIN_MAX_PIN_ATTEMPTS ?? 5);

// POST /api/auth/login {token, pin}
// Validates token + PIN + campaign window; locks out after N failures.
// On success sets a signed, httpOnly session cookie scoped to (agent, campaign).
export async function POST(req: NextRequest) {
  try {
    const { token, pin } = loginSchema.parse(await req.json());

    const cred = await prisma.agentCredential.findUnique({
      where: { token },
      include: { campaign: true, agent: true },
    });
    if (!cred || !cred.active) {
      throw new ApiError(401, "invalid_login", "Invalid link or PIN.");
    }
    if (cred.expiresAt && new Date() > cred.expiresAt) {
      throw new ApiError(401, "expired", "This login has expired.");
    }
    if (
      !isCampaignOpen({
        status: cred.campaign.status,
        openAt: cred.campaign.openAt,
        closeAt: cred.campaign.closeAt,
      })
    ) {
      throw new ApiError(423, "campaign_closed", "No active campaign window.");
    }
    if (cred.failedAttempts >= MAX_ATTEMPTS) {
      throw new ApiError(429, "locked", "Too many attempts. Ask CDG to reset your PIN.");
    }

    const ok = await verifyPin(pin, cred.pinHash);
    if (!ok) {
      const updated = await prisma.agentCredential.update({
        where: { token },
        data: { failedAttempts: { increment: 1 } },
      });
      const remaining = Math.max(0, MAX_ATTEMPTS - updated.failedAttempts);
      throw new ApiError(401, "invalid_login", `Invalid PIN. ${remaining} attempt(s) left.`);
    }

    if (cred.failedAttempts > 0) {
      await prisma.agentCredential.update({ where: { token }, data: { failedAttempts: 0 } });
    }

    const res = NextResponse.json({
      ok: true,
      agent: { id: cred.agent.id, full_name: cred.agent.fullName, role: cred.agent.role },
      campaign_id: cred.campaignId,
    });
    res.cookies.set(
      SESSION_COOKIE,
      signSession({ agentId: cred.agentId, campaignId: cred.campaignId }),
      {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/",
        maxAge: SESSION_MAX_AGE_SECONDS,
      },
    );
    return res;
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
