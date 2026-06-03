// DESIGN-SLOT: replace with the user's design-system landing / "no active campaign" screen.
export default function Home() {
  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "var(--space-6)" }}>
      <h1 style={{ color: "var(--color-brand)" }}>Inventory — Field App</h1>
      <p style={{ color: "var(--color-text-muted)" }}>
        Public app for field users (Agent · Warehouseman). Phase 0 scaffold.
      </p>
      <p>No active campaign. The app opens during a campaign window.</p>
    </main>
  );
}
