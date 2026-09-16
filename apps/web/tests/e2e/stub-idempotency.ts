/**
 * 替身 harness 的 Idempotency-Key 契约（GOAL-003 EC-05 / PLAN-068）。
 *
 * 与真中间件（`services/api/middleware.py`）同语义，四条：
 *
 * 1. mutating（POST/PATCH/PUT/DELETE）必须带 `Idempotency-Key`，缺头/空值 → **422**
 *    `Idempotency-Key Required`；
 * 2. 同 key + 不同请求摘要 → **422** `Idempotency-Key Reused`；
 * 3. 同 key + 同摘要 → **重放首次响应**（不触发第二次状态变更）；
 * 4. 分析类 POST（`validate`/`compile`/`preflight`/`dry-run`/`test`/`discover-models`/`probe`）
 *    豁免——它们没有业务写入。
 *
 * 为什么替身要做这件事：stub 套件原本完全不看请求头，客户端漏发 `Idempotency-Key`
 * 在 stub 上"照样成功"，只有 live 套件才拦得住——这条契约属于**客户端**，
 * 必须能在 stub 层被证伪（详见 RECHECK-068 的客户端反证）。
 *
 * 两个**刻意的不一致**（写进 RECHECK-068 的告警，不假装逐字相同）：
 * - 摘要只需"同/不同"的判等，不追求与真中间件 sha256 的逐字节一致（两者不共享存储）；
 * - 重放响应不带 `ETag`（真中间件会回放存储的 ETag；替身的响应体里没有它）。
 *
 * `ANALYSIS_ACTIONS`/`MUTATING_METHODS` 与 Python 侧词表由
 * `tests/tooling/test_console_stub_idempotency_parity.py` 守同步。
 */

export const MUTATING_METHODS = ["POST", "PATCH", "PUT", "DELETE"] as const;

export const ANALYSIS_ACTIONS = [
  "validate",
  "compile",
  "preflight",
  "dry-run",
  "test",
  "discover-models",
  "probe",
] as const;

/** 与真中间件 `_problem()` 同形状（注意 `instance` 是空串，不是请求路径）。 */
export interface ProblemBody {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
}

export interface StubReply {
  status: number;
  body: unknown;
}

/** 一次 mutating 调用的记账票据：handler 跑完后用它记下响应。 */
export interface MutationTicket {
  key: string;
  digest: string;
}

/** 待守门的请求（替身只用到这四样，避免长参数表）。 */
export interface MutationRequest {
  method: string;
  path: string;
  headers: Record<string, string>;
  bodyText: string;
}

function problem(status: number, title: string, detail: string): ProblemBody {
  return { type: "about:blank", title, status, detail, instance: "" };
}

function isMutating(method: string): boolean {
  return (MUTATING_METHODS as readonly string[]).includes(method);
}

function isAnalysisPost(path: string): boolean {
  const last = path.replace(/\/+$/, "").split("/").pop() ?? "";
  return (ANALYSIS_ACTIONS as readonly string[]).includes(last);
}

function requiredKey(): StubReply {
  return {
    status: 422,
    body: problem(422, "Idempotency-Key Required", "mutating requests require Idempotency-Key"),
  };
}

function reusedKey(): StubReply {
  return {
    status: 422,
    body: problem(
      422,
      "Idempotency-Key Reused",
      "Idempotency-Key was used with a different request payload",
    ),
  };
}

/** key → 首次响应的摘要与内容（替身进程内，逐测试重置）。 */
const replayStore = new Map<string, { digest: string } & StubReply>();

/** 每个测试开头调用：stub 的幂等存储不能被上一个测试污染。 */
export function resetIdempotencyStub(): void {
  replayStore.clear();
}

/**
 * 请求进入 handler 之前的守门：
 * - 返回 `reject` ⇒ 直接回该响应（缺头 / 同 key 不同摘要 / 重放）；
 * - 返回 `ticket` ⇒ 交给 handler，之后用 `recordMutation` 记账。
 */
export function beginMutation(request: MutationRequest): {
  reject?: StubReply;
  ticket?: MutationTicket;
} {
  const { method, path, headers, bodyText } = request;
  if (!isMutating(method) || (method === "POST" && isAnalysisPost(path))) {
    return {};
  }
  const key = headers["idempotency-key"];
  if (key === undefined || key === "") {
    return { reject: requiredKey() };
  }
  const digest = `${method}\n${path}\n${bodyText}`;
  const stored = replayStore.get(key);
  if (stored !== undefined) {
    if (stored.digest !== digest) {
      return { reject: reusedKey() };
    }
    return { reject: { status: stored.status, body: stored.body } };
  }
  return { ticket: { key, digest } };
}

/** handler 返回之后记账（只记首次执行，重放不会到这里）。 */
export function recordMutation(ticket: MutationTicket, reply: StubReply): void {
  replayStore.set(ticket.key, { digest: ticket.digest, status: reply.status, body: reply.body });
}
