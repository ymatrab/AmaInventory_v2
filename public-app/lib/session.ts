import { cookies } from "next/headers";

import { ApiError } from "./errors";
import { type AgentSession, signSession, verifySession } from "./session-crypto";

// Per-agent session, established at login (link + PIN) and carried in a signed,
// httpOnly cookie. Field routes call requireSession(); the shape is unchanged
// from the Phase 3 skeleton (only the cookie is now signed/verified).
export const SESSION_COOKIE = "ama_session";
export const SESSION_MAX_AGE_SECONDS = 12 * 60 * 60;

export type { AgentSession };
export { signSession };

export function getSession(): AgentSession | null {
  return verifySession(cookies().get(SESSION_COOKIE)?.value);
}

export function requireSession(): AgentSession {
  const session = getSession();
  if (!session) {
    throw new ApiError(401, "not_authenticated", "No agent session.");
  }
  return session;
}
