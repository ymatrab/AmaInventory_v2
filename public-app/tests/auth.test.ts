import bcrypt from "bcryptjs";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { verifyPin } from "../lib/pin";
import { signSession, verifySession } from "../lib/session-crypto";

describe("session-crypto", () => {
  beforeEach(() => {
    process.env.SESSION_SECRET = "s3cr3t";
  });
  afterEach(() => {
    delete process.env.SESSION_SECRET;
  });

  it("round-trips a signed session", () => {
    const token = signSession({ agentId: "AG-1", campaignId: "1" });
    expect(verifySession(token)).toEqual({ agentId: "AG-1", campaignId: "1" });
  });

  it("rejects a tampered token", () => {
    const token = signSession({ agentId: "AG-1", campaignId: "1" });
    expect(verifySession(`${token}x`)).toBeNull();
    expect(verifySession("garbage")).toBeNull();
    expect(verifySession(undefined)).toBeNull();
  });

  it("rejects a token signed with a different secret", () => {
    const token = signSession({ agentId: "AG-1", campaignId: "1" });
    process.env.SESSION_SECRET = "other-secret";
    expect(verifySession(token)).toBeNull();
  });
});

describe("verifyPin", () => {
  it("matches a bcrypt hash and rejects a wrong PIN", async () => {
    const hash = bcrypt.hashSync("1234", 10);
    expect(await verifyPin("1234", hash)).toBe(true);
    expect(await verifyPin("0000", hash)).toBe(false);
  });
});
