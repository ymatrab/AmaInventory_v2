import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api, type Campaign } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Badge, Section } from "../components/ui";
import { AssignmentPanel } from "./panels/AssignmentPanel";
import { LifecyclePanel } from "./panels/LifecyclePanel";
import { MonitorPanel } from "./panels/MonitorPanel";
import { ReconciliationPanel } from "./panels/ReconciliationPanel";
import { SignoffPanel } from "./panels/SignoffPanel";
import { KpiPanel } from "./panels/KpiPanel";

const TABS = [
  "Lifecycle",
  "Assignment",
  "Live counts",
  "Reconciliation",
  "Sign-off",
  "Agent KPI",
] as const;
type Tab = (typeof TABS)[number];

export function CampaignDetail() {
  const { id } = useParams();
  const campaignId = Number(id);
  const { me } = useAuth();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [tab, setTab] = useState<Tab>("Lifecycle");

  const reload = useCallback(() => {
    api
      .campaign(campaignId)
      .then(setCampaign)
      .catch(() => setCampaign(null));
  }, [campaignId]);

  useEffect(reload, [reload]);

  if (!campaign) return <p>Loading…</p>;

  const tabBtn = (t: Tab) => ({
    padding: "var(--space-2) var(--space-3)",
    cursor: "pointer",
    border: "none",
    borderBottom: tab === t ? "2px solid var(--color-brand)" : "2px solid transparent",
    background: "transparent",
    color: tab === t ? "var(--color-brand)" : "var(--color-text-muted)",
    fontWeight: tab === t ? 600 : 400,
  });

  return (
    <Section title={`Campaign ${campaign.code}`} actions={<Badge>{campaign.status_display}</Badge>}>
      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          borderBottom: "1px solid var(--color-border)",
          marginBottom: "var(--space-4)",
        }}
      >
        {TABS.map((t) => (
          <button key={t} style={tabBtn(t)} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {tab === "Lifecycle" && <LifecyclePanel campaign={campaign} me={me} onChange={reload} />}
      {tab === "Assignment" && <AssignmentPanel campaign={campaign} me={me} />}
      {tab === "Live counts" && <MonitorPanel campaign={campaign} />}
      {tab === "Reconciliation" && <ReconciliationPanel campaign={campaign} me={me} />}
      {tab === "Sign-off" && <SignoffPanel campaign={campaign} />}
      {tab === "Agent KPI" && <KpiPanel campaign={campaign} />}
    </Section>
  );
}
