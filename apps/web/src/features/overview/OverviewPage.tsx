import { api } from "../../api/client";
import type { BudgetViewDto, ClaimMapDto, RunDetailDto, TaskDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { MetricCard } from "../../components/charts/MetricCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import styles from "./OverviewPage.module.css";

/**
 * 概览（T17）：只聚合当前选定 Run 的真实数据（详情/任务/论断/用量）。
 * 无运行或无预检时显示未选择/未执行，不自动发起预检探测。
 */
export function OverviewPage({ ctx }: { ctx: PageContext }) {
  const { t } = useI18n();
  const runId = ctx.selectedRunId;
  const key = runId === "" ? null : runId;
  const run = useResource(key, () => api.getRun(runId));
  const tasks = useResource(key, () => api.runTasks(runId));
  const claims = useResource(key, () => api.runClaimMap(runId));
  const usage = useResource(key, () => api.runUsage(runId));

  if (runId === "") {
    return (
      <div className={styles.page}>
        <h2 className={styles.heading}>{t("page.plan.overview")}</h2>
        <EmptyState message={t("overview.noRun")} />
      </div>
    );
  }
  if (run.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (run.phase === "error") {
    return <ErrorState message={run.error ?? t("state.error")} />;
  }
  return <OverviewBody run={run} tasks={tasks} claims={claims} usage={usage} />;
}

function OverviewBody(props: {
  run: ResourceState<RunDetailDto>;
  tasks: ResourceState<TaskDto[]>;
  claims: ResourceState<ClaimMapDto>;
  usage: ResourceState<BudgetViewDto>;
}) {
  const { t } = useI18n();
  const done = props.tasks.data?.filter((task) => task.status === "SUCCEEDED").length ?? 0;
  const total = props.tasks.data?.length ?? 0;
  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.plan.overview")}</h2>
        <Chip tone="accent">{props.run.data?.state ?? "UNKNOWN"}</Chip>
      </div>
      <div className={styles.grid}>
        <MetricCard
          label={t("overview.tasks")}
          value={`${String(done)} / ${String(total)}`}
          sub={t("overview.tasksDone")}
          bar={total > 0 ? done / total : undefined}
        />
        <ClaimsCard data={props.claims.data} />
        <UsageCard data={props.usage.data} />
      </div>
    </div>
  );
}

function ClaimsCard({ data }: { data: ClaimMapDto | null }) {
  const { t } = useI18n();
  const unsupported = data?.unsupported_claims.length ?? 0;
  return (
    <MetricCard
      label={t("overview.claims")}
      value={String(data?.claims.length ?? 0)}
      sub={`${String(unsupported)} ${t("overview.unsupported")}`}
      unknownWarn={data === null}
    />
  );
}

function UsageCard({ data }: { data: BudgetViewDto | null }) {
  const { t } = useI18n();
  const unknown = data?.total_estimated_cost_minor === null;
  const subtotal = data?.known_cost_subtotal_minor ?? 0;
  const currency = data?.total_currency ?? "";
  return (
    <MetricCard
      label={t("overview.cost")}
      value={unknown ? t("overview.unknownCost") : `${String(subtotal)} ${currency}`}
      sub={`${String(data?.unknown_cost_entries ?? 0)} ${t("overview.unknownEntries")}`}
      unknownWarn={unknown}
    />
  );
}
