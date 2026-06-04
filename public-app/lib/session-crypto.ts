import { createHmac, timingSafeEqual } from "node:crypto";

import { ApiError } from "./errors";

// Signed per-agent session token: base64url(payload).base64url(hmac).
// Framework-free so it can be unit-tested without next/headers.
export interface AgentSession {
  agentId: string;
  campaignId: string;
}

function secret(): string {
  const s = process.env.SESSION_SECRET;
  if (!s) {
    throw new ApiError(500, "session_not_configured", "SESSION_SECRET is not set.");
  }
  return s;
}

function sign(payload: string): string {
  return createHmac("sha256", secret()).update(payload).digest("base64url");
}

export function signSession(session: AgentSession): string {
  const payload = Buffer.from(JSON.stringify(session)).toString("base64url");
  return `${payload}.${sign(payload)}`;
}

export function verifySession(value: string | undefined): AgentSession | null {
  if (!value) return null;
  const [payload, sig] = value.split(".");
  if (!payload || !sig) return null;

  const expected = sign(payload);
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;

  try {
    const obj = JSON.parse(Buffer.from(payload, "base64url").toString()) as Partial<AgentSession>;
    if (typeof obj.agentId === "string" && typeof obj.campaignId === "string") {
      return { agentId: obj.agentId, campaignId: obj.campaignId };
    }
  } catch {
    // fall through
  }
  return null;
}
