/**
 * 控制面 token 面单元测试（GOAL-20260926-020 EC-01）。
 *
 * 验证四件事（缺一不可）：
 * 1. **只对写请求携带**：POST/PATCH/PUT/DELETE 带 `Authorization: Bearer <token>`，
 *    GET **不带**（后端读面不认证 ⇒ 前端也就不该把凭据发到读请求上）；
 * 2. **未配置时不加空头**：关闭态请求头集合与基线一致（这是「逐字不变」的可测形态）；
 * 3. **存储面**：只存内存——源码里**不得**出现任何持久化写入（`localStorage` /
 *    `sessionStorage` / `IndexedDB` / cookie / URL），也不得回显；
 * 4. **API 语义**：空白串归一为「未配置」，订阅在 set / clear 时触发。
 *
 * 不依赖真实后端；fetch 用合成 mock。**token 值是杜撰串**（非真实凭据）。
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, test } from "node:test";

import {
  clearControlPlaneToken,
  controlPlaneTokenStatus,
  getControlPlaneToken,
  hasControlPlaneToken,
  setControlPlaneToken,
  subscribeControlPlaneToken,
} from "../../src/api/controlPlaneToken";
import { api } from "../../src/api/client";
import { request } from "../../src/api/http";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(HERE, "../../src");
const MODULE = path.join(SRC, "api/controlPlaneToken.ts");

/** 杜撰 token（刻意不是任何真实凭据形态）。 */
const FIXTURE_TOKEN = "fixture-" + "t".repeat(24);

type FetchCall = { url: string; init: RequestInit };

let calls: FetchCall[] = [];

beforeEach(() => {
  calls = [];
  clearControlPlaneToken();
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: typeof input === "string" ? input : input.toString(), init: init ?? {} });
    return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
  }) as typeof fetch;
});

afterEach(() => {
  delete (globalThis as { fetch?: unknown }).fetch;
  clearControlPlaneToken();
});

function authHeaderOf(index: number): string | null {
  return new Headers(calls[index]?.init.headers).get("Authorization");
}

test("写请求带 Authorization: Bearer <token>", async () => {
  setControlPlaneToken(FIXTURE_TOKEN);
  await api.createProject("p");
  assert.equal(authHeaderOf(0), `Bearer ${FIXTURE_TOKEN}`);
});

test("读请求不带 Authorization（读面不认证）", async () => {
  setControlPlaneToken(FIXTURE_TOKEN);
  await api.listProjects();
  assert.equal(authHeaderOf(0), null, "GET 不应携带凭据");
});

test("未配置 token 时写请求也不加空头（关闭态逐字不变）", async () => {
  await api.createProject("p");
  const headers = new Headers(calls[0]?.init.headers);
  assert.equal(headers.get("Authorization"), null);
  assert.ok(headers.get("Idempotency-Key"), "既有写面契约不受影响");
});

test("PATCH/PUT/DELETE 同样携带；无关方法不受影响", async () => {
  setControlPlaneToken(FIXTURE_TOKEN);
  await request("/x", { method: "PATCH", body: JSON.stringify({}) });
  await request("/x", { method: "PUT", body: JSON.stringify({}) });
  await request("/x", { method: "DELETE" });
  await request("/x", { method: "HEAD" });
  assert.equal(authHeaderOf(0), `Bearer ${FIXTURE_TOKEN}`);
  assert.equal(authHeaderOf(1), `Bearer ${FIXTURE_TOKEN}`);
  assert.equal(authHeaderOf(2), `Bearer ${FIXTURE_TOKEN}`);
  assert.equal(authHeaderOf(3), null, "HEAD 属读面");
});

test("空白串归一为未配置；状态与订阅随之变化", () => {
  assert.equal(controlPlaneTokenStatus(), "missing");
  setControlPlaneToken("   ");
  assert.equal(hasControlPlaneToken(), false);
  assert.equal(getControlPlaneToken(), null);

  let notified = 0;
  const unsubscribe = subscribeControlPlaneToken(() => {
    notified += 1;
  });
  setControlPlaneToken(`  ${FIXTURE_TOKEN}  `);
  assert.equal(getControlPlaneToken(), FIXTURE_TOKEN, "首尾空白被去掉");
  assert.equal(controlPlaneTokenStatus(), "configured");
  assert.equal(notified, 1);

  clearControlPlaneToken();
  assert.equal(hasControlPlaneToken(), false);
  assert.equal(notified, 2);

  clearControlPlaneToken();
  assert.equal(notified, 2, "重复清除不重复通知");
  unsubscribe();
});

/**
 * 剥掉注释，只留可执行代码文本。
 *
 * 为什么必须剥：本模块的**文档注释**为了说明「为什么不选浏览器持久层」而**提到了**那些 API
 * ⇒ 对整份源码做子串匹配会把「解释」当成「使用」（判据被自己的文字喂饱）。
 * 本判据要判的是**代码有没有触碰持久化面**，所以先去块注释与行注释。
 * 用 `indexOf` / `slice` 逐段切分，不用正则。
 */
function stripComments(source: string): string {
  let out = "";
  let rest = source;
  while (rest.length > 0) {
    const block = rest.indexOf("/*");
    const line = rest.indexOf("//");
    if (block >= 0 && (line < 0 || block < line)) {
      out += rest.slice(0, block);
      const close = rest.indexOf("*/", block);
      if (close < 0) break;
      rest = rest.slice(close + 2);
      continue;
    }
    if (line >= 0) {
      out += rest.slice(0, line);
      const newline = rest.indexOf("\n", line);
      if (newline < 0) break;
      rest = rest.slice(newline);
      continue;
    }
    out += rest;
    break;
  }
  return out;
}

test("持久化面零命中：源码不写浏览器存储 / cookie / URL", () => {
  const raw = readFileSync(MODULE, "utf8");
  const code = stripComments(raw);
  for (const forbidden of [
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "document.cookie",
    "location.search",
    "window.name",
  ]) {
    assert.ok(!code.includes(forbidden), `token 模块的代码不得触碰持久化面：${forbidden}`);
  }
  // 反向对照 ①：剥注释**确实**在起作用——注释里提到被否决的方案（该措辞只出现在注释里），
  // 所以剥掉后代码文本必然更短，且不再含注释里那句决策说明。
  assert.ok(raw.includes("浏览器存储"), "决策说明应提到被否决的方案");
  assert.ok(!code.includes("决策与理由"), "块注释已被剥掉（注释里的措辞不该出现在代码文本里）");
  assert.ok(code.length < raw.length, "剥注释后代码文本必须更短");
  // 反向对照 ②：本判据确实读到了模块的可执行代码（否则空文件也会「通过」）。
  assert.ok(code.includes("subscribeControlPlaneToken"), "读到了模块的可执行代码");
});
