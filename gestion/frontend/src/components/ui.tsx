// DESIGN-SLOT: minimal, token-styled primitives. The user's design system can
// replace these wholesale — pages import from here, never hardcode styling.
import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";

export function Card({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-5)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function Section({
  title,
  actions,
  children,
}: {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section style={{ marginBottom: "var(--space-6)" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--space-3)",
        }}
      >
        <h2 style={{ margin: 0, fontSize: 18 }}>{title}</h2>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>{actions}</div>
      </div>
      {children}
    </section>
  );
}

type Variant = "primary" | "default" | "danger";
export function Button({
  variant = "default",
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const bg =
    variant === "primary"
      ? "var(--color-brand)"
      : variant === "danger"
        ? "var(--color-danger)"
        : "var(--color-surface)";
  const color = variant === "default" ? "var(--color-text)" : "var(--color-brand-contrast)";
  return (
    <button
      {...rest}
      style={{
        background: bg,
        color,
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-sm)",
        padding: "var(--space-2) var(--space-3)",
        cursor: rest.disabled ? "not-allowed" : "pointer",
        opacity: rest.disabled ? 0.6 : 1,
        ...rest.style,
      }}
    >
      {children}
    </button>
  );
}

export function Badge({ children }: { children: ReactNode }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px var(--space-2)",
        borderRadius: "var(--radius-sm)",
        background: "var(--color-bg)",
        border: "1px solid var(--color-border)",
        fontSize: 12,
        color: "var(--color-text-muted)",
      }}
    >
      {children}
    </span>
  );
}

export function Table({ head, children }: { head: ReactNode[]; children: ReactNode }) {
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
      <thead>
        <tr style={{ borderBottom: "1px solid var(--color-border)", textAlign: "left" }}>
          {head.map((h, i) => (
            <th key={i} style={{ padding: "var(--space-2)" }}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  );
}

export const td: CSSProperties = {
  padding: "var(--space-2)",
  borderBottom: "1px solid var(--color-border)",
};

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        padding: "var(--space-2)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-sm)",
        ...props.style,
      }}
    />
  );
}

export function ErrorText({ children }: { children: ReactNode }) {
  return children ? <p style={{ color: "var(--color-danger)" }}>{children}</p> : null;
}
