import type { TranslationKey } from "../../i18n/zh";
import { useState, type Dispatch, type SetStateAction } from "react";
import { UnavailableState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import type { ConsolePreferences } from "../../layout/preferences";
import { pageSupport, isOperationDisabled } from "../../navigation/pageSupport";
import type { Route } from "../../navigation/registry";
import shared from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { PreferencesSection } from "./PreferencesSection";
import styles from "./SettingsPage.module.css";
import { WorkspaceSection } from "./WorkspaceSection";

const SETTINGS_ROUTE: Route = { domain: "settings", page: "settings" };

const SECTIONS = [
  { id: "preferences", labelKey: "settings.preferences" },
  { id: "workspace", labelKey: "settings.workspace" },
  { id: "account", labelKey: "settings.account" },
  { id: "security", labelKey: "settings.security" },
  { id: "billing", labelKey: "settings.billing" },
] as const;

export function SettingsPage({
  preferences,
  onPreferencesChange,
}: {
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
}) {
  const { language, t } = useI18n();
  const [section, setSection] = useState<(typeof SECTIONS)[number]["id"]>("preferences");
  return (
    <SettingsPageTitle
      {...{ t, language, section, setSection, preferences, onPreferencesChange }}
    />
  );
}

interface SettingsPageTitleProps {
  t: (key: TranslationKey) => string;
  language: string;
  section: string;
  setSection: Dispatch<
    SetStateAction<"preferences" | "workspace" | "account" | "security" | "billing">
  >;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
}

function SettingsPageTitle({
  t,
  language,
  section,
  setSection,
  preferences,
  onPreferencesChange,
}: SettingsPageTitleProps) {
  return (
    <section className={shared.page} data-testid="settings-page">
      <PageHeader
        title={t("settings.title")}
        kicker="SETTINGS / CONSOLE"
        description={
          language === "zh"
            ? "本机偏好、项目配置与尚未接入的账户能力分别标明。"
            : [
                "Local preferences, project configuration and unavailable account ",
                "capabilities are labeled separately.",
              ].join("")
        }
      />
      <SettingsPageLocked
        {...{ language, section, setSection, t, preferences, onPreferencesChange }}
      />
    </section>
  );
}

interface SettingsPageLockedProps {
  language: string;
  section: string;
  setSection: Dispatch<
    SetStateAction<"preferences" | "workspace" | "account" | "security" | "billing">
  >;
  t: (key: TranslationKey) => string;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
}

function SettingsPageLocked({
  language,
  section,
  setSection,
  t,
  preferences,
  onPreferencesChange,
}: SettingsPageLockedProps) {
  return (
    <div className={styles.layout}>
      <nav
        className={styles.navigation}
        aria-label={language === "zh" ? "设置分区" : "Settings sections"}
      >
        {SECTIONS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={styles.section}
            aria-current={section === item.id ? "page" : undefined}
            onClick={() => {
              setSection(item.id);
            }}
          >
            {t(item.labelKey)}
          </button>
        ))}
      </nav>
      <div className={styles.content}>
        {section === "preferences" && (
          <PreferencesSection preferences={preferences} onChange={onPreferencesChange} />
        )}
        {section === "workspace" && <WorkspaceSection />}
        {isOperationDisabled(SETTINGS_ROUTE, section) && (
          <UnavailableState
            title={t("settings.locked")}
            reason={pageSupport(SETTINGS_ROUTE).reason ?? ""}
          />
        )}
      </div>
    </div>
  );
}
