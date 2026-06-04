// DESIGN-SLOT: replace this shell with the user's design-system layout/header.
export function Shell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "var(--space-6)" }}>
      <h1 style={{ color: "var(--color-brand)", marginBottom: "var(--space-2)" }}>{title}</h1>
      {children}
    </main>
  );
}
