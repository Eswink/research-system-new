import type { BudgetViewDto } from "../../api/types";
import type { TranslationKey } from "../../i18n/zh";
import { api } from "../../api/client";
import { Button } from "../../components/Button";
import { MetricCard } from "../../components/charts/MetricCard";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { GAPS } from "../../navigation/pageSupport";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { ledgerSummary } from "./ledgerPresentation";
import { LedgerTables } from "./LedgerTables";

export function BudgetPage({ ctx }: { ctx: PageContext }) {
  const { language, t } = useI18n();
  const zh = language === "zh";
  const runId = ctx.selectedRunId;
  const usage = useResource(runId === "" ? null : runId, () => api.runUsage(runId));
  const summary = ledgerSummary(usage.phase === "ready" ? usage.data : null);
  const metrics = [
    [zh ? "总估算金额" : "Total estimated cost", summary.total],
    [zh ? "已知小计（不等于总额）" : "Known subtotal (not the total)", summary.subtotal],
    [zh ? "未知费用条目" : "Unknown-cost entries", summary.unknownEntries],
    [zh ? "资源预留" : "Reservations", summary.reservations],
  ] as const;
  return <BudgetPageGovernBudget {...{ t, zh, runId, usage, ctx, metrics }} />;
}

interface BudgetPageGovernBudgetProps {
  t: (key: TranslationKey) => string;
  zh: boolean;
  runId: string;
  usage: ResourceState<BudgetViewDto>;
  ctx: PageContext;
  metrics: readonly [
    readonly ["总估算金额" | "Total estimated cost", string],
    readonly ["已知小计（不等于总额）" | "Known subtotal (not the total)", string],
    readonly ["未知费用条目" | "Unknown-cost entries", string],
    readonly ["资源预留" | "Reservations", string],
  ];
}

function BudgetPageGovernBudget({
  t,
  zh,
  runId,
  usage,
  ctx,
  metrics,
}: BudgetPageGovernBudgetProps) {
  return (
    <section className={styles.page} data-testid="budget-page">
      <PageHeader
        title={t("page.govern.budget")}
        kicker="GOVERNANCE / BUDGET & USAGE"
        description={
          zh
            ? "当前运行的后端账本投影：保留原始单位、估算与实际金额，以及未知费用。"
            : [
                "Backend ledger projection for the selected run: original units, ",
                "estimated/actual amounts and unknown costs.",
              ].join("")
        }
        actions={<Button disabledReason={GAPS.budgetAdjust}>{t("budget.adjust")}</Button>}
      />
      <RunQueryBar
        runId={runId}
        busy={usage.phase === "loading"}
        onSelect={(id) => {
          if (id === runId) usage.reload();
          else ctx.onSelectedRunIdChange(id);
        }}
      />
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
      <ResourceBoundary state={usage}>
        {usage.data !== null && <LedgerTables view={usage.data} />}
      </ResourceBoundary>
    </section>
  );
}
