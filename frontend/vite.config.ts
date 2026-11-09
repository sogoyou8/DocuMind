import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const backend = process.env.DOCUMIND_PROXY_TARGET || "http://127.0.0.1:8001";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    allowedHosts: ["web"],
    proxy: {
      "/api": { target: backend, changeOrigin: false, secure: false },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
  },
});
