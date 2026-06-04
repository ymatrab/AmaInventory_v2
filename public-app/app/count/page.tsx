"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { CountTable, type RowItem } from "@/components/CountTable";
import { Shell } from "@/components/Shell";
import { api, type CountLineDTO } from "@/lib/client";

export default function CountPage() {
  const router = useRouter();
  const [warehouseId, setWarehouseId] = useState<string | null>(null);
  const [items, setItems] = useState<RowItem[]>([]);
  const [lines, setLines] = useState<CountLineDTO[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    Promise.all([api.me(), api.items(), api.mine()])
      .then(([me, itemsRes, mine]) => {
        if (me.warehouses[0]) setWarehouseId(me.warehouses[0].id);
        setItems(itemsRes.items);
        setLines(mine.lines.filter((l) => !l.is_recount));
        setReady(true);
      })
      .catch((e) => {
        setError(e.message);
        if (String(e.message).includes("session")) router.push("/login");
      });
  }, [router]);

  if (error) return <Shell title="Count entry">{error}</Shell>;
  if (!ready) return <Shell title="Count entry">Loading…</Shell>;
  if (!warehouseId) return <Shell title="Count entry">No warehouse assigned.</Shell>;

  return (
    <Shell title="Count entry">
      <p style={{ color: "var(--color-text-muted)" }}>
        Enter counted quantities by unit or by pack, then Save.
      </p>
      <CountTable warehouseId={warehouseId} items={items} initialLines={lines} allowAddItem />
    </Shell>
  );
}
