import { createHmac } from "node:crypto";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { ApiError } from "../lib/errors";
import { verifySyncAuth } from "../lib/sync-auth";

const TOKEN = "test-token";
const SECRET = "test-secret";

function headers(body: string, overrides: Record<string, string> = {}): Headers {
  const ts = Math.floor(Date.now() / 1000).toString();
  const sig = createHmac("sha256", SECRET).update(body).digest("hex");
  return new Headers({
    authorization: `Bearer ${TOKEN}`,
    "x-timestamp": ts,
    "x-signature": sig,
    ...overrides,
  });
}

describe("verifySyncAuth", () => {
  beforeEach(() => {
    process.env.SYNC_SERVICE_TOKEN = TOKEN;
    process.env.SYNC_HMAC_SECRET = SECRET;
  });
  afterEach(() => {
    delete process.env.SYNC_SERVICE_TOKEN;
    delete process.env.SYNC_HMAC_SECRET;
  });

  it("accepts a correctly signed request", () => {
    const body = '{"id":"1"}';
    expect(() => verifySyncAuth(headers(body), body)).not.toThrow();
  });

  it("rejects a wrong token", () => {
    const body = "{}";
    expect(() => verifySyncAuth(headers(body, { authorization: "Bearer nope" }), body)).toThrow(
      ApiError,
    );
  });

  it("rejects a tampered body (signature mismatch)", () => {
    const body = '{"id":"1"}';
    const h = headers(body);
    expect(() => verifySyncAuth(h, '{"id":"2"}')).toThrow(ApiError);
  });

  it("rejects a stale timestamp", () => {
    const body = "{}";
    const old = (Math.floor(Date.now() / 1000) - 600).toString();
    expect(() => verifySyncAuth(headers(body, { "x-timestamp": old }), body)).toThrow(ApiError);
  });
});
