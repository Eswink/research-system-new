import { api } from "../../api/client";
import { Button } from "../../components/Button";
import { Chip } from "../../components/Chip";
import { Table, type Column } from "../../components/Table";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import type { BudgetViewDto } from "../../api/types";
import { useI18n } from "../../i18n/useI18n";
import { useResource } from "../../hooks/useResource";
import type { PageContext } from "../../navigation/pageContext";
import { GAPS } from "../../navigation/pageSupport";
import styles from "../shared/FeaturePage.module.css";

interface UsageRow {
  entry: string;
  resource: string;
  quantity: string;
  costStatus: string;
  minor: number | null;
  currency: string;
}

function usageRows(view: BudgetViewDto | null): UsageRow[] {
  return (view?.entries ?? []).map((e) => ({
    entry: e.entry_id,
    resource: e.resource_type,
    quantity: `${String(e.quantity)} ${e.unit}`.trim(),
    costStatus: e.cost_status,
    minor: e.estimated_cost_minor ?? e.actual_cost_minor,
    currency: e.currency,
  }));
}

function columnsFor(
  t: (
    key:
      | "cost.dimension"
      | "cost.status"
      | "cost.minor"
      | "cost.currency"
      | "budget.quantity",
  ) => string,
): Column<UsageRow>[] {
  return [
    {
      key: "resource",
      header: t("cost.dimension"),
      render: (r) => <Chip tone="neutral">{r.resource}</Chip>,
    },
    { key: "quantity", header: t("budget.quantity"), render: (r) => r.quantity },
    {
      key: "costStatus",
      header: t("cost.status"),
      render: (r) => (
        <Chip tone={r.costStatus === "KNOWN" ? "success" : "warn"}>{r.costStatus}</Chip>
      ),
    },
    {
      key: "minor",
      header: t("cost.minor"),
      align: "right",
      render: (r) => (r.minor === null ? "—" : String(r.minor)),
    },
    {
      key: "currency",
      header: t("cost.currency"),
      render: (r) => r.currency || "—",
    },
  ];
}

/**
 * 预算（T22）：usage/cost 真实金额；已知小计、未知条目、币种与预留如实展示。
 * 预算调整无契约（501）——禁用并说明。
 */
export function BudgetPage({ ctx }: { ctx: PageContext }) {
  const { t } = useI18n();
  const runId = ctx.selectedRunId;
  const usage = useResource(runId === "" ? null : runId, () => api.runUsage(runId));

  if (runId === "") {
    return <EmptyState message={t("overview.noRun")} />;
  }
  if (usage.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (usage.phase === "error") {
    return <ErrorState message={usage.error ?? t("state.error")} />;
  }
  const view = usage.data;
  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.govern.budget")}</h2>
        <Chip tone="accent">{`${t("run.context.label")}: ${runId.slice(0, 12)}`}</Chip>
        <span className={styles.spacer} />
        <Button disabledReason={GAPS.budgetAdjust}>{t("budget.adjust")}</Button>
      </div>
      <SummaryChips view={view} />
      <Table
        ariaLabel={t("page.govern.budget")}
        columns={columnsFor(t)}
        rows={usageRows(view)}
        rowKey={(r) => r.entry}
        empty={<EmptyState message={t("state.empty")} />}
      />
    </div>
  );
}

function SummaryChips({ view }: { view: BudgetViewDto | null }) {
  const { t } = useI18n();
  const unknown = view?.total_estimated_cost_minor === null;
  const subtotal = view?.known_cost_subtotal_minor ?? 0;
  const currency = view?.total_currency ?? "";
  const unknownCount = view?.unknown_cost_entries ?? 0;
  const reservationCount = view?.reservations.length ?? 0;
  return (
    <div className={styles.head}>
      <Chip tone={unknown ? "warn" : "success"}>
        {unknown ? t("overview.unknownCost") : `${String(subtotal)} ${currency}`}
      </Chip>
      <Chip tone="neutral">{`${String(unknownCount)} ${t("overview.unknownEntries")}`}</Chip>
      <Chip tone="neutral">{`${String(reservationCount)} ${t("budget.reservations")}`}</Chip>
    </div>
  );
}
