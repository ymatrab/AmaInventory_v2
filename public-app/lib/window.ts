import { ApiError } from "./errors";

// Campaign-window enforcement. Field counting is allowed only while the
// campaign is OPEN or RECOUNT and now is within [open_at, close_at].
export interface CampaignWindow {
  status: string;
  openAt: Date | null;
  closeAt: Date | null;
}

export function isCampaignOpen(c: CampaignWindow, now: Date = new Date()): boolean {
  if (c.status !== "OPEN" && c.status !== "RECOUNT") return false;
  if (c.openAt && now < c.openAt) return false;
  if (c.closeAt && now > c.closeAt) return false;
  return true;
}

// Throws 423 (Locked) when the window is not open.
export function assertCampaignOpen(c: CampaignWindow, now: Date = new Date()): void {
  if (!isCampaignOpen(c, now)) {
    throw new ApiError(423, "campaign_closed", "No active campaign window.");
  }
}
