import { EXAMPLE_WORKSPACES } from "../features/example-console/exampleChrome";
import { WorkspaceSwitcher } from "../features/example-console/reference/WorkspaceSwitcher";
import { useI18n } from "../i18n/useI18n";
import { usePresentation } from "../navigation/usePresentation";
import styles from "./WorkspaceIdentity.module.css";

export function WorkspaceIdentity() {
  const { source } = usePresentation();
  const { language } = useI18n();
  return (
    <div className={styles.identity}>
      {source === "example" ? (
        <WorkspaceSwitcher workspaces={EXAMPLE_WORKSPACES} />
      ) : (
        <span className="chip">{language === "zh" ? "个人工作区" : "Personal workspace"}</span>
      )}
    </div>
  );
}
