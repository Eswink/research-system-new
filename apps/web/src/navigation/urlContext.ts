/**
 * URL 上下文参数（T07）：选中的 Run / 草稿经 hash query 恢复，可分享、刷新不丢。
 * 形如 `#/run/timeline?run=run_01K5...`；不包含凭据或协议正文。
 */

export interface UrlContext {
  runId: string;
  draftId: string;
}

export const EMPTY_CONTEXT: UrlContext = { runId: "", draftId: "" };

/** 从完整 hash（`#/domain/page?run=X&draft=Y`）解析上下文参数。 */
export function parseContext(hash: string): UrlContext {
  const qIndex = hash.indexOf("?");
  if (qIndex < 0) {
    return EMPTY_CONTEXT;
  }
  const params = new URLSearchParams(hash.slice(qIndex + 1));
  return {
    runId: params.get("run") ?? "",
    draftId: params.get("draft") ?? "",
  };
}

/** 把上下文参数序列化进 hash（空值省略）。 */
export function withContext(base: string, ctx: UrlContext): string {
  const params = new URLSearchParams();
  if (ctx.runId !== "") {
    params.set("run", ctx.runId);
  }
  if (ctx.draftId !== "") {
    params.set("draft", ctx.draftId);
  }
  const query = params.toString();
  return query === "" ? base : `${base}?${query}`;
}

/** 去掉 hash 的 query 部分，得到纯路由串。 */
export function stripContext(hash: string): string {
  const qIndex = hash.indexOf("?");
  return qIndex < 0 ? hash : hash.slice(0, qIndex);
}
