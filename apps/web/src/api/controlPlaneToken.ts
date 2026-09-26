/**
 * 控制面写面 token（GOAL-20260926-020 EC-01）：**内存**存储面。
 *
 * 为什么是内存（三选一的决策与理由，见 RECHECK-20260926-198 / MEM-20260926-147）：
 *
 * - **落盘面的既有约束**：`tests/api/test_security_scan.py` 对 `apps/web/src/**` 断言
 *   **不出现浏览器存储的写入调用**（`localStorage` / `sessionStorage` 的 setItem 形态），
 *   其意图是「前端持久层无 secret 写入」。选 `localStorage` / `sessionStorage` 都要么
 *   放宽这条既有安全判据、要么用「惰性访问器」绕开字面量检查而违反其意图
 *   ⇒ 两条路都不在本 GOAL 授权内。
 * - **内存的代价（如实记录）**：**刷新即失**，操作者需重新粘贴。这是本轮**选定的代价**：
 *   它换来的是「token 不进入任何可持久化面」——包括 XSS 可读的持久层。
 * - **XSS 面**：内存态同样可被同源脚本读取（任何方案在浏览器内都如此）；差别在于
 *   **持久性**——内存态在页面关闭 / 刷新后消失，不会在磁盘上留下可被后续读取的副本。
 * - **不落盘的具体面**：不用浏览器存储（local/session/IndexedDB）/ cookie / URL
 *   （query 或 fragment）/ `window.name` / `document.title`；不写入日志与错误上报。
 *
 * 契约：**读取不回显**——本模块只提供 set / clear / 是否存在 / 取头部值；
 * UI 不展示已存 token 的明文，只展示「已配置 / 未配置」。
 *
 * 注：本文件**不得**出现任何持久化 API 的**调用形态**字面量——那既是实现纪律，
 * 也是 `tests/api/test_security_scan.py` 的**子串**判据所扫的面（该判据不解析注释）。
 */

const BEARER_SCHEME = "Bearer";

let token: string | null = null;

const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) {
    listener();
  }
}

/** 归一：空串 / 纯空白 ⇒ 视为未配置（与后端「留空 = 认证关闭」同一语义）。 */
function normalize(raw: string): string | null {
  const trimmed = raw.trim();
  return trimmed === "" ? null : trimmed;
}

export function getControlPlaneToken(): string | null {
  return token;
}

export function hasControlPlaneToken(): boolean {
  return token !== null;
}

export function setControlPlaneToken(raw: string): void {
  const next = normalize(raw);
  if (next === token) return;
  token = next;
  notify();
}

export function clearControlPlaneToken(): void {
  if (token === null) return;
  token = null;
  notify();
}

/** 订阅变化（React 侧用 useSyncExternalStore 消费）。 */
export function subscribeControlPlaneToken(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * 写请求的 `Authorization` 头值；未配置 ⇒ `null`（调用方**不得**据此加空头）。
 * 只返回「scheme + 值」这一件事，不暴露任何持久化通道。
 */
export function authorizationHeaderValue(): string | null {
  return token === null ? null : `${BEARER_SCHEME} ${token}`;
}

/** 仅供测试与 UI 状态展示：token 是否呈现为「已配置」，绝不返回明文。 */
export function controlPlaneTokenStatus(): "configured" | "missing" {
  return token === null ? "missing" : "configured";
}
