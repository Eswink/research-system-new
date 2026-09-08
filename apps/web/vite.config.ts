import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 工程版本唯一来源：仓库根 VERSION（不走设计稿的 protocol_version）
const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
const appVersion = readFileSync(`${repoRoot}VERSION`, "utf-8").trim();

const apiProxyTarget =
  process.env.RESEARCHOS_API_PROXY_TARGET ?? "http://127.0.0.1:8000";
const apiProxy = {
  "/api": {
    target: apiProxyTarget,
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  preview: {
    port: 5173,
    proxy: apiProxy,
  },
});
