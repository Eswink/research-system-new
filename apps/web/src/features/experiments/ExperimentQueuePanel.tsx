import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { ExperimentQueueEntryDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, ErrorState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { ExperimentEnqueueForm } from "./ExperimentEnqueueForm";

type Tone = "neutral" | "accent" | "success" | "warn" | "danger";

const STATE_TONES: Record<string, Tone> = {
  QUEUED: "accent",
  DISPATCHING: "warn",
  DISPATCHED: "success",
  FAILED: "danger",
  CANCELLED: "neutral",
};

function toneOf(state: string): Tone {
  return STATE_TONES[state] ?? "neutral";
}

/** G14 实验队列与调度：入队 / 改期 / 取消 / 派发结果（状态来自控制面）。 */
export function ExperimentQueuePanel() {
  const { language } = useI18n();
  const zh = language === "zh";
  const queue = useResource("experiment-queue", () => api.experimentQueue());
  const plans = useResource("experiment-plans", () => api.experimentPlans("PREREGISTERED"));
  return (
    <PanelSection
      title={zh ? "实验队列与调度" : "Experiment queue and scheduling"}
      count={queue.data?.entries.length}
    >
      <div className={styles.page} data-testid="experiment-queue-panel">
        <ExperimentEnqueueForm plans={plans.data ?? []} onEnqueued={queue.reload} />
        <QueueRows view={queue} zh={zh} onChanged={queue.reload} />
        {queue.data !== null && <p className={styles.notice}>{queue.data.dispatch_note}</p>}
      </div>
    </PanelSection>
  );
}

type QueueView = Awaited<ReturnType<typeof api.experimentQueue>>;

function QueueRows({
  view,
  zh,
  onChanged,
}: {
  view: ReturnType<typeof useResource<QueueView>>;
  zh: boolean;
  onChanged: () => void;
}) {
  const rows = view.data?.entries ?? [];
  return (
    <ResourceBoundary state={view}>
      {view.phase === "ready" && rows.length === 0 && (
        <EmptyState message={zh ? "队列为空（无排队条目）" : "Queue is empty"} />
      )}
      {rows.length > 0 && (
        <ul className={styles.list} data-testid="queue-rows">
          {rows.map((entry) => (
            <QueueRow key={entry.id} entry={entry} zh={zh} onChanged={onChanged} />
          ))}
        </ul>
      )}
    </ResourceBoundary>
  );
}

function QueueRow({
  entry,
  zh,
  onChanged,
}: {
  entry: ExperimentQueueEntryDto;
  zh: boolean;
  onChanged: () => void;
}) {
  const [when, setWhen] = useState(localInputValue(entry.not_before));
  const [issue, setIssue] = useState<string | null>(null);
  const act = async (call: () => Promise<unknown>): Promise<void> => {
    setIssue(null);
    try {
      await call();
      onChanged();
    } catch (err) {
      setIssue(problemText(err));
    }
  };
  return (
    <li className={styles.notice} data-testid={`queue-row-${entry.id}`}>
      <span className="mono">{entry.plan_name ?? entry.plan_id}</span>{" "}
      <Chip tone={toneOf(entry.state)}>{entry.state}</Chip> ·{" "}
      <span className="mono">{sourceLabel(entry)}</span>
      <ScheduleNote entry={entry} zh={zh} />
      <RunNote runId={entry.run_id} />
      {entry.failure_reason !== null && (
        <span data-testid={`queue-failure-${entry.id}`}> · {entry.failure_reason}</span>
      )}
      {entry.state === "QUEUED" && (
        <QueueRowActions entry={entry} when={when} setWhen={setWhen} act={act} zh={zh} />
      )}
      {issue !== null && <ErrorState message={issue} />}
    </li>
  );
}

function ScheduleNote({ entry, zh }: { entry: ExperimentQueueEntryDto; zh: boolean }) {
  if (entry.not_before === null) return null;
  return (
    <span>
      {" "}
      · {zh ? "排期" : "from"} <span className="mono">{entry.not_before}</span>
    </span>
  );
}

function RunNote({ runId }: { runId: string | null }) {
  if (runId === null) return null;
  return (
    <span>
      {" "}
      · run <a href={`#/run/timeline?run=${encodeURIComponent(runId)}`}>{runId}</a>
    </span>
  );
}

function QueueRowActions({
  entry,
  when,
  setWhen,
  act,
  zh,
}: {
  entry: ExperimentQueueEntryDto;
  when: string;
  setWhen: (value: string) => void;
  act: (call: () => Promise<unknown>) => Promise<void>;
  zh: boolean;
}) {
  return (
    <span className={styles.toolbar}>
      <input
        className="input"
        type="datetime-local"
        aria-label={zh ? "改期" : "Reschedule"}
        value={when}
        onChange={(event) => {
          setWhen(event.target.value);
        }}
      />
      <button
        className="btn sm"
        type="button"
        onClick={() => {
          void act(() =>
            api.rescheduleExperiment(entry.id, when === "" ? null : new Date(when).toISOString()),
          );
        }}
      >
        {zh ? "改期" : "Reschedule"}
      </button>
      <button
        className="btn sm ghost"
        type="button"
        onClick={() => {
          void act(() => api.cancelExperiment(entry.id));
        }}
      >
        {zh ? "取消" : "Cancel"}
      </button>
    </span>
  );
}

function sourceLabel(entry: ExperimentQueueEntryDto): string {
  if (entry.protocol_path !== null) return entry.protocol_path;
  if (entry.draft_id !== null) return `${entry.draft_id}@r${String(entry.draft_revision ?? 0)}`;
  return "UNKNOWN SOURCE";
}

/** ISO（UTC）→ datetime-local 控件值（浏览器本地时区，仅展示层换算）。 */
function localInputValue(iso: string | null): string {
  if (iso === null) return "";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return "";
  const offsetMs = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - offsetMs).toISOString().slice(0, 16);
}
