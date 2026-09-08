import { api } from "../../api/client";
import type { CostDimensionDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { EmptyState, ErrorState, LoadingState, UnavailableState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { useResource } from "../../hooks/useResource";
import type { PageContext } from "../../navigation/pageContext";
import { GAPS } from "../../navigation/pageSupport";
import styles from "../shared/FeaturePage.module.css";

interface CostRow {
  key: string;
  dimension: string;
  status: string;
  minor: number | null;
  currency: string;
  entries: number;
}

function costRows(dimensions: readonly CostDimensionDto[]): CostRow[] {
  return dimensions.map((d) => ({
    key: d.resource_key,
    dimension: d.dimension,
    status: d.amount.status,
    minor: d.amount.minor_units,
    currency: d.amount.currency,
    entries: d.entry_count,
  }));
}

function columnsFor(
  t: (key: "cost.dimension" | "cost.status" | "cost.minor" | "cost.currency") => string,
): Column<CostRow>[] {
  return [
    {
      key: "dimension",
      header: t("cost.dimension"),
      render: (r) => <Chip tone="neutral">{r.dimension}</Chip>,
    },
    { key: "key", header: "Key", render: (r) => <span className="mono">{r.key}</span> },
    {
      key: "status",
      header: t("cost.status"),
      render: (r) => <Chip tone={statusTone(r.status)}>{r.status}</Chip>,
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

function statusTone(status: string): "success" | "warn" | "danger" | "neutral" {
  if (status === "ACTUAL") {
    return "success";
  }
  if (
    status === "USAGE_UNKNOWN" ||
    status === "MONETARY_UNAVAILABLE" ||
    status === "CURRENCY_CONFLICT"
  ) {
    return "danger";
  }
  if (status === "ESTIMATED" || status === "PARTIALLY_METERED") {
    return "warn";
  }
  return "neutral";
}

/**
 * 成本分析（T22）：Run cost/usage 真实金额；保留未知、部分计量、币种冲突语义。
 * 无日序列/预测——折线图显示数据不可用，不画虚构折线。
 */
export function CostAnalyticsPage({ ctx }: { ctx: PageContext }) {
  const { t } = useI18n();
  const runId = ctx.selectedRunId;
  const cost = useResource(runId === "" ? null : runId, () => api.runCost(runId));

  if (runId === "") {
    return (
      <div className={styles.page}>
        <h2 className={styles.heading}>{t("page.insights.cost-analytics")}</h2>
        <EmptyState message={t("overview.noRun")} />
      </div>
    );
  }
  if (cost.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (cost.phase === "error") {
    return <ErrorState message={cost.error ?? t("state.error")} />;
  }
  const rows = costRows(cost.data?.dimensions ?? []);
  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.insights.cost-analytics")}</h2>
        <Chip tone="accent">{`${t("run.context.label")}: ${runId.slice(0, 12)}`}</Chip>
      </div>
      <Table
        ariaLabel={t("page.insights.cost-analytics")}
        columns={columnsFor(t)}
        rows={rows}
        rowKey={(r) => `${r.dimension}-${r.key}`}
        empty={<EmptyState message={t("state.empty")} />}
      />
      <UnavailableState title={t("cost.trend")} reason={GAPS.costSeries} />
    </div>
  );
}
