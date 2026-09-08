import type { Language } from "../i18n/I18nProvider";
import { useI18n } from "../i18n/useI18n";
import type { ConsolePreferences } from "./preferences";
import styles from "./TopBar.module.css";

function RunContext({
  selectedRunId,
  onSelectedRunIdChange,
}: {
  selectedRunId: string;
  onSelectedRunIdChange: (runId: string) => void;
}) {
  const { t } = useI18n();
  const hasRun = selectedRunId.length > 0;
  return (
    <div className={styles.runContext} data-testid="run-context">
      <span className={styles.runLabel}>{t("run.context.label")}</span>
      {hasRun ? (
        <>
          <span className="chip mono">{selectedRunId}</span>
          <button
            type="button"
            className="btn sm ghost"
            onClick={() => {
              onSelectedRunIdChange("");
            }}
          >
            {t("run.context.clear")}
          </button>
        </>
      ) : (
        <span className="empty-mark">{t("run.context.none")}</span>
      )}
    </div>
  );
}

function SelectControl({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className={styles.control}>
      <span className={styles.controlLabel}>{label}</span>
      <select
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

const THEME_OPTIONS = [
  { value: "dark", key: "app.theme.dark" },
  { value: "light", key: "app.theme.light" },
] as const;

const DENSITY_OPTIONS = [
  { value: "normal", key: "app.density.normal" },
  { value: "compact", key: "app.density.compact" },
] as const;

const LANGUAGE_OPTIONS = [
  { value: "zh", label: "中文" },
  { value: "en", label: "English" },
] as const;

function PreferenceControls({
  preferences,
  onPreferencesChange,
}: {
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
}) {
  const { t, setLanguage } = useI18n();
  const nextLang = (raw: string): Language => (raw === "en" ? "en" : "zh");
  return (
    <div className={styles.controls}>
      <SelectControl
        label={t("app.theme")}
        value={preferences.theme}
        options={THEME_OPTIONS.map((o) => ({ value: o.value, label: t(o.key) }))}
        onChange={(raw) => {
          onPreferencesChange({ ...preferences, theme: raw === "light" ? "light" : "dark" });
        }}
      />
      <SelectControl
        label={t("app.density")}
        value={preferences.density}
        options={DENSITY_OPTIONS.map((o) => ({ value: o.value, label: t(o.key) }))}
        onChange={(raw) => {
          const density = raw === "compact" ? "compact" : "normal";
          onPreferencesChange({ ...preferences, density });
        }}
      />
      <SelectControl
        label={t("app.language")}
        value={preferences.language}
        options={LANGUAGE_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
        onChange={(raw) => {
          setLanguage(nextLang(raw));
        }}
      />
      <span className="chip mono" title={t("app.version")}>
        v{preferences.version}
      </span>
    </div>
  );
}

/** 顶部条：当前运行上下文 + 主题/密度/语言偏好 + 工程版本（只读，来自根 VERSION） */
export function TopBar({
  preferences,
  onPreferencesChange,
  selectedRunId,
  onSelectedRunIdChange,
}: {
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
  selectedRunId: string;
  onSelectedRunIdChange: (runId: string) => void;
}) {
  return (
    <header className={styles.topbar}>
      <RunContext
        selectedRunId={selectedRunId}
        onSelectedRunIdChange={onSelectedRunIdChange}
      />
      <PreferenceControls preferences={preferences} onPreferencesChange={onPreferencesChange} />
    </header>
  );
}
