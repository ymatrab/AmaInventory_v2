import { useEffect, useState } from "react";

import { api, type Campaign } from "../../lib/api";
import { Button, Card, Table, td } from "../../components/ui";

interface Row {
  whs_code: string;
  lines: number;
  flagged: number;
  last_update: string;
}

export function MonitorPanel({ campaign }: { campaign: Campaign }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  function reload() {
    api
      .monitor(campaign.id)
      .then((r) => setRows(r.warehouses))
      .catch(() => setRows([]));
  }

  useEffect(reload, [campaign.id]);

  async function sync() {
    const r = await api.syncNow(campaign.id);
    setMsg(`Pulled ${r.rows} line(s).`);
    reload();
  }

  return (
    <Card>
      <div
        style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-3)" }}
      >
        <span style={{ color: "var(--color-text-muted)" }}>
          Progress per warehouse (from pulled counts).
        </span>
        <Button onClick={sync}>Sync now</Button>
      </div>
      {msg && <p style={{ color: "var(--color-success)" }}>{msg}</p>}
      <Table head={["Warehouse", "Lines counted", "Flagged", "Last update"]}>
        {rows.map((r) => (
          <tr key={r.whs_code}>
            <td style={td}>{r.whs_code}</td>
            <td style={td}>{r.lines}</td>
            <td style={td}>{r.flagged}</td>
            <td style={td}>{r.last_update ? new Date(r.last_update).toLocaleString() : "—"}</td>
          </tr>
        ))}
        {rows.length === 0 && (
          <tr>
            <td style={td} colSpan={4}>
              No counts pulled yet.
            </td>
          </tr>
        )}
      </Table>
    </Card>
  );
}
