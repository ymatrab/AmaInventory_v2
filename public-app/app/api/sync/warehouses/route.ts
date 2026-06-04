import { NextRequest, NextResponse } from "next/server";

import { prisma } from "@/lib/db";
import { errorResponse } from "@/lib/http";
import { verifySyncAuth } from "@/lib/sync-auth";
import { syncWarehousesSchema } from "@/lib/sync-validation";

// POST /api/sync/warehouses — gestion upserts the campaign's warehouses.
export async function POST(req: NextRequest) {
  try {
    const raw = await req.text();
    verifySyncAuth(req.headers, raw);
    const warehouses = syncWarehousesSchema.parse(JSON.parse(raw));

    for (const w of warehouses) {
      const data = { whsCode: w.whs_code, name: w.name, city: w.city, campaignId: w.campaign_id };
      await prisma.warehouse.upsert({
        where: { id: w.id },
        update: data,
        create: { id: w.id, ...data },
      });
    }
    return NextResponse.json({ ok: true, count: warehouses.length });
  } catch (err) {
    return errorResponse(err);
  }
}

export const dynamic = "force-dynamic";
