/**
 * 活动项目上下文（PLAN-041 WP-C，EC-01）。
 *
 * view-state（localStorage，经 preferences.ts 同风格的惰性访问器——持久化写入
 * 面保持仓库的安全扫描约束），不是业务真相：项目注册表与数据归属以后端为准
 * （POST /projects 落行；runs/settings/drafts 按路径 project_id 持久化）。
 * client 层默认读取本模块拼接 project 路径；显式传参可覆盖（对比页等）。
 */

export const DEFAULT_PROJECT_ID = "example-project";
export const ACTIVE_PROJECT_EVENT = "ros:active-project";

const STORAGE_KEY = "ros.active-project";

/** node:test 无 window；惰性访问 + 缺失回退保证纯 Node 环境可测（preferences 同风格）。 */
function storage(): Pick<Storage, "getItem" | "setItem"> | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
}

export function getActiveProjectId(): string {
  const stored = storage()?.getItem(STORAGE_KEY);
  return stored === null || stored === undefined || stored === ""
    ? DEFAULT_PROJECT_ID
    : stored;
}

export function setActiveProjectId(projectId: string): void {
  if (!projectId) return;
  // 隐私模式/无存储环境：本轮会话内保持默认即可，不伪造持久化。
  storage()?.setItem(STORAGE_KEY, projectId);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(ACTIVE_PROJECT_EVENT, { detail: projectId }));
  }
}

export function subscribeActiveProject(listener: () => void): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }
  const handler = () => {
    listener();
  };
  window.addEventListener(ACTIVE_PROJECT_EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(ACTIVE_PROJECT_EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}
