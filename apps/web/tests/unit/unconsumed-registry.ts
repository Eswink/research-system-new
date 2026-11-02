/**
 * 未消费路由登记表的**读取原语**（GOAL-20261103-104 EC-04）。
 *
 * 单列成非 `.test.ts` 模块：`backend-route-coverage.test.ts` 要用它，而
 * `unconsumed-registry.test.ts` 又要测「登记本身诚实」。若前者直接 import 后者，
 * 后者的 `test(...)` 会被**注册两次**（实测：两个文件里同名的
 * `the placeholder detector itself bites` 各自跑一遍并各自失败）。原语与判据分开，
 * 就像 `consoleFixtures.ts` 与用它的那组用例。
 *
 * **表格格式**（`docs/frontend/UNCONSUMED.md`）：
 *
 *     | 方法 | 路径 | 理由 |
 *     | --- | --- | --- |
 *     | GET | /health | 进程存活探针… |
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, "../../../..");
export const WHITELIST = path.join(ROOT, "docs/frontend/UNCONSUMED.md");
export const OPENAPI = path.join(ROOT, "docs/api/openapi.m13.json");

export interface Entry {
  method: string;
  path: string;
  reason: string;
}

const METHODS = new Set(["get", "post", "put", "patch", "delete"]);

/** 占位符理由：写着等于没写（前后空白先剪掉再判）。 */
export const PLACEHOLDER =
  /^(|[-—–]+|tbd|todo|n\/a|待补|暂无|略|无理由)$/i;

/** 理由是否为空/占位符（调用方不必自己 trim）。 */
export function isPlaceholder(reason: string): boolean {
  return PLACEHOLDER.test(reason.trim());
}

/** 从文档里读白名单（只认「第一列是大写 HTTP 方法」的数据行）。 */
export function readWhitelist(): Entry[] {
  const rows: Entry[] = [];
  for (const line of readFileSync(WHITELIST, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed.startsWith("|")) continue;
    const cells = trimmed
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim().replace(/`/g, ""));
    const [method, routePath, reason] = cells;
    if (method === undefined || routePath === undefined || reason === undefined) continue;
    if (!/^[A-Z]+$/.test(method) || !METHODS.has(method.toLowerCase())) continue;
    if (!routePath.startsWith("/")) continue;
    rows.push({ method, path: routePath, reason });
  }
  return rows;
}

/** OpenAPI 快照里的全部路由（方法 + 原样路径）。 */
export function openapiRoutes(): { method: string; path: string }[] {
  const doc = JSON.parse(readFileSync(OPENAPI, "utf8")) as {
    paths: Record<string, Record<string, unknown>>;
  };
  const routes: { method: string; path: string }[] = [];
  for (const [routePath, ops] of Object.entries(doc.paths)) {
    for (const method of Object.keys(ops)) {
      if (METHODS.has(method.toLowerCase())) {
        routes.push({ method: method.toUpperCase(), path: routePath });
      }
    }
  }
  return routes;
}
