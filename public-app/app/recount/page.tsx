import { Shell } from "@/components/Shell";

// Re-count — same as count but only flagged items (highlighted). Wired in Phase 5.
// DESIGN-SLOT: re-count grid with flagged items highlighted.
export default function RecountPage() {
  return (
    <Shell title="Re-count">
      <p style={{ color: "var(--color-text-muted)" }}>
        Only the items CDG flagged for re-count appear here, highlighted. Loaded from{" "}
        <code>/api/recount</code> (Phase 5).
      </p>
    </Shell>
  );
}
