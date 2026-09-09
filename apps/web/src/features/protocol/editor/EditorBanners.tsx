import { Icon } from "../../../components/Icon";
import { cx } from "../../../components/cx";
import { useI18n } from "../../../i18n/useI18n";
import styles from "./EditorLayout.module.css";

/** 模板选择下拉（服务端受控目录；点击模板载入其正文；Esc 关闭） */
export function TemplatePicker({
  templates,
  onPick,
  onClose,
}: {
  templates: readonly { template_id: string; display_name: string; description: string }[];
  onPick: (templateId: string) => void;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const onKeyDown = (event: React.KeyboardEvent): void => {
    if (event.key === "Escape") {
      onClose();
    }
  };
  return (
    <div className={styles.templatePicker} data-testid="template-picker" onKeyDown={onKeyDown}>
      <TemplatePickerHeader
        onClose={onClose}
        label={t("editor.templatesHeader")}
        closeLabel={t("editor.templates")}
      />
      <div className={styles.templateGrid}>
        {templates.map((item, index) => (
          <TemplateCard
            key={item.template_id}
            item={item}
            autoFocus={index === 0}
            onPick={onPick}
          />
        ))}
      </div>
    </div>
  );
}

function TemplatePickerHeader({
  label,
  closeLabel,
  onClose,
}: {
  label: string;
  closeLabel: string;
  onClose: () => void;
}) {
  return (
    <div className={styles.templateHeader}>
      <span>{label}</span>
      <button
        type="button"
        className="btn sm ghost"
        style={{ height: 18, padding: "0 6px" }}
        aria-label={closeLabel}
        onClick={onClose}
      >
        <Icon name="x" size={9} />
      </button>
    </div>
  );
}

function TemplateCard({
  item,
  autoFocus,
  onPick,
}: {
  item: { template_id: string; display_name: string; description: string };
  autoFocus: boolean;
  onPick: (templateId: string) => void;
}) {
  return (
    <button
      type="button"
      className={styles.templateCard}
      autoFocus={autoFocus}
      onClick={() => {
        onPick(item.template_id);
      }}
    >
      <Icon name="book" size={12} className={styles.templateIcon} />
      <span className={styles.templateBody}>
        <span className={styles.templateName}>{item.display_name}</span>
        <span className={styles.templateDesc}>{item.description}</span>
      </span>
    </button>
  );
}

/** 未保存修改横幅（复用设计稿 DigestBanner；摘要来自真实修订） */
export function DigestBanner({ digest }: { digest: string }) {
  const { t } = useI18n();
  const codeClass = cx("mono", styles.digestCode);
  return (
    <div className={styles.digestBanner}>
      <Icon name="warn-tri" size={11} className={styles.digestIcon} />
      <span>
        <strong>{t("editor.warnTitle")}</strong> {t("editor.dirty")}{" "}
        <span className={codeClass}>
          {digest} → <span className={styles.digestDirty}>dirty</span>
        </span>
      </span>
    </div>
  );
}

/** 错误汇总横幅（可展开定位到区块） */
export function ErrorBanner({
  errors,
  onJump,
}: {
  errors: readonly { code: string; message: string; section: SectionRef }[];
  onJump: (section: SectionRef) => void;
}) {
  const { t } = useI18n();
  return (
    <div className={styles.errorBanner} role="alert">
      <div className={styles.errorBannerRow}>
        <Icon name="x" size={11} />
        <span>
          <strong>
            {errors.length} {t("editor.errorsBlock")}
          </strong>
        </span>
      </div>
      <div className={styles.errorList}>
        {errors.map((error) => (
          <button
            key={`${error.code}-${error.message}`}
            type="button"
            className={cx("btn", "sm", "ghost", styles.errorJump)}
            onClick={() => {
              onJump(error.section);
            }}
          >
            <span className="mono">{error.code}</span> · {error.message} · {t("editor.jumpTo")}
          </button>
        ))}
      </div>
    </div>
  );
}

export type SectionRef = "identity" | "phases" | "yaml";
