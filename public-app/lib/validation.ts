import { z } from "zod";

// Input validation for field API routes (CLAUDE.md §7: zod on public routes).

export const countSubmitSchema = z.object({
  line_uid: z.string().uuid().optional(),
  warehouse_id: z.string().min(1),
  item_code: z.string().min(1),
  sku: z.string().min(1),
  qty_units: z.coerce.number().nonnegative().default(0),
  qty_packs: z.coerce.number().nonnegative().default(0),
});

export type CountSubmit = z.infer<typeof countSubmitSchema>;
