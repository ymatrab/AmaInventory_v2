import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

// The shared @ama/tokens package lives at the repo root (../../packages),
// outside this Vite project root, so allow serving from there.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5174,
    fs: { allow: [resolve(__dirname, "../..")] },
  },
});
