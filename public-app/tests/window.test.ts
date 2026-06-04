import { describe, expect, it } from "vitest";

import { ApiError } from "../lib/errors";
import { countSubmitSchema } from "../lib/validation";
import { assertCampaignOpen, isCampaignOpen } from "../lib/window";

const now = new Date("2026-06-03T12:00:00Z");
const past = new Date("2026-06-01T00:00:00Z");
const future = new Date("2026-06-10T00:00:00Z");

describe("isCampaignOpen", () => {
  it("is open when status OPEN and within window", () => {
    expect(isCampaignOpen({ status: "OPEN", openAt: past, closeAt: future }, now)).toBe(true);
  });

  it("is open during RECOUNT", () => {
    expect(isCampaignOpen({ status: "RECOUNT", openAt: past, closeAt: future }, now)).toBe(true);
  });

  it("is closed for non-open statuses", () => {
    for (const status of ["DRAFT", "ARMED", "CLOSED", "ARCHIVED"]) {
      expect(isCampaignOpen({ status, openAt: past, closeAt: future }, now)).toBe(false);
    }
  });

  it("is closed before open_at and after close_at", () => {
    expect(isCampaignOpen({ status: "OPEN", openAt: future, closeAt: null }, now)).toBe(false);
    expect(isCampaignOpen({ status: "OPEN", openAt: null, closeAt: past }, now)).toBe(false);
  });

  it("open with null bounds when status OPEN", () => {
    expect(isCampaignOpen({ status: "OPEN", openAt: null, closeAt: null }, now)).toBe(true);
  });
});

describe("assertCampaignOpen", () => {
  it("throws 423 when closed", () => {
    try {
      assertCampaignOpen({ status: "CLOSED", openAt: past, closeAt: future }, now);
      throw new Error("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(423);
      expect((err as ApiError).code).toBe("campaign_closed");
    }
  });

  it("does not throw when open", () => {
    expect(() =>
      assertCampaignOpen({ status: "OPEN", openAt: past, closeAt: future }, now),
    ).not.toThrow();
  });
});

describe("countSubmitSchema", () => {
  it("accepts a valid create body and coerces qty", () => {
    const parsed = countSubmitSchema.parse({
      warehouse_id: "wh-1",
      item_code: "ITM-001",
      sku: "ITM-001-RED",
      qty_units: "5",
      qty_packs: 2,
    });
    expect(parsed.qty_units).toBe(5);
    expect(parsed.qty_packs).toBe(2);
    expect(parsed.line_uid).toBeUndefined();
  });

  it("rejects negative quantities", () => {
    expect(() =>
      countSubmitSchema.parse({ warehouse_id: "w", item_code: "i", qty_units: -1 }),
    ).toThrow();
  });

  it("rejects missing item_code", () => {
    expect(() => countSubmitSchema.parse({ warehouse_id: "w" })).toThrow();
  });
});
