import type { RunDetailDto, TaskDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import type { RunSelectionProps } from "../shared/useSelectedRun";
import { RunActions } from "./RunActions";
import { RebuildReadiness } from "./RebuildReadiness";
import { TimelineView } from "./TimelineView";
import { useRunTimeline } from "./useRunTimeline";

export function RunPanel(props: RunSelectionProps = {}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const flow = useRunTimeline(props);
  return <RunPanelsection {...{ zh, flow }} />;
}

interface RunPanelsectionProps {
  zh: boolean;
  flow: ReturnType<typeof useRunTimeline>;
}

function RunPanelsection({ zh, flow }: RunPanelsectionProps) {
  return (
    <section className={styles.page} data-testid="run-panel">
      <RunPanelPageHeader {...{ zh, flow }} />
      <RunNavigation />
      <ResourceBoundary state={flow.run}>
        {flow.run.data !== null && <RunIdentity run={flow.run.data} flow={flow} />}
      </ResourceBoundary>
      <ResourceBoundary state={flow.run}>
        {flow.run.data !== null && <RebuildReadiness rebuild={flow.run.data.rebuild} />}
      </ResourceBoundary>
      {flow.runId === "" ? (
        <div data-testid="runs-empty">
          <EmptyState
            message={
              zh
                ? "选择历史运行，或先在协议编辑器完成编译与预检。"
                : "Select a historical run, or compile and preflight a protocol first."
            }
          />
        </div>
      ) : (
        <div className={styles.split}>
          <ResourceBoundary state={flow.tasks}>
            <TaskList tasks={flow.tasks.data ?? []} />
          </ResourceBoundary>
          <ResourceBoundary state={flow.replay}>
            <TimelineView events={flow.events} />
          </ResourceBoundary>
        </div>
      )}
      {flow.stream.invalidFrames > 0 && (
        <p className={styles.notice} role="status">
          {zh
            ? "忽略了格式无效或 Run 不匹配的事件帧："
            : "Ignored invalid or mismatched event frames: "}
          {flow.stream.invalidFrames}
        </p>
      )}
    </section>
  );
}

interface RunPanelPageHeaderProps {
  zh: boolean;
  flow: ReturnType<typeof useRunTimeline>;
}

function RunPanelPageHeader({ zh, flow }: RunPanelPageHeaderProps) {
  return (
    <PageHeader
      title={zh ? "运行时间线" : "Run timeline"}
      kicker="RUN / EXECUTION"
      description={
        zh
          ? "正式事件回放 + SSE 增量；运行状态来自后端，模型推理身份以 Manifest 为准。"
          : [
              "Persisted event replay plus SSE updates. Run state is backend-owned; ",
              "inference identity comes from the manifest.",
            ].join("")
      }
      actions={
        <RunQueryBar
          runId={flow.runId}
          busy={flow.run.phase === "loading"}
          onSelect={(id) => {
            if (id === flow.runId) flow.refresh();
            else flow.selectRun(id);
          }}
        />
      }
    />
  );
}

function RunNavigation() {
  const { language } = useI18n();
  return (
    <div className={styles.toolbar}>
      <a href="#/plan/protocol" className="btn primary sm" data-testid="run-start">
        {language === "zh" ? "协议 · 编译 · 预检" : "Protocol · compile · preflight"}
      </a>
      <a href="#/portfolio/runs-history" className="btn sm">
        {language === "zh" ? "选择历史运行" : "Select historical run"}
      </a>
      <span className="muted" data-testid="run-runtime-note">
        {language === "zh"
          ? "此页不会直接启动未预检运行。"
          : "This page cannot start an un-preflighted run."}
      </span>
    </div>
  );
}

function RunIdentity({
  run,
  flow,
}: {
  run: RunDetailDto;
  flow: ReturnType<typeof useRunTimeline>;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const connection = flow.stream.connected
    ? "CONNECTED"
    : flow.stream.reconnecting
      ? "RECONNECTING"
      : "CONNECTING";
  return (
    <PanelSection
      title={zh ? "运行身份与连接" : "Run identity and connection"}
      extra={
        <RunActions
          key={run.id}
          run={run}
          busy={flow.run.phase !== "ready"}
          onChanged={flow.refresh}
        />
      }
    >
      <div className={styles.toolbar}>
        <span data-testid="run-state">
          <Chip tone="accent">{run.state}</Chip>
        </span>
        <span data-testid="run-live-state">
          <Chip>{`SSE · ${connection}`}</Chip>
        </span>
        <span className="muted">
          {zh ? "连接状态不等于执行进度" : "Connection state is not execution progress"}
        </span>
      </div>
      <RunIdentityFacts run={run} zh={zh} />
    </PanelSection>
  );
}

/** 身份事实表（含执行体与运行时指纹两行；GOAL-007 EC-04）。 */
function RunIdentityFacts({ run, zh }: { run: RunDetailDto; zh: boolean }) {
  return (
    <KeyValueList
      fields={[
        { label: "Run", value: run.id },
        { label: "Protocol", value: run.protocol_id },
        { label: "Manifest", value: run.manifest_digest ?? "NOT FROZEN" },
        {
          label: zh ? "执行体" : "Execution",
          value: <span data-testid="run-execution-backend">{executionBackendLabel(run, zh)}</span>,
        },
        {
          label: zh ? "运行时指纹" : "Runtime fingerprint",
          value: <span data-testid="run-runtime-fingerprint">{fingerprintLabel(run, zh)}</span>,
        },
      ]}
    />
  );
}

/** 执行体读面文案（GOAL-007 EC-04）：未冻结 / 未声明 / 具体基质三态分开说。 */
function executionBackendLabel(run: RunDetailDto, zh: boolean): string {
  if (run.execution === null) return zh ? "未冻结" : "NOT FROZEN";
  if (run.execution.execution_backend === null) return zh ? "未声明" : "UNDECLARED";
  return run.execution.execution_backend;
}

/** 指纹读面文案：只报**状态**，`NOT_VERIFIED` 时连同原因一起显示，不冒充指纹值。 */
function fingerprintLabel(run: RunDetailDto, zh: boolean): string {
  const fingerprint = run.execution?.runtime_fingerprint ?? null;
  if (fingerprint === null) return zh ? "未声明" : "UNDECLARED";
  if (fingerprint.status !== "VERIFIED" && fingerprint.reason) {
    return `${fingerprint.status} · ${fingerprint.reason}`;
  }
  return fingerprint.status;
}

function TaskList({ tasks }: { tasks: TaskDto[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div data-testid="run-tasks">
      <PanelSection title={zh ? "任务" : "Tasks"} count={tasks.length}>
        {tasks.length === 0 ? (
          <EmptyState message={zh ? "没有已记录任务" : "No recorded tasks"} />
        ) : (
          <ul className={styles.list}>
            {tasks.map((task) => (
              <li key={task.task_id} className={styles.card}>
                <div className={styles.cardHead}>
                  <strong>{task.contract_id}</strong>
                  <Chip>{task.status}</Chip>
                </div>
                <KeyValueList
                  fields={[
                    { label: "Task", value: task.task_id },
                    { label: "Agent", value: task.agent_id ?? "UNASSIGNED" },
                    { label: "Attempt", value: task.attempt },
                  ]}
                />
              </li>
            ))}
          </ul>
        )}
      </PanelSection>
    </div>
  );
}
