import { useState } from "react";

import { api, type Campaign, type Me } from "../../lib/api";
import { Button, Card, ErrorText, Input, Table, td } from "../../components/ui";

export function LifecyclePanel({
  campaign,
  me,
  onChange,
}: {
  campaign: Campaign;
  me: Me | null;
  onChange: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [creds, setCreds] = useState<{ matricule: string; pin: string; token: string }[]>([]);
  const [closeAt, setCloseAt] = useState("");

  const canManage = !!me && (me.is_audit || me.is_cdg || me.is_inventory_responsible);

  async function run(label: string, fn: () => Promise<unknown>) {
    setError(null);
    setMsg(null);
    try {
      await fn();
      setMsg(`${label} done.`);
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${label} failed`);
    }
  }

  return (
    <div style={{ display: "grid", gap: "var(--space-4)" }}>
      <Card>
        <p style={{ marginTop: 0 }}>
          Window: <strong>{campaign.open_at ?? "—"}</strong> →{" "}
          <strong>{campaign.close_at ?? "—"}</strong>
        </p>
        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
          <Button
            disabled={!canManage}
            onClick={() => run("Arm", () => api.armCampaign(campaign.id))}
          >
            Arm (snapshot SAP)
          </Button>
          <Button
            disabled={!canManage}
            onClick={() =>
              run("Generate credentials", async () => {
                const r = await api.genCredentials(campaign.id);
                setCreds(r.credentials);
              })
            }
          >
            Generate credentials
          </Button>
          <Button
            disabled={!canManage}
            onClick={() => run("Push setup", () => api.pushSetup(campaign.id))}
          >
            Push to public
          </Button>
          <Button
            variant="primary"
            disabled={!me?.is_audit && !me?.is_cdg}
            onClick={() => run("Open", () => api.openCampaign(campaign.id))}
          >
            Open
          </Button>
          <Button
            variant="danger"
            disabled={!me?.is_audit && !me?.is_cdg}
            onClick={() => run("Close", () => api.closeCampaign(campaign.id))}
          >
            Close (expire tokens)
          </Button>
          <Button onClick={() => run("Sync", () => api.syncNow(campaign.id))}>
            Sync now (pull)
          </Button>
        </div>
        <div
          style={{
            marginTop: "var(--space-3)",
            display: "flex",
            gap: "var(--space-2)",
            alignItems: "center",
          }}
        >
          <Input
            type="datetime-local"
            value={closeAt}
            onChange={(e) => setCloseAt(e.target.value)}
          />
          <Button
            disabled={(!me?.is_audit && !me?.is_cdg) || !closeAt}
            onClick={() =>
              run("Extend", () => api.extendCampaign(campaign.id, new Date(closeAt).toISOString()))
            }
          >
            Extend window
          </Button>
        </div>
        {msg && <p style={{ color: "var(--color-success)" }}>{msg}</p>}
        <ErrorText>{error}</ErrorText>
      </Card>

      {creds.length > 0 && (
        <Card>
          <h3 style={{ marginTop: 0 }}>Credentials (shown once — hand out securely)</h3>
          <Table head={["Matricule", "PIN", "Magic link"]}>
            {creds.map((c) => (
              <tr key={c.matricule}>
                <td style={td}>{c.matricule}</td>
                <td style={td}>{c.pin}</td>
                <td style={td}>
                  /c/{campaign.code}/a/{c.token}
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </div>
  );
}
