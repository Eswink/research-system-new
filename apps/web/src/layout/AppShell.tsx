import type { ReactNode } from "react";

import { useI18n } from "../i18n/useI18n";
import type { ConsolePreferences } from "./preferences";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import styles from "./AppShell.module.css";

/**
 * 应用外壳：左侧信息域导航 + 顶部上下文/偏好条 + 主工作区。
 * 共享上下文只保存界面状态（选中 Run ID 等）；业务数据从 API 获取。
 */
export function AppShell({
  route,
  onNavigate,
  preferences,
  onPreferencesChange,
  selectedRunId,
  onSelectedRunIdChange,
  onOpenSetup,
  children,
}: {
  route: string;
  onNavigate: (hash: string) => void;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
  selectedRunId: string;
  onSelectedRunIdChange: (runId: string) => void;
  version?: string | undefined;
  onOpenSetup: () => void;
  children: ReactNode;
}) {
  const { t } = useI18n();
  return (
    <div className={styles.shell}>
      <Sidebar route={route} onNavigate={onNavigate} onOpenSetup={onOpenSetup} />
      <div className={styles.main}>
        <TopBar
          preferences={preferences}
          onPreferencesChange={onPreferencesChange}
          selectedRunId={selectedRunId}
          onSelectedRunIdChange={onSelectedRunIdChange}
        />
        <main className={styles.content} data-testid="console-main">
          <h1 className="sr">{t("app.title")}</h1>
          {children}
        </main>
      </div>
    </div>
  );
}
