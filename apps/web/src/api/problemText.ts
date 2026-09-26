/** RFC-7807 problem → 用户可读单行文本（各写操作错误展示共用）。 */

import { ApiError } from "./http";

/**
 * 401 的**可操作指引**（GOAL-20260926-020 EC-01）。
 *
 * 服务端的 401 正文已经**点名**缺什么（`Authentication Required` +
 * 「缺 `Authorization: Bearer <token>` 头」或「token 不匹配」）。前端**不改**那个形态，
 * 只在后面追加一句「去哪里填」，让「需要认证」在界面上是**可操作**的而不是死路。
 *
 * 为什么写成中英同句：`problemText` 是**不带 i18n 上下文**的纯函数（20+ 写面板共用），
 * 给它加语言参数会牵动全部调用点 ⇒ 用一句短指引保持「不改调用点」的最小改动面。
 */
export const AUTH_REQUIRED_POINTER = "→ Settings / 控制面连接：填入控制面 token 后重试";

export function problemText(err: unknown, fallback = "request failed"): string {
  if (err instanceof ApiError) {
    const line = `${err.problem.title} · ${err.problem.detail}`;
    return err.status === 401 ? `${line} ${AUTH_REQUIRED_POINTER}` : line;
  }
  return err instanceof Error ? err.message : fallback;
}
