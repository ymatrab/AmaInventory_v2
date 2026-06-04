import { Shell } from "@/components/Shell";

// Login (magic link + PIN). Phase 3 stub — the form is wired in Phase 5.
// DESIGN-SLOT: per-agent login screen (identity prefilled from link + PIN entry).
export default function LoginPage() {
  return (
    <Shell title="Sign in">
      <p style={{ color: "var(--color-text-muted)" }}>
        Open your personal counting link, then enter your PIN.
      </p>
      <form style={{ display: "grid", gap: "var(--space-3)", maxWidth: 280 }}>
        <label style={{ display: "grid", gap: "var(--space-1)" }}>
          <span>PIN</span>
          <input
            name="pin"
            inputMode="numeric"
            disabled
            placeholder="enabled in Phase 5"
            style={{ padding: "var(--space-2)", borderRadius: "var(--radius-sm)" }}
          />
        </label>
        <button
          type="button"
          disabled
          style={{
            padding: "var(--space-2)",
            background: "var(--color-brand)",
            color: "var(--color-brand-contrast)",
            border: "none",
            borderRadius: "var(--radius-sm)",
          }}
        >
          Sign in
        </button>
      </form>
    </Shell>
  );
}
