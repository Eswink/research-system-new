import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 工程版本唯一来源：仓库根 VERSION（不走设计稿的 protocol_version）；
// 构建上下文缺失该文件时回退 "dev"（不阻断构建）。
const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
const versionFile = `${repoRoot}VERSION`;
const appVersion = existsSync(versionFile)
  ? readFileSync(versionFile, "utf-8").trim()
  : "dev";

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
    // 0.0.0.0：TUN 严格路由模式下 loopback 地址被隧道接管，前端需绑定
    // 全接口以便通过本机实际网卡/TUN 虚拟地址访问。
    host: "0.0.0.0",
    port: 5173,
    proxy: apiProxy,
  },
  preview: {
    host: "0.0.0.0",
    port: 5173,
    proxy: apiProxy,
  },
});
