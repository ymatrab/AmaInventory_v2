import { useEffect, useState } from "react";
import { getHealth } from "./lib/api";

// DESIGN-SLOT: replace this placeholder shell with the user's design-system layout.
export function App() {
  const [apiStatus, setApiStatus] = useState<string>("checking…");

  useEffect(() => {
    getHealth()
      .then((h) => setApiStatus(h.status))
      .catch(() => setApiStatus("unreachable"));
  }, []);

  return (
    <main
      style={{
        maxWidth: 640,
        margin: "0 auto",
        padding: "var(--space-6)",
      }}
    >
      <h1 style={{ color: "var(--color-brand)" }}>Gestion — Inventory Platform</h1>
      <p style={{ color: "var(--color-text-muted)" }}>
        Internal app (Inventory Responsible · Audit · CDG). Phase 0 scaffold.
      </p>
      <p>
        Backend API status: <strong>{apiStatus}</strong>
      </p>
    </main>
  );
}
