import { LoadingState } from "../components/States";
import { useI18n } from "../i18n/useI18n";
import { ConsoleFrame } from "./ConsoleFrame";
import styles from "./ConsoleLoading.module.css";
import type { ConsoleProps } from "./consoleProps";
import { SourceControl } from "./SourceControl";

/** Keep navigation and source provenance available while an individual route chunk loads. */
export function ConsoleLoading(props: ConsoleProps) {
  const { t } = useI18n();
  const loading = <LoadingState message={t("state.loading")} />;
  if (props.resolved.route.domain === "command-center")
    return (
      <main className={styles.screen}>
        <SourceControl />
        {loading}
      </main>
    );
  return <ConsoleFrame {...props}>{loading}</ConsoleFrame>;
}
