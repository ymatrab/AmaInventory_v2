import { createHmac, timingSafeEqual } from "node:crypto";

import { ApiError } from "./errors";

// M2M auth for the sync endpoints (Appendix B header):
//   Authorization: Bearer <SYNC_SERVICE_TOKEN>
//   X-Timestamp:   <unix seconds>
//   X-Signature:   hmac_sha256(rawBody, SYNC_HMAC_SECRET)  (hex)
// Reject if the token is wrong, the timestamp skew > 5 min, or the signature
// is invalid. Only the gestion backend ever calls these (outbound-only).
const MAX_SKEW_SECONDS = 5 * 60;

function safeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ab.length !== bb.length) return false;
  return timingSafeEqual(ab, bb);
}

export function verifySyncAuth(headers: Headers, rawBody: string): void {
  const token = process.env.SYNC_SERVICE_TOKEN;
  const secret = process.env.SYNC_HMAC_SECRET;
  if (!token || !secret) {
    throw new ApiError(500, "sync_not_configured", "Sync secrets are not configured.");
  }

  const auth = headers.get("authorization") ?? "";
  const provided = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!safeEqual(provided, token)) {
    throw new ApiError(401, "bad_token", "Invalid service token.");
  }

  const tsRaw = headers.get("x-timestamp") ?? "";
  const ts = Number(tsRaw);
  if (!Number.isFinite(ts) || Math.abs(Date.now() / 1000 - ts) > MAX_SKEW_SECONDS) {
    throw new ApiError(401, "stale_timestamp", "Timestamp missing or outside the allowed window.");
  }

  const signature = headers.get("x-signature") ?? "";
  const expected = createHmac("sha256", secret).update(rawBody).digest("hex");
  if (!safeEqual(signature, expected)) {
    throw new ApiError(401, "bad_signature", "Invalid request signature.");
  }
}
