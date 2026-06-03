export interface Tokens {
  color: {
    brand: string;
    brandContrast: string;
    accent: string;
    bg: string;
    surface: string;
    border: string;
    text: string;
    textMuted: string;
    success: string;
    warning: string;
    danger: string;
  };
  space: Record<1 | 2 | 3 | 4 | 5 | 6, string>;
  radius: { sm: string; md: string };
  font: { sans: string; sizeBase: string; lineHeightBase: number };
}

export declare const tokens: Tokens;
export default tokens;
