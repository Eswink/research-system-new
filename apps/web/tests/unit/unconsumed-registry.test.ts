/**
 * 白名单登记的**诚实性**判据（GOAL-20261103-104 EC-04）。
 *
 * 与 `backend-route-coverage.test.ts` 分工：那个文件守「每条路由有消费者或被登记」，
 * 这个文件守「登记本身可信」—— 理由非空、路径真的存在、不重复。读取原语在
 * `unconsumed-registry.ts`（非 `.test.ts`，否则 import 方会把这里的 `test(...)`
 * 注册第二遍）。
 *
 * **为什么这几条是判据而不是文档纪律**：「理由写清楚」这类要求如果没人查，就会退化成
 * 一排 `-`。本轮 `fix_policy.forbidden` 明写「不得用白名单刷覆盖率数字」，这里的
 * 占位符检测就是那条禁令的机械形态。
 */

import assert from "node:assert/strict";
import { test } from "node:test";

import { OPENAPI, isPlaceholder, openapiRoutes, readWhitelist } from "./unconsumed-registry";

test("the whitelist exists and is non-empty", () => {
  assert.ok(
    readWhitelist().length > 0,
    "白名单为空 ⇒ 「有消费者或被登记」在空集上靠不住",
  );
});

test("no whitelist entry has an empty or placeholder reason", () => {
  const bad = readWhitelist()
    .filter((entry) => isPlaceholder(entry.reason))
    .map((entry) => `${entry.method} ${entry.path}`);
  assert.deepEqual(bad, [], "这些条目的理由为空或只是占位符（= 没登记）");
});

test("the placeholder detector itself bites", () => {
  // 反证臂：判据不是空断言。
  for (const empty of ["", "  ", "-", "TODO", "TBD", "待补", "无理由"]) {
    assert.ok(isPlaceholder(empty), `占位符 ${JSON.stringify(empty)} 没有被识别`);
  }
  assert.ok(
    !isPlaceholder("服务端能力，前端暂不暴露：没有任务级故障处置交互"),
    "真理由被误判成占位符",
  );
});

test("every whitelisted route really exists in the OpenAPI snapshot", () => {
  assert.ok(OPENAPI.endsWith("openapi.m13.json"), "读的不是 OpenAPI 快照");
  const live = new Set(openapiRoutes().map((route) => `${route.method} ${route.path}`));
  const stale = readWhitelist()
    .map((entry) => `${entry.method} ${entry.path}`)
    .filter((key) => !live.has(key));
  assert.deepEqual(stale, [], "白名单里有 OpenAPI 不存在的路由（路径写错或后端已删除）");
});

test("no route is listed twice", () => {
  const seen = new Set<string>();
  const dupes: string[] = [];
  for (const entry of readWhitelist()) {
    const key = `${entry.method} ${entry.path}`;
    if (seen.has(key)) dupes.push(key);
    seen.add(key);
  }
  assert.deepEqual(dupes, [], "同一条路由被登记了两次（改一处忘改另一处就会漂）");
});
