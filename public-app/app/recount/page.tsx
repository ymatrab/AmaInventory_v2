"use client";

import { useEffect, useState } from "react";

import { CountTable, type RowItem } from "@/components/CountTable";
import { Shell } from "@/components/Shell";
import { api, type CountLineDTO } from "@/lib/client";

export default function RecountPage() {
  const [warehouseId, setWarehouseId] = useState<string | null>(null);
  const [items, setItems] = useState<RowItem[]>([]);
  const [lines, setLines] = useState<CountLineDTO[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api
      .recount()
      .then((d) => {
        setLines(d.lines);
        setItems(d.lines.map((l) => ({ item_code: l.item_code, sku: l.sku })));
        if (d.lines[0]) setWarehouseId(d.lines[0].warehouse_id);
        setReady(true);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <Shell title="Re-count">{error}</Shell>;
  if (!ready) return <Shell title="Re-count">Loading…</Shell>;
  if (lines.length === 0) return <Shell title="Re-count">No items flagged for re-count.</Shell>;

  return (
    <Shell title="Re-count">
      <p style={{ color: "var(--color-text-muted)" }}>
        Only items flagged by CDG are shown (highlighted). Re-enter quantities and Save.
      </p>
      <CountTable warehouseId={warehouseId ?? ""} items={items} initialLines={lines} />
    </Shell>
  );
}
