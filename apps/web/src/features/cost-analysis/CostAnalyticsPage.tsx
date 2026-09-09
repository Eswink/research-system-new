import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, UnavailableState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { GAPS } from "../../navigation/pageSupport";
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
            ? "冻结计价来源、正式五态分类与真实维度明细；不把缺少的时序数据画成预测曲线。"
            : [
                "Frozen pricing provenance, formal five-state classifications and actual ",
                "dimensions; missing time series are not fabricated as forecasts.",
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
      <UnavailableState title={t("cost.trend")} reason={GAPS.costSeries} />
    </section>
  );
}
