import type { Dispatch, SetStateAction } from "react";

import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/** Team 页头：刷新全部配置 + 新建 Agent 入口。 */
export function TeamPageHeader({
  zh,
  refresh,
  setCreating,
}: {
  zh: boolean;
  refresh: () => void;
  setCreating: Dispatch<SetStateAction<boolean>>;
}) {
  return (
    <PageHeader
      title={zh ? "研究团队与 Agent" : "Research team and agents"}
      kicker="PLAN / TEAM"
      description={
        zh
          ? "职责、配置实例与模型绑定分开管理；所有状态来自实际项目接口。"
          : [
              "Responsibilities, agent instances and model bindings remain distinct, ",
              "using actual project APIs.",
            ].join("")
      }
      actions={
        <div className={styles.toolbar}>
          <button type="button" className="btn" onClick={refresh}>
            {zh ? "刷新配置" : "Refresh configuration"}
          </button>
          <button
            type="button"
            className="btn primary"
            onClick={() => {
              setCreating(true);
            }}
            data-testid="agent-create-open"
          >
            {zh ? "新建 Agent" : "New agent"}
          </button>
        </div>
      }
    />
  );
}
