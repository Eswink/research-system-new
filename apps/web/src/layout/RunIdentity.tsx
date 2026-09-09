import exampleRun from "../features/example-console/data/run.json";
import { DigestText } from "../features/example-console/reference/DigestText";
import { usePresentation } from "../navigation/usePresentation";
import styles from "./TopBar.module.css";

export function RunIdentity({ runId }: { runId?: string | null | undefined }) {
  const { source } = usePresentation();
  const value = source === "example" ? exampleRun.id : runId;
  return (
    <div className={styles.runIdentity}>
      <span className="vr" />
      <DigestText value={value} label="run:" length={12} prefix={false} />
    </div>
  );
}
