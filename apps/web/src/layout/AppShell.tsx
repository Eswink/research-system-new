import { useState, type ReactNode } from "react";

import { useI18n } from "../i18n/useI18n";
import type { Route } from "../navigation/registry";
import { CommandPalette } from "./CommandPalette";
import type { ConsolePreferences } from "./preferences";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import styles from "./AppShell.module.css";

/**
 * 应用外壳：左侧八域导航 + 顶部面包屑/命令/偏好 + 主工作区（16px 间距）。
 * 只持有界面状态（折叠、命令面板）；业务数据从 API 获取。
 */
export interface AppShellProps {
  route: Route;
  onNavigate: (hash: string) => void;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
  onOpenCommandCenter: () => void;
  onOpenNotifications: () => void;
  children: ReactNode;
}

export function AppShell(props: AppShellProps) {
  const { route, onNavigate, preferences, onPreferencesChange } = props;
  const { t } = useI18n();
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  return (
    <div className={styles.shell} data-collapsed={collapsed || undefined}>
      <Sidebar
        route={`#/${route.domain}/${route.page}`}
        onNavigate={onNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => { setCollapsed(!collapsed); }}
        onOpenSettings={() => { onNavigate("#/settings/settings"); }}
      />
      <div className={styles.main}>
        <TopBar
          route={route}
          preferences={preferences}
          onPreferencesChange={onPreferencesChange}
          onOpenPalette={() => { setPaletteOpen(true); }}
          onOpenCommandCenter={props.onOpenCommandCenter}
          onOpenNotifications={props.onOpenNotifications}
        />
        <main className={styles.content} data-testid="console-main">
          <h1 className="sr">{t("app.title")}</h1>
          {props.children}
        </main>
      </div>
      <CommandPalette
        open={paletteOpen}
        onClose={() => { setPaletteOpen(false); }}
        onNavigate={onNavigate}
      />
    </div>
  );
}
