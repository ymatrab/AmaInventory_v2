"use client";

import { useState } from "react";

import { api, type CountLineDTO } from "@/lib/client";

export interface RowItem {
  item_code: string;
  sku: string;
  description?: string;
  color_parfum?: string;
}

function lineKey(itemCode: string, sku: string): string {
  return `${itemCode}|${sku}`;
}

function Row({
  item,
  warehouseId,
  line,
  onSaved,
}: {
  item: RowItem;
  warehouseId: string;
  line?: CountLineDTO;
  onSaved: (l: CountLineDTO) => void;
}) {
  const [units, setUnits] = useState(line ? String(line.qty_units) : "");
  const [packs, setPacks] = useState(line ? String(line.qty_packs) : "");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function save() {
    setBusy(true);
    setMsg(null);
    try {
      const res = await api.submit({
        line_uid: line?.line_uid,
        warehouse_id: warehouseId,
        item_code: item.item_code,
        sku: item.sku,
        qty_units: Number(units || 0),
        qty_packs: Number(packs || 0),
      });
      onSaved(res.line);
      setMsg(`saved v${res.line.version}`);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "save failed");
    } finally {
      setBusy(false);
    }
  }

  const cell = { padding: "var(--space-2)" } as const;
  return (
    <tr style={{ background: line?.flagged ? "rgba(200,134,43,0.15)" : undefined }}>
      <td style={cell}>
        {item.item_code}/{item.sku}
        {item.color_parfum ? ` · ${item.color_parfum}` : ""}
      </td>
      <td style={cell}>
        <input
          value={units}
          onChange={(e) => setUnits(e.target.value)}
          inputMode="decimal"
          style={{ width: 70 }}
        />
      </td>
      <td style={cell}>
        <input
          value={packs}
          onChange={(e) => setPacks(e.target.value)}
          inputMode="decimal"
          style={{ width: 70 }}
        />
      </td>
      <td style={cell}>
        <button type="button" onClick={save} disabled={busy}>
          {busy ? "…" : "Save"}
        </button>{" "}
        <span style={{ color: "var(--color-text-muted)" }}>{msg}</span>
      </td>
    </tr>
  );
}

export function CountTable({
  warehouseId,
  items,
  initialLines,
  allowAddItem = false,
}: {
  warehouseId: string;
  items: RowItem[];
  initialLines: CountLineDTO[];
  allowAddItem?: boolean;
}) {
  const [rows, setRows] = useState<RowItem[]>(items);
  const [lines, setLines] = useState<Record<string, CountLineDTO>>(() => {
    const m: Record<string, CountLineDTO> = {};
    for (const l of initialLines) m[lineKey(l.item_code, l.sku)] = l;
    return m;
  });
  const [newCode, setNewCode] = useState("");
  const [newSku, setNewSku] = useState("");

  function onSaved(l: CountLineDTO) {
    setLines((prev) => ({ ...prev, [lineKey(l.item_code, l.sku)]: l }));
  }

  function addItem(e: React.FormEvent) {
    e.preventDefault();
    if (!newCode || !newSku) return;
    if (!rows.some((r) => r.item_code === newCode && r.sku === newSku)) {
      setRows((prev) => [...prev, { item_code: newCode, sku: newSku }]);
    }
    setNewCode("");
    setNewSku("");
  }

  const head = { padding: "var(--space-2)", textAlign: "left" as const };
  return (
    <>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
            <th style={head}>Item</th>
            <th style={head}>Units</th>
            <th style={head}>Packs</th>
            <th style={head}></th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td
                style={{ padding: "var(--space-2)", color: "var(--color-text-muted)" }}
                colSpan={4}
              >
                No items.
              </td>
            </tr>
          )}
          {rows.map((item) => (
            <Row
              key={lineKey(item.item_code, item.sku)}
              item={item}
              warehouseId={warehouseId}
              line={lines[lineKey(item.item_code, item.sku)]}
              onSaved={onSaved}
            />
          ))}
        </tbody>
      </table>

      {allowAddItem && (
        <form
          onSubmit={addItem}
          style={{ marginTop: "var(--space-4)", display: "flex", gap: "var(--space-2)" }}
        >
          <input
            value={newCode}
            onChange={(e) => setNewCode(e.target.value)}
            placeholder="item code"
          />
          <input value={newSku} onChange={(e) => setNewSku(e.target.value)} placeholder="sku" />
          <button type="submit">Add item not in list</button>
        </form>
      )}
    </>
  );
}
