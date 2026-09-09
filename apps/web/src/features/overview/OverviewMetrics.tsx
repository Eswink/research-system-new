import type { BudgetViewDto, ClaimMapDto, TaskDto } from "../../api/types";
import { MetricCard } from "../../components/charts/MetricCard";
import { useI18n } from "../../i18n/useI18n";
import { claimSummary, taskProgress, usageSummary } from "./overviewPresentation";

export function TasksMetric({ data }: { data: TaskDto[] | null }) {
  const { t } = useI18n();
  const progress = taskProgress(data);
  return (
    <MetricCard
      label={t("overview.tasks")}
      unknownWarn={progress === null}
      value={progress === null ? "—" : `${String(progress.done)} / ${String(progress.total)}`}
      sub={t("overview.tasksDone")}
      bar={progress?.ratio}
    />
  );
}

export function ClaimsMetric({ data }: { data: ClaimMapDto | null }) {
  const { language, t } = useI18n();
  const summary = claimSummary(data);
  const zh = language === "zh";
  const subtitle =
    summary === null
      ? zh
        ? "尚未读取"
        : "Not loaded"
      : `${String(summary.unsupported)} ${t("overview.unsupported")} · ` +
        `${String(summary.disputed)} ${zh ? "争议" : "disputed"}`;
  return (
    <MetricCard
      label={t("overview.claims")}
      value={summary === null ? "—" : String(summary.total)}
      sub={summary?.degraded === true ? `${subtitle} · DEGRADED` : subtitle}
      unknownWarn={summary === null || summary.degraded}
    />
  );
}

export function UsageMetric({ data }: { data: BudgetViewDto | null }) {
  const { language, t } = useI18n();
  const summary = usageSummary(data);
  const zh = language === "zh";
  const total = summary?.total;
  const known = total !== null && total !== undefined;
  return (
    <MetricCard
      label={t("overview.cost")}
      value={known ? String(total) : t("overview.unknownCost")}
      unknownWarn={!known}
      sub={
        summary === null
          ? zh
            ? "账本尚未读取"
            : "Ledger not loaded"
          : `${summary.currency ?? "UNKNOWN CURRENCY"} minor units · ` +
            `${String(summary.unknownEntries)} ${t("overview.unknownEntries")}`
      }
    />
  );
}
