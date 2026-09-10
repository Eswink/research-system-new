import { Icon } from "../../../components/Icon";
import { cx } from "../../../components/cx";
import { useI18n } from "../../../i18n/useI18n";
import styles from "./EditorChrome.module.css";

/** Form/YAML 分段切换（role=radiogroup；切换不丢输入） */
export function ModeToggle({
  mode,
  onModeChange,
}: {
  mode: "form" | "yaml";
  onModeChange: (mode: "form" | "yaml") => void;
}) {
  const { t } = useI18n();
  const groupLabel = t("editor.title");
  const segments: readonly { value: "form" | "yaml"; label: string; icon: "edit" | "code" }[] = [
    { value: "form", label: t("editor.mode.form"), icon: "edit" },
    { value: "yaml", label: t("editor.mode.yaml"), icon: "code" },
  ];
  return (
    <div className={styles.toggle} role="radiogroup" aria-label={groupLabel}>
      {segments.map((segment) => (
        <button
          key={segment.value}
          type="button"
          role="radio"
          aria-checked={mode === segment.value}
          className={cx(styles.segment, mode === segment.value && styles.segmentActive)}
          onClick={() => {
            onModeChange(segment.value);
          }}
        >
          <Icon name={segment.icon} size={10} /> {segment.label}
        </button>
      ))}
    </div>
  );
}

/** 工具条右侧按钮组：模板 / 差异 / 校验 */
export function ChromeActions({
  templateOpen,
  onToggleTemplates,
  onValidate,
  onDiff,
  validateBusy,
}: {
  templateOpen: boolean;
  onToggleTemplates: () => void;
  onValidate: () => void;
  onDiff: () => void;
  validateBusy: boolean;
}) {
  const { t } = useI18n();
  return (
    <>
      <span className={cx("vr", styles.vrShort)} />
      <button
        type="button"
        id="templates-toggle"
        className={cx("btn", "sm", "ghost", styles.iconBtn)}
        title={t("editor.templates.tip")}
        aria-expanded={templateOpen}
        data-testid="templates-toggle"
        onClick={onToggleTemplates}
      >
        <Icon name="copy" size={10} /> {t("editor.templates")} <Icon name="chevron-d" size={9} />
      </button>
      <button
        type="button"
        className={cx("btn", "sm", "ghost", styles.iconBtn)}
        aria-label={t("editor.diff")}
        title={t("editor.diff.tip")}
        onClick={onDiff}
      >
        <Icon name="fork" size={10} />
      </button>
      <button
        type="button"
        className={cx("btn", "sm", "ghost", styles.iconBtn)}
        aria-label={t("editor.validate")}
        title={t("editor.validate.tip")}
        onClick={onValidate}
        disabled={validateBusy}
      >
        <Icon name="check" size={10} />
      </button>
    </>
  );
}
