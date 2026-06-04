import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, type Warehouse } from "../lib/api";
import { Button, Card, ErrorText, Input, Section } from "../components/ui";

export function CreateCampaign() {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    code: "",
    type: "MONTHLY",
    trigger: "ROUTINE",
    scope: "ALL",
    open_at: "",
    close_at: "",
    warehouse_ids: [] as number[],
  });

  useEffect(() => {
    api
      .warehouses()
      .then(setWarehouses)
      .catch(() => setWarehouses([]));
  }, []);

  function toggle(id: number) {
    setForm((f) => ({
      ...f,
      warehouse_ids: f.warehouse_ids.includes(id)
        ? f.warehouse_ids.filter((x) => x !== id)
        : [...f.warehouse_ids, id],
    }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await api.createCampaign({
        code: form.code,
        type: form.type,
        trigger: form.trigger,
        scope: form.scope,
        open_at: form.open_at || null,
        close_at: form.close_at || null,
        warehouse_ids: form.warehouse_ids,
      });
      navigate(`/campaigns/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  const selectStyle = {
    padding: "var(--space-2)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
  };
  return (
    <Section title="New campaign">
      <Card style={{ maxWidth: 560 }}>
        <form
          onSubmit={submit}
          style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}
        >
          <label>
            Code
            <Input
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              style={{ width: "100%" }}
            />
          </label>
          <div style={{ display: "flex", gap: "var(--space-3)" }}>
            <label style={{ flex: 1 }}>
              Type
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                style={{ ...selectStyle, width: "100%" }}
              >
                <option value="MONTHLY">Monthly</option>
                <option value="PERIOD">Period / ad-hoc</option>
              </select>
            </label>
            <label style={{ flex: 1 }}>
              Trigger
              <select
                value={form.trigger}
                onChange={(e) => setForm({ ...form, trigger: e.target.value })}
                style={{ ...selectStyle, width: "100%" }}
              >
                <option value="ROUTINE">Routine</option>
                <option value="HIGH_GAP">High gap</option>
                <option value="ANOMALY">Anomaly</option>
              </select>
            </label>
          </div>
          <div style={{ display: "flex", gap: "var(--space-3)" }}>
            <label style={{ flex: 1 }}>
              Open at
              <Input
                type="datetime-local"
                value={form.open_at}
                onChange={(e) => setForm({ ...form, open_at: e.target.value })}
                style={{ width: "100%" }}
              />
            </label>
            <label style={{ flex: 1 }}>
              Close at
              <Input
                type="datetime-local"
                value={form.close_at}
                onChange={(e) => setForm({ ...form, close_at: e.target.value })}
                style={{ width: "100%" }}
              />
            </label>
          </div>
          <fieldset
            style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius-sm)" }}
          >
            <legend>Warehouses</legend>
            {warehouses.map((w) => (
              <label key={w.id} style={{ display: "block", padding: "var(--space-1)" }}>
                <input
                  type="checkbox"
                  checked={form.warehouse_ids.includes(w.id)}
                  onChange={() => toggle(w.id)}
                />{" "}
                {w.whs_code} — {w.name}
              </label>
            ))}
          </fieldset>
          <Button variant="primary" type="submit">
            Create campaign
          </Button>
          <ErrorText>{error}</ErrorText>
        </form>
      </Card>
    </Section>
  );
}
