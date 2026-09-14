import { useState } from "react";

import type { BudgetViewDto, CostForecastDto } from "../../api/types";
import { api } from "../../api/client";
import { Button } from "../../components/Button";
import { MetricCard } from "../../components/charts/MetricCard";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { TranslationKey } from "../../i18n/zh";
import type { PageContext } from "../../navigation/pageContext";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { BudgetAdjustBar } from "./BudgetAdjustBar";
import { ForecastTable } from "./ForecastTable";
import { forecastSummary } from "./forecastPresentation";
import { LedgerTables } from "./LedgerTables";
import { ledgerSummary } from "./ledgerPresentation";

interface BudgetData {
  t: (key: TranslationKey) => string;
  zh: boolean;
  runId: string;
  ctx: PageContext;
  usage: ResourceState<BudgetViewDto>;
  forecast: ResourceState<CostForecastDto>;
}

export function BudgetPage({ ctx }: { ctx: PageContext }) {
  const { language, t } = useI18n();
  const runId = ctx.selectedRunId;
  const usage = useResource(runId === "" ? null : runId, () => api.runUsage(runId));
  const forecast = useResource(runId === "" ? null : `${runId}#forecast`, () =>
    api.runCostForecast(runId),
  );
  const [adjusting, setAdjusting] = useState(false);
  const data: BudgetData = { t, zh: language === "zh", runId, ctx, usage, forecast };
  return (
    <BudgetPageBody
      {...data}
      adjusting={adjusting}
      onToggleAdjust={() => {
        setAdjusting((open) => !open);
      }}
      onReload={() => {
        usage.reload();
        forecast.reload();
      }}
    />
  );
}

interface BudgetPageBodyProps extends BudgetData {
  adjusting: boolean;
  onToggleAdjust: () => void;
  onReload: () => void;
}

function budgetDescription(zh: boolean): string {
  if (zh) {
    return [
      "当前运行的后端账本投影：预留-消耗预测、原始单位、估算与实际金额、未知费用；",
      "预算调整走 BudgetLedger。",
    ].join("");
  }
  return [
    "Backend ledger projection for the selected run: reserved-vs-consumed forecast, ",
    "original units, estimated/actual amounts and unknown costs; ",
    "adjustments go through the BudgetLedger.",
  ].join("");
}

function budgetMetrics(zh: boolean, usage: BudgetPageBodyProps["usage"], forecast: string) {
  const summary = ledgerSummary(usage.phase === "ready" ? usage.data : null);
  return [
    [zh ? "总估算金额" : "Total estimated cost", summary.total],
    [zh ? "已知小计（不等于总额）" : "Known subtotal (not the total)", summary.subtotal],
    [zh ? "未知费用条目" : "Unknown-cost entries", summary.unknownEntries],
    [zh ? "预留-消耗" : "Reserved vs consumed", forecast],
  ] as const;
}

function BudgetPageBody({ t, zh, runId, ctx, usage, forecast, ...rest }: BudgetPageBodyProps) {
  const metrics = budgetMetrics(
    zh,
    usage,
    forecastSummary(forecast.phase === "ready" ? forecast.data : null),
  );
  return (
    <section className={styles.page} data-testid="budget-page">
      <PageHeader
        title={t("page.govern.budget")}
        kicker="GOVERNANCE / BUDGET & USAGE"
        description={budgetDescription(zh)}
        actions={
          <Button onClick={rest.onToggleAdjust} disabled={runId === ""}>
            {t("budget.adjust")}
          </Button>
        }
      />
      <RunQueryBar
        runId={runId}
        busy={usage.phase === "loading"}
        onSelect={(id) => {
          if (id === runId) rest.onReload();
          else ctx.onSelectedRunIdChange(id);
        }}
      />
      {rest.adjusting && <BudgetAdjustBar runId={runId} onAdjusted={rest.onReload} />}
      <div className={styles.metrics}>
        {metrics.map(([label, value]) => (
          <MetricCard
            key={label}
            label={label}
            value={value}
            unknownWarn={value === "—" || value.includes("UNKNOWN")}
            sub={zh ? "来自后端 · UNKNOWN ≠ 0" : "Backend projection · UNKNOWN ≠ 0"}
          />
        ))}
      </div>
      {runId === "" && <EmptyState message={t("overview.noRun")} />}
      <ResourceBoundary state={forecast}>
        {forecast.data !== null && <ForecastTable view={forecast.data} />}
      </ResourceBoundary>
      <ResourceBoundary state={usage}>
        {usage.data !== null && <LedgerTables view={usage.data} />}
      </ResourceBoundary>
    </section>
  );
}
