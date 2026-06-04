// DESIGN-SLOT: app shell + role-aware navigation. Nav items hide based on the
// signed-in user's groups (Inventory Responsible / Audit / CDG).
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../lib/auth";
import { Badge, Button } from "./ui";

const linkStyle = ({ isActive }: { isActive: boolean }) => ({
  display: "block",
  padding: "var(--space-2) var(--space-3)",
  borderRadius: "var(--radius-sm)",
  color: isActive ? "var(--color-brand-contrast)" : "var(--color-text)",
  background: isActive ? "var(--color-brand)" : "transparent",
  textDecoration: "none",
});

export function Shell() {
  const { me, logout } = useAuth();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 220,
          background: "var(--color-surface)",
          borderRight: "1px solid var(--color-border)",
          padding: "var(--space-4)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-2)",
        }}
      >
        <h1 style={{ color: "var(--color-brand)", fontSize: 18, margin: "0 0 var(--space-3)" }}>
          Gestion
        </h1>
        <NavLink to="/campaigns" style={linkStyle}>
          Campaigns
        </NavLink>
        <NavLink to="/history" style={linkStyle}>
          History / Archive
        </NavLink>
        <NavLink to="/analysis" style={linkStyle}>
          Analysis
        </NavLink>

        <div style={{ marginTop: "auto", fontSize: 13, color: "var(--color-text-muted)" }}>
          {me && (
            <>
              <div style={{ marginBottom: "var(--space-2)" }}>
                {me.username} <Badge>{me.groups.join(", ") || "—"}</Badge>
              </div>
              <Button onClick={() => logout()}>Sign out</Button>
            </>
          )}
        </div>
      </aside>

      <main style={{ flex: 1, padding: "var(--space-6)", maxWidth: 1100 }}>
        <Outlet />
      </main>
    </div>
  );
}
