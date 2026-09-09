/** 编辑器主体（拆分）：YAML 编辑 / 解析错误兜底 / Form 区块布局。 */

import { SectionNav, type SectionId } from "./EditorLayout";
import styles from "./EditorShell.module.css";
import { parseProtocolYaml } from "./protocolDocument";
import { IdentitySection } from "./sections/IdentitySection";
import { PhasesSection } from "./sections/PhasesSection";

export function EditorBody(props: {
  mode: "form" | "yaml";
  working: string;
  savedRevision: number | null;
  activeSection: SectionId;
  onSectionChange: (section: SectionId) => void;
  onEditText: (text: string) => void;
}): React.JSX.Element {
  if (props.mode === "yaml") {
    return (
      <div className={styles.yamlView} data-testid="yaml-view">
        <textarea
          className={styles.yamlEditor}
          value={props.working}
          spellCheck={false}
          onChange={(event) => {
            props.onEditText(event.target.value);
          }}
        />
      </div>
    );
  }
  const outcome = parseProtocolYaml(props.working);
  const form = outcome.form;
  if (form === null) {
    return (
      <div className={styles.formFallback} role="alert" data-testid="form-fallback">
        {outcome.error}
      </div>
    );
  }
  return (
    <div className={styles.formGrid}>
      <SectionNav
        active={props.activeSection}
        onChange={props.onSectionChange}
        counts={{ identity: { errors: 0, warnings: 0 }, phases: { errors: 0, warnings: 0 } }}
      />
      <div className={styles.formBody} data-testid={"section-" + props.activeSection}>
        {props.activeSection === "identity" ? (
          <IdentitySection form={form} revision={props.savedRevision} />
        ) : (
          <PhasesSection form={form} onEditText={props.onEditText} />
        )}
      </div>
    </div>
  );
}
