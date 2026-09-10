/** RFC-7807 problem → 用户可读单行文本（各写操作错误展示共用）。 */

import { ApiError } from "./http";

export function problemText(err: unknown, fallback = "request failed"): string {
  if (err instanceof ApiError) {
    return `${err.problem.title} · ${err.problem.detail}`;
  }
  return err instanceof Error ? err.message : fallback;
}
