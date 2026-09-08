import { Icon } from "../../../components/Icon";
import styles from "./EditorChrome.module.css";
import { ChromeActions, ModeToggle } from "./EditorChromeParts";

/** 编辑器工具条：文件名 + DIRTY 徽章 + Form/YAML 切换 + 模板/校验/差异 */
export function EditorChrome({
  mode,
  onModeChange,
  dirty,
  fileName,
  templateOpen,
  onToggleTemplates,
  onValidate,
  onDiff,
  validateBusy,
}: {
  mode: "form" | "yaml";
  onModeChange: (mode: "form" | "yaml") => void;
  dirty: boolean;
  fileName: string;
  templateOpen: boolean;
  onToggleTemplates: () => void;
  onValidate: () => void;
  onDiff: () => void;
  validateBusy: boolean;
}) {
  return (
    <div className={styles.chrome}>
      <Icon name="book" size={12} className={styles.fileIcon} />
      <span className={styles.fileName}>{fileName}</span>
      {dirty && <span className={styles.dirtyPill}>DIRTY</span>}
      <div className={styles.actions}>
        <ModeToggle mode={mode} onModeChange={onModeChange} />
        <ChromeActions
          templateOpen={templateOpen}
          onToggleTemplates={onToggleTemplates}
          onValidate={onValidate}
          onDiff={onDiff}
          validateBusy={validateBusy}
        />
      </div>
    </div>
  );
}
