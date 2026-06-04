import { Shell } from "@/components/Shell";

// Count entry — item list + qty by unit/pack (interactive in Phase 5).
// DESIGN-SLOT: counting grid (item, color/parfum, qty unit/pack, add item).
export default function CountPage() {
  return (
    <Shell title="Count entry">
      <p style={{ color: "var(--color-text-muted)" }}>
        Enter counted quantities by unit or by pack. The item list loads from{" "}
        <code>/api/items</code> once signed in (Phase 5).
      </p>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid var(--color-border)" }}>
            <th style={{ padding: "var(--space-2)" }}>Item</th>
            <th style={{ padding: "var(--space-2)" }}>Color / Parfum</th>
            <th style={{ padding: "var(--space-2)" }}>Units</th>
            <th style={{ padding: "var(--space-2)" }}>Packs</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: "var(--space-2)", color: "var(--color-text-muted)" }} colSpan={4}>
              No items loaded.
            </td>
          </tr>
        </tbody>
      </table>
    </Shell>
  );
}
