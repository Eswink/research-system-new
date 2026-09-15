import { useState } from "react";

import {
  DEFAULT_PROJECT_ID,
  getActiveProjectId,
  setActiveProjectId,
} from "../../api/activeProject";
import { api } from "../../api/client";

/**
 * 项目删除的状态机（EC-06/PLAN-061）。
 *
 * 只负责：确认框开合、busy、错误文案（服务端 409 的 detail 原样呈现，不本地
 * 猜测），以及"删掉的是活动项目 → 活动上下文回退默认项目"这一条副作用；删除
 * 后的读面事实一律由调用方 reload 重新加载。
 */
export function useProjectDeletion(projectId: string, onDeleted: () => void) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runDelete = (): void => {
    setBusy(true);
    setError(null);
    void api
      .deleteProject(projectId)
      .then(() => {
        if (getActiveProjectId() === projectId) {
          setActiveProjectId(DEFAULT_PROJECT_ID);
        }
        onDeleted();
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : String(reason));
      })
      .finally(() => {
        setBusy(false);
        setConfirming(false);
      });
  };
  return { confirming, setConfirming, busy, error, runDelete };
}
