import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { DailyCostPanel } from "./DailyCostPanel";
import { ProjectCostForecastPanel } from "./ProjectCostForecastPanel";
import { CostView } from "../operations/CostView";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";

export function CostAnalyticsPage({ ctx }: { ctx: PageContext }) {
  const { language, t } = useI18n();
  const runId = ctx.selectedRunId;
  const cost = useResource(runId === "" ? null : runId, () => api.runCost(runId));
  return (
    <section className={styles.page} data-testid="cost-analytics-page">
      <PageHeader
        title={t("page.insights.cost-analytics")}
        kicker="INSIGHTS / COST ANALYTICS"
        description={
          language === "zh"
            ? [
                "冻结计价来源、正式五态分类与真实维度明细；",
                "项目级预测只对已计价的天外推（方法/样本/排除项随响应返回），不插值、UNKNOWN 不当 0。",
              ].join("")
            : [
                "Frozen pricing provenance, formal five-state classifications and actual ",
                "dimensions; the project projection extrapolates valued days only (method, ",
                "sample size and exclusions come from the response) — never interpolated.",
              ].join("")
        }
        actions={
          <RunQueryBar
            runId={runId}
            busy={cost.phase === "loading"}
            onSelect={(id) => {
              if (id === runId) cost.reload();
              else ctx.onSelectedRunIdChange(id);
            }}
          />
        }
      />
      {runId === "" && <EmptyState message={t("overview.noRun")} />}
      <ResourceBoundary state={cost}>
        {cost.data !== null && <CostView cost={cost.data} />}
      </ResourceBoundary>
      <DailyCostPanel />
      <ProjectCostForecastPanel />
    </section>
  );
}
