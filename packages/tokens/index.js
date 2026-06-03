/**
 * Design tokens as a JS object (mirrors tokens.css custom properties).
 * PLACEHOLDER — replaced by the user's brand system later.
 * Import the CSS for runtime variables; import this object when you need
 * token values in JS (e.g. charts). Keep both in sync.
 */
export const tokens = {
  color: {
    brand: "#1f4e79",
    brandContrast: "#ffffff",
    accent: "#2e8b57",
    bg: "#f7f8fa",
    surface: "#ffffff",
    border: "#e2e5ea",
    text: "#1a1d21",
    textMuted: "#5b6470",
    success: "#2e8b57",
    warning: "#c8862b",
    danger: "#c0392b",
  },
  space: { 1: "4px", 2: "8px", 3: "12px", 4: "16px", 5: "24px", 6: "32px" },
  radius: { sm: "4px", md: "8px" },
  font: {
    sans: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    sizeBase: "16px",
    lineHeightBase: 1.5,
  },
};

export default tokens;
