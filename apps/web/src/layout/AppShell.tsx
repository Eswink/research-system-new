import { useState, type Dispatch, type ReactNode, type SetStateAction } from "react";

import type { TranslationKey } from "../i18n/zh";
import { useI18n } from "../i18n/useI18n";
import type { Route } from "../navigation/registry";
import styles from "./AppShell.module.css";
import { CommandPalette } from "./CommandPalette";
import type { ConsolePreferences } from "./preferences";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

/**
 * 应用外壳：左侧八域导航 + 顶部面包屑/命令/偏好 + 主工作区（16px 间距）。
 * 只持有界面状态（折叠、命令面板）；业务数据从 API 获取。
 */
export interface AppShellProps {
  route: Route;
  runId?: string | null | undefined;
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
    <div
      data-design-surface="console"
      className={styles.shell}
      data-collapsed={collapsed || undefined}
    >
      <Sidebar
        route={`#/${route.domain}/${route.page}`}
        onNavigate={onNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => {
          setCollapsed(!collapsed);
        }}
        onOpenSettings={() => {
          onNavigate("#/settings/settings");
        }}
      />
      <AppShellMain
        {...{ props, onNavigate, route, preferences, onPreferencesChange, setPaletteOpen, t }}
      />
      <CommandPalette
        open={paletteOpen}
        onClose={() => {
          setPaletteOpen(false);
        }}
        onNavigate={onNavigate}
      />
    </div>
  );
}

interface AppShellMainProps {
  props: AppShellProps;
  onNavigate: (hash: string) => void;
  route: Route;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
  setPaletteOpen: Dispatch<SetStateAction<boolean>>;
  t: (key: TranslationKey) => string;
}

function AppShellMain({
  props,
  onNavigate,
  route,
  preferences,
  onPreferencesChange,
  setPaletteOpen,
  t,
}: AppShellMainProps) {
  return (
    <div className={styles.main}>
      <TopBar
        runId={props.runId}
        onNavigate={onNavigate}
        route={route}
        preferences={preferences}
        onPreferencesChange={onPreferencesChange}
        onOpenPalette={() => {
          setPaletteOpen(true);
        }}
        onOpenCommandCenter={props.onOpenCommandCenter}
        onOpenNotifications={props.onOpenNotifications}
      />
      <main className={styles.content} data-testid="console-main">
        <h1 className="sr">{t("app.title")}</h1>
        {props.children}
      </main>
    </div>
  );
}
