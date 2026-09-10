/** Run 控制面迁移门（与后端状态机白名一致：RUNNING↔PAUSED；终态不可再请求取消）。 */

export function canRequestCancellation(state: string): boolean {
  return !new Set(["SUCCEEDED", "FAILED", "CANCELLED", "REJECTED"]).has(state);
}

/** 后端仅在 RUNNING→PAUSED 迁移成功，其余返回 409。 */
export function canPauseRun(state: string): boolean {
  return state === "RUNNING";
}

/** 后端仅在 PAUSED→RUNNING 迁移成功（并要求冻结 manifest 摘要一致）。 */
export function canResumeRun(state: string): boolean {
  return state === "PAUSED";
}
