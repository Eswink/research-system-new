/**
 * e2e 严格 API 替身（PLAN-20260908-034 T10）。
 *
 * 替换旧空数组兜底：未注册的 /api 请求立即使测试失败（route.abort + 记录违规），
 * 已支持 API 的样例遵循真实 DTO 形状。无后端页面的填充数据只进入隔离的视觉
 * 测试组合入口（见 visualFixtures），不加入生产路由/生产 API 客户端。
 *
 * 路由表与 fixture 常量拆到 stubRoutes.ts / stubFixtures.ts（守 450 行硬上限）；
 * 本文件只保留拦截 harness 与未匹配断言。
 */

import type { Page, Route } from "@playwright/test";

import { beginMutation, recordMutation, resetIdempotencyStub } from "./stub-idempotency";
import { ROUTES, type StubRoute } from "./stub-routes";

export { DRAFT, ENDPOINT, VALID_YAML } from "./stub-fixtures";

/** 收集未匹配请求，测试结束断言为空。 */
export const unmatchedRequests: string[] = [];

function match(path: string, method: string): StubRoute | null {
  for (const route of ROUTES) {
    if (route.method === method && route.pattern.test(path)) {
      return route;
    }
  }
  return null;
}

interface FulfillOptions {
  status: number;
  body: unknown;
  /** 文本制品正文：逐字原文（不带 JSON 引号/转义），与真后端的 `text/markdown` 一致。 */
  text?: boolean;
}

function fulfill(route: Route, { status, body, text = false }: FulfillOptions): void {
  if (text) {
    void route
      .fulfill({ status, contentType: "text/markdown; charset=utf-8", body: String(body) })
      .catch(() => undefined);
    return;
  }
  void route
    .fulfill({ status, contentType: "application/json", body: JSON.stringify(body) })
    .catch(() => undefined);
}

export async function stubApi(page: Page): Promise<void> {
  unmatchedRequests.length = 0;
  resetIdempotencyStub();
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith("/api/")) {
      void route.continue();
      return;
    }
    const path = url.pathname.replace(/^\/api/, "");
    const method = route.request().method();
    const post = route.request().postData();
    // EC-05：mutating 契约在 handler 之前守门（缺头 → 422，与真中间件同语义）
    const gate = beginMutation({
      method,
      path,
      headers: route.request().headers(),
      bodyText: post ?? "",
    });
    if (gate.reject !== undefined) {
      fulfill(route, { status: gate.reject.status, body: gate.reject.body });
      return;
    }
    const handler = match(path, method);    if (handler === null) {
      unmatchedRequests.push(`${method} ${url.pathname}`);
      fulfill(route, {
        status: 500,
        body: {
          type: "about:blank",
          title: "Unstubbed Request",
          status: 500,
          detail: `No stub for ${method} ${path}`,
          instance: path,
        },
      });
      return;
    }
    let body: unknown;
    try {
      body = post ? JSON.parse(post) : undefined;
    } catch {
      body = undefined;
    }
    const result = handler.handler(url, body);
    if (gate.ticket !== undefined) {
      recordMutation(gate.ticket, result);
    }
    fulfill(route, { status: result.status, body: result.body, text: handler.bodyKind === "text" });
  });
}

/** 测试内断言：无未匹配请求。 */
export function assertNoUnmatched(): void {
  if (unmatchedRequests.length > 0) {
    const list = unmatchedRequests.join(", ");
    unmatchedRequests.length = 0;
    throw new Error(`Unstubbed API requests: ${list}`);
  }
}
