import type { TranslationKey } from "../../i18n/zh";
import { api } from "../../api/client";
import type { BudgetViewDto, ClaimMapDto, RunDetailDto, TaskDto } from "../../api/types";
import { MetricCard } from "../../components/charts/MetricCard";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { ClaimsMetric, TasksMetric, UsageMetric } from "./OverviewMetrics";

/** Every metric is scoped to the selected persisted run. Missing queries never become zeros. */
export function OverviewPage({ ctx }: { ctx: PageContext }) {
  const { language, t } = useI18n();
  const runId = ctx.selectedRunId;
  const key = runId === "" ? null : runId;
  const run = useResource(key, () => api.getRun(runId));
  const tasks = useResource(key, () => api.runTasks(runId));
  const claims = useResource(key, () => api.runClaimMap(runId));
  const usage = useResource(key, () => api.runUsage(runId));
  const refresh = () => {
    run.reload();
    tasks.reload();
    claims.reload();
    usage.reload();
  };
  return (
    <OverviewPagePlanOverview
      {...{ t, language, runId, refresh, ctx, run, tasks, claims, usage }}
    />
  );
}

function DegradedClaimsNotice({ degraded, language }: { degraded: boolean; language: string }) {
  if (!degraded) return null;
  return (
    <p className={styles.notice} role="status">
      {language === "zh"
        ? "论断图已降级：存在无法完整投影的账本记录，不能据此推断研究已验证。"
        : [
            "Claim map degraded: some ledger records could not be projected. ",
            "Verification is not implied.",
          ].join("")}
    </p>
  );
}

interface OverviewPagePlanOverviewProps {
  t: (key: TranslationKey) => string;
  language: string;
  runId: string;
  refresh: () => void;
  ctx: PageContext;
  run: ResourceState<RunDetailDto>;
  tasks: ResourceState<TaskDto[]>;
  claims: ResourceState<ClaimMapDto>;
  usage: ResourceState<BudgetViewDto>;
}

function OverviewPagePlanOverview({
  t,
  language,
  runId,
  refresh,
  ctx,
  run,
  tasks,
  claims,
  usage,
}: OverviewPagePlanOverviewProps) {
  return (
    <section className={styles.page} data-testid="overview-page">
      <OverviewPagePlanOverview2 {...{ t, language, runId, refresh, ctx, run }} />
      <div className={styles.metrics}>
        <TasksMetric data={tasks.phase === "ready" ? tasks.data : null} />
        <ClaimsMetric data={claims.phase === "ready" ? claims.data : null} />
        <UsageMetric data={usage.phase === "ready" ? usage.data : null} />
        <MetricCard
          label={language === "zh" ? "运行状态" : "Run state"}
          value={run.phase === "ready" ? (run.data?.state ?? "UNKNOWN") : "—"}
          sub={run.data?.protocol_id ?? t("overview.noRun")}
          unknownWarn={run.phase !== "ready"}
        />
      </div>
      <div className={styles.split}>
        <div className={styles.page}>
          <ResourceBoundary state={run}>
            <RunMetadata run={run.data} />
          </ResourceBoundary>
          <QuickNavigation runId={runId} />
        </div>
        <ResourceBoundary state={tasks}>
          <TaskSnapshot tasks={tasks.data} />
        </ResourceBoundary>
      </div>
      <ResourceBoundary state={claims}>
        <DegradedClaimsNotice degraded={claims.data?.degraded === true} language={language} />
      </ResourceBoundary>
      <ResourceBoundary state={usage}>{null}</ResourceBoundary>
    </section>
  );
}

interface OverviewPagePlanOverview2Props {
  t: (key: TranslationKey) => string;
  language: string;
  runId: string;
  refresh: () => void;
  ctx: PageContext;
  run: ResourceState<RunDetailDto>;
}

function OverviewPagePlanOverview2({
  t,
  language,
  runId,
  refresh,
  ctx,
  run,
}: OverviewPagePlanOverview2Props) {
  return (
    <PageHeader
      title={t("page.plan.overview")}
      kicker="PLAN / RESEARCH OVERVIEW"
      description={
        language === "zh"
          ? "当前运行的计划、执行、论断与账本投影。没有预检报告时不推断预检通过。"
          : [
              "Selected run: plan, execution, claims and ledger. Absence of a preflight ",
              "report does not imply a pass.",
            ].join("")
      }
      actions={
        <RunQueryBar
          runId={runId}
          onSelect={(id) => {
            if (id === runId) refresh();
            else ctx.onSelectedRunIdChange(id);
          }}
          busy={run.phase === "loading"}
        />
      }
    />
  );
}

function RunMetadata({ run }: { run: RunDetailDto | null }) {
  const { language, t } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection
      title={zh ? "计划与冻结身份" : "Plan and frozen identity"}
      extra={
        <Chip tone={run?.manifest_digest == null ? "unknown" : "accent"}>
          {run?.manifest_digest == null ? "NOT FROZEN" : "FROZEN"}
        </Chip>
      }
    >
      {run === null ? (
        <EmptyState message={t("overview.noRun")} />
      ) : (
        <KeyValueList
          fields={[
            { label: "Run", value: run.id },
            { label: "Protocol", value: run.protocol_id },
            { label: "Project", value: run.project_id },
            { label: "Manifest", value: run.manifest_digest ?? "—" },
            { label: zh ? "创建时间" : "Created", value: run.created_at },
            { label: zh ? "更新时间" : "Updated", value: run.updated_at },
          ]}
        />
      )}
    </PanelSection>
  );
}

function QuickNavigation({ runId }: { runId: string }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const links = [
    ["plan/protocol", zh ? "编辑协议与预检" : "Protocol and preflight"],
    ["plan/team", zh ? "配置研究团队" : "Configure research team"],
    ["run/timeline", zh ? "查看运行时间线" : "Inspect run timeline"],
    ["portfolio/runs-history", zh ? "浏览历史运行" : "Browse run history"],
    ["evidence/claims", zh ? "检查论断与证据" : "Inspect claims and evidence"],
  ] as const;
  return (
    <PanelSection title={zh ? "工作流入口" : "Workflow shortcuts"}>
      <div className={styles.list}>
        {links.map(([route, label]) => (
          <a
            key={route}
            href={`#/${route}${runId === "" ? "" : `?run=${encodeURIComponent(runId)}`}`}
            className="btn ghost"
          >
            {label} →
          </a>
        ))}
      </div>
    </PanelSection>
  );
}

function TaskSnapshot({ tasks }: { tasks: TaskDto[] | null }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection title={zh ? "执行任务快照" : "Execution task snapshot"}>
      {tasks === null || tasks.length === 0 ? (
        <EmptyState message={zh ? "没有已读取的执行任务" : "No loaded execution tasks"} />
      ) : (
        <ul className={styles.list}>
          {tasks.slice(0, 12).map((task) => (
            <li key={task.task_id} className={styles.card}>
              <div className={styles.cardHead}>
                <strong>{task.contract_id}</strong>
                <Chip>{task.status}</Chip>
              </div>
              <span className="mono">{task.task_id}</span>
              <br />
              <span>
                {task.agent_id ?? "UNASSIGNED"} · attempt {task.attempt}
              </span>
            </li>
          ))}
        </ul>
      )}
      {tasks !== null && tasks.length > 12 && (
        <p className={styles.notice}>
          {zh
            ? "仅展示前 12 条，完整任务见时间线。"
            : "First 12 tasks shown; the timeline contains all tasks."}
        </p>
      )}
    </PanelSection>
  );
}
