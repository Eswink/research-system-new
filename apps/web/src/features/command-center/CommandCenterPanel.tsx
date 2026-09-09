import type { ReactNode } from "react";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import type { ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { usePresentation } from "../../navigation/usePresentation";
import styles from "./CommandCenterPage.module.css";

export function CommandCenterPanel<T>({
  title,
  state,
  children,
}: {
  title: string;
  state: ResourceState<T>;
  children: (value: T) => ReactNode;
}) {
  const { language } = useI18n();
  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>
        {title}
        <span>QUERY SNAPSHOT</span>
      </h2>
      <div className={styles.panelBody}>
        <ResourceBoundary state={state}>
          {state.data === null ? (
            <p className={styles.empty}>
              {language === "zh"
                ? "先选择运行；未读取不等于零。"
                : "Select a run; not loaded does not mean zero."}
            </p>
          ) : (
            children(state.data)
          )}
        </ResourceBoundary>
      </div>
    </section>
  );
}

export function CommandCenterGap({ title, reason }: { title: string; reason: string }) {
  const { language } = useI18n();
  const { setSource } = usePresentation();
  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>
        {title}
        <span>API GAP</span>
      </h2>
      <div className={styles.gap}>
        <div className={styles.gapSymbol} aria-hidden="true">
          ◇
        </div>
        <p>{reason}</p>
        <button
          type="button"
          className="btn sm"
          onClick={() => {
            setSource("example");
          }}
        >
          {language === "zh" ? "查看带标识的完整示例" : "View labeled complete example"}
        </button>
      </div>
    </section>
  );
}
