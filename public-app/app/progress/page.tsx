import { Shell } from "@/components/Shell";

// Progress / submission status (wired in Phase 5).
// DESIGN-SLOT: progress + submission confirmation.
export default function ProgressPage() {
  return (
    <Shell title="Progress">
      <p style={{ color: "var(--color-text-muted)" }}>
        What is done and what is pending, from <code>/api/counts/mine</code> (Phase 5).
      </p>
    </Shell>
  );
}
