import { cookies } from "next/headers";

import { ApiError } from "./http";

// Per-agent session. Phase 3 skeleton: the cookie carries {agentId, campaignId}
// as JSON. Phase 5 replaces this with a signed/verified token issued at login
// (link + PIN); the AgentSession shape and the helpers below stay the same.
export const SESSION_COOKIE = "ama_session";

export interface AgentSession {
  agentId: string;
  campaignId: string;
}

export function parseSession(raw: string | undefined): AgentSession | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<AgentSession>;
    if (typeof parsed.agentId === "string" && typeof parsed.campaignId === "string") {
      return { agentId: parsed.agentId, campaignId: parsed.campaignId };
    }
  } catch {
    // fall through
  }
  return null;
}

export function getSession(): AgentSession | null {
  return parseSession(cookies().get(SESSION_COOKIE)?.value);
}

export function requireSession(): AgentSession {
  const session = getSession();
  if (!session) {
    throw new ApiError(401, "not_authenticated", "No agent session.");
  }
  return session;
}
