import { z } from "zod";

// Payload schemas for the gestion -> public sync push (Appendix B.1).
const status = z.enum(["DRAFT", "ARMED", "OPEN", "RECOUNT", "CLOSED", "ARCHIVED"]);
const role = z.enum(["AGENT", "WAREHOUSEMAN"]);

export const syncCampaignSchema = z.object({
  id: z.string().min(1),
  code: z.string().min(1),
  status,
  open_at: z.string().datetime({ offset: true }).nullable().optional(),
  close_at: z.string().datetime({ offset: true }).nullable().optional(),
});

export const syncWarehousesSchema = z.array(
  z.object({
    id: z.string().min(1),
    whs_code: z.string().min(1),
    name: z.string(),
    city: z.string().default(""),
    campaign_id: z.string().min(1),
  }),
);

export const syncItemsSchema = z.array(
  z.object({
    item_code: z.string().min(1),
    sku: z.string().min(1),
    description: z.string().default(""),
    color_parfum: z.string().default(""),
    base_unit: z.string().default("unit"),
    units_per_pack: z.number().int().positive().default(1),
    campaign_id: z.string().min(1),
  }),
);

export const syncAgentsSchema = z.array(
  z.object({
    agent_id: z.string().min(1),
    full_name: z.string(),
    role,
    token: z.string().min(1),
    pin_hash: z.string().min(1),
    campaign_id: z.string().min(1),
    expires_at: z.string().datetime({ offset: true }).nullable().optional(),
  }),
);

export const syncRecountSchema = z
  .object({
    campaign_id: z.string().min(1),
    line_uids: z.array(z.string().uuid()).optional(),
    item_codes: z.array(z.string()).optional(),
  })
  .refine((v) => (v.line_uids?.length ?? 0) > 0 || (v.item_codes?.length ?? 0) > 0, {
    message: "Provide line_uids or item_codes.",
  });
