import { useCallback, useEffect, useState } from "react";

import { api, type Campaign, type CsvExport, type Me, type Reconciliation } from "../../lib/api";
import { Badge, Button, Card, ErrorText, Input, Table, td } from "../../components/ui";

export function ReconciliationPanel({ campaign, me }: { campaign: Campaign; me: Me | null }) {
  const [recons, setRecons] = useState<Reconciliation[]>([]);
  const [exports, setExports] = useState<CsvExport[]>([]);
  const [whs, setWhs] = useState<number | "">(campaign.warehouses[0]?.id ?? "");
  const [margin, setMargin] = useState("0");
  const [flagged, setFlagged] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const canRecon = !!me && me.is_cdg;
  const current = recons.find((r) => r.warehouse === whs);

  const reload = useCallback(() => {
    api
      .reconciliations(campaign.id)
      .then(setRecons)
      .catch(() => setRecons([]));
    api
      .exports(campaign.id)
      .then(setExports)
      .catch(() => setExports([]));
  }, [campaign.id]);

  useEffect(reload, [reload]);

  async function guard(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  }

  const sel = {
    padding: "var(--space-2)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
  };
  return (
    <div style={{ display: "grid", gap: "var(--space-4)" }}>
      <Card>
        <div
          style={{ display: "flex", gap: "var(--space-2)", alignItems: "center", flexWrap: "wrap" }}
        >
          <select value={whs} onChange={(e) => setWhs(Number(e.target.value))} style={sel}>
            {campaign.warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.whs_code}
              </option>
            ))}
          </select>
          <Button
            disabled={!canRecon || !whs}
            onClick={() => guard(() => api.buildRecon(campaign.id, Number(whs)))}
          >
            Build / refresh gaps
          </Button>
          <span style={{ marginLeft: "var(--space-3)" }}>Margin (per WHS):</span>
          <Input value={margin} onChange={(e) => setMargin(e.target.value)} style={{ width: 90 }} />
          <Button
            disabled={!canRecon || !whs}
            onClick={() => guard(() => api.setMargin(campaign.id, Number(whs), margin))}
          >
            Set margin
          </Button>
          {current && <Badge>current margin: {current.value_margin}</Badge>}
        </div>
        <ErrorText>{error}</ErrorText>
      </Card>

      {current && (
        <Card>
          <Table
            head={["Flag", "Item", "Physical", "System", "Gap qty", "Gap value", "Within margin"]}
          >
            {current.lines.map((l) => (
              <tr
                key={l.id}
                style={{ background: l.within_margin ? undefined : "rgba(192,57,43,0.08)" }}
              >
                <td style={td}>
                  <input
                    type="checkbox"
                    checked={!!flagged[l.item_code]}
                    onChange={(e) => setFlagged({ ...flagged, [l.item_code]: e.target.checked })}
                  />
                </td>
                <td style={td}>
                  {l.item_code}/{l.sku}
                </td>
                <td style={td}>{l.physical_qty}</td>
                <td style={td}>{l.system_qty}</td>
                <td style={td}>{l.gap_qty}</td>
                <td style={td}>{l.gap_value}</td>
                <td style={td}>{l.within_margin ? "✓" : <Badge>out</Badge>}</td>
              </tr>
            ))}
          </Table>
          <div style={{ marginTop: "var(--space-3)", display: "flex", gap: "var(--space-2)" }}>
            <Button
              variant="primary"
              disabled={!canRecon || Object.values(flagged).every((v) => !v)}
              onClick={() =>
                guard(() =>
                  api.flagRecount(
                    campaign.id,
                    Number(whs),
                    Object.keys(flagged).filter((k) => flagged[k]),
                  ),
                )
              }
            >
              Flag selected for re-count
            </Button>
            <Button
              disabled={!canRecon}
              onClick={() => guard(() => api.generateExport(campaign.id, Number(whs)))}
            >
              Generate CSV (this WHS)
            </Button>
            <Button
              disabled={!canRecon}
              onClick={() => guard(() => api.generateExport(campaign.id))}
            >
              Generate CSV (all)
            </Button>
          </div>
        </Card>
      )}

      <Card>
        <h3 style={{ marginTop: 0 }}>CSV exports</h3>
        <Table head={["Generated", "Scope", "Download"]}>
          {exports.map((e) => (
            <tr key={e.id}>
              <td style={td}>{new Date(e.generated_at).toLocaleString()}</td>
              <td style={td}>{e.whs_code ?? "all"}</td>
              <td style={td}>
                <a href={api.downloadExportUrl(e.id)}>download</a>
              </td>
            </tr>
          ))}
          {exports.length === 0 && (
            <tr>
              <td style={td} colSpan={3}>
                No exports yet.
              </td>
            </tr>
          )}
        </Table>
      </Card>
    </div>
  );
}
