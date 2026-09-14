import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { ReportBody } from "./ReportBody";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";

/**
 * 报告（EC-02）：读取既有 persisted `deliverable.json`（M12 build_deliverable
 * 产物）。未完成 M12 参考链的 Run 诚实显示"无交付物"，不生成空报告冒充。
 */
export function ReportsPage({ ctx }: { ctx: PageContext }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const runId = ctx.selectedRunId;
  const key = runId === "" ? null : runId;
  const deliverable = useResource(key, () => api.runDeliverable(runId));
  return (
    <section className={styles.page} data-testid="reports-page">
      <PageHeader
        title={zh ? "研究报告" : "Research reports"}
        kicker="INSIGHTS / REPORTS"
        description={
          zh
            ? "当前 Run 的持久化研究报告（M12 交付物）。未产出交付物的 Run 显示明确空态。"
            : [
                "Persisted research deliverable for the selected run (M12 output). ",
                "Runs without a deliverable show an explicit empty state.",
              ].join("")
        }
        actions={
          <RunQueryBar
            runId={runId}
            onSelect={(id) => {
              if (id === runId) deliverable.reload();
              else ctx.onSelectedRunIdChange(id);
            }}
            busy={deliverable.phase === "loading"}
          />
        }
      />
      {runId === "" && (
        <EmptyState message={zh ? "选择运行以阅读报告" : "Select a run to read its report"} />
      )}
      {runId !== "" && (
        <ResourceBoundary state={deliverable}>
          {deliverable.data !== null && <ReportBody data={deliverable.data} zh={zh} />}
        </ResourceBoundary>
      )}
    </section>
  );
}
