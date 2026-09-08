import { useState } from "react";

import { api } from "../../api/client";
import { Button } from "../../components/Button";
import { Chip } from "../../components/Chip";
import { Field } from "../../components/Field";
import { SegmentedToggle } from "../../components/SegmentedToggle";
import { ErrorState, LoadingState, UnavailableState } from "../../components/States";
import type { ConsolePreferences } from "../../layout/preferences";
import { useI18n } from "../../i18n/useI18n";
import { useResource } from "../../hooks/useResource";
import { GAPS } from "../../navigation/pageSupport";
import styles from "../shared/FeaturePage.module.css";

const SECTIONS = [
  { id: "preferences", labelKey: "settings.preferences" },
  { id: "workspace", labelKey: "settings.workspace" },
  { id: "account", labelKey: "settings.account" },
  { id: "security", labelKey: "settings.security" },
  { id: "billing", labelKey: "settings.billing" },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];

/**
 * 设置（T27）：主题/密度/语言为真实本地偏好；Workspace 走项目设置 API；
 * 账户/平台 API Keys/双因素/Billing 无 API——锁定并说明。
 */
export function SettingsPage({
  preferences,
  onPreferencesChange,
}: {
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
}) {
  const { t } = useI18n();
  const [section, setSection] = useState<SectionId>("preferences");
  return (
    <div className={styles.page}>
      <h2 className={styles.heading}>{t("settings.title")}</h2>
      <div className={styles.head}>
        {SECTIONS.map((s) => (
          <Button
            key={s.id}
            variant={section === s.id ? "primary" : "ghost"}
            size="sm"
            onClick={() => { setSection(s.id); }}
          >
            {t(s.labelKey as never)}
          </Button>
        ))}
      </div>
      {section === "preferences" && (
        <PreferencesSection preferences={preferences} onChange={onPreferencesChange} />
      )}
      {section === "workspace" && <WorkspaceSection />}
      {section !== "preferences" && section !== "workspace" && (
        <UnavailableState title={t("settings.locked")} reason={GAPS.account} />
      )}
    </div>
  );
}

function PreferencesSection({
  preferences,
  onChange,
}: {
  preferences: ConsolePreferences;
  onChange: (next: ConsolePreferences) => void;
}) {
  const { t } = useI18n();
  return (
    <div className={styles.panel}>
      <div className={styles.panelTitle}>{t("settings.preferences")}</div>
      <Field label={t("app.theme")}>
        <SegmentedToggle
          ariaLabel={t("app.theme")}
          value={preferences.theme}
          options={[
            { value: "dark", label: t("app.theme.dark") },
            { value: "light", label: t("app.theme.light") },
          ]}
          onChange={(v) => {
            onChange({ ...preferences, theme: v === "light" ? "light" : "dark" });
          }}
        />
      </Field>
      <Field label={t("app.density")}>
        <SegmentedToggle
          ariaLabel={t("app.density")}
          value={preferences.density}
          options={[
            { value: "normal", label: t("app.density.normal") },
            { value: "compact", label: t("app.density.compact") },
          ]}
          onChange={(v) => {
            onChange({ ...preferences, density: v === "compact" ? "compact" : "normal" });
          }}
        />
      </Field>
    </div>
  );
}

function WorkspaceSection() {
  const { t } = useI18n();
  const settings = useResource("project-settings", () => api.getProjectSettings());
  if (settings.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (settings.phase === "error") {
    return <ErrorState message={settings.error ?? t("state.error")} />;
  }
  const s = settings.data;
  return (
    <div className={styles.panel}>
      <div className={styles.panelTitle}>{t("settings.workspace")}</div>
      <div className={styles.head}>
        <Chip tone="neutral">{`team: ${s?.team_template_id ?? "—"}`}</Chip>
        <Chip tone="neutral">{`workspace: ${s?.workspace_backend ?? "—"}`}</Chip>
        <Chip tone="neutral">{`budget: ${s?.budget_policy_id ?? "—"}`}</Chip>
      </div>
      <p style={{ margin: "8px 0 0", fontSize: "var(--fs-caption)", color: "var(--fg-muted)" }}>
        {t("settings.lastWrite")}
      </p>
    </div>
  );
}
