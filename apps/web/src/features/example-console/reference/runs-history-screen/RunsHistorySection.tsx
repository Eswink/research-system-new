import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { DigestText } from "../DigestText";
import { LiveIndicator } from "../LiveIndicator";
import { RunStateBadge } from "../RunStateBadge";
import visual from "../RunsHistoryScreen.module.css";
import { fmtDuration } from "../fmtDuration";
import { RunsHistoryLabel } from "./RunsHistoryLabel";

interface RunsHistorySectionProps {
  filtered: FixtureTypes.Run[];
  selectedIds: string[];
  setSelectedIds: Dispatch<SetStateAction<string[]>>;
  t: (key: string, fallback?: string) => string;
}

export function RunsHistorySection({
  filtered,
  selectedIds,
  setSelectedIds,
  t,
}: RunsHistorySectionProps) {
  return (
    <div className={visual.surface2}>
      {filtered.map((run) => (
        <RunHistoryRow key={run.id} {...{ run, selectedIds, setSelectedIds, t }} />
      ))}
    </div>
  );
}

function RunTaskCounts({ run, t }: { run: FixtureTypes.Run; t: RunsHistorySectionProps["t"] }) {
  return (
    <span className={visual.label3}>
      <span className={visual.surface5}>{run.tasks_done}</span>/<span>{run.tasks_total}</span>
      {run.tasks_failed > 0 && (
        <span className={visual.surface6}>
          {" "}
          · {run.tasks_failed} {t("rh.fail")}
        </span>
      )}
    </span>
  );
}

function RunHistoryRow({
  run: r,
  selectedIds,
  setSelectedIds,
  t,
}: {
  run: FixtureTypes.Run;
  selectedIds: string[];
  setSelectedIds: Dispatch<SetStateAction<string[]>>;
  t: RunsHistorySectionProps["t"];
}) {
  const on = selectedIds.includes(r.id);
  return (
    <div
      className={`row ${visual.surface3 ?? ""}`}
      style={{
        background: on ? "var(--accent-dim)" : undefined,
        borderLeft: `2px solid ${on ? "var(--accent)" : "transparent"}`,
      }}
    >
      <RunsHistoryLabel {...{ on, setSelectedIds, r }} />
      <div className={`row-cell-wrap ${visual.surface4 ?? ""}`}>
        <div className={visual.row}>
          <span className={visual.label}>{r.label}</span>
          {r.live && <LiveIndicator state="live" />}
        </div>
        <DigestText value={r.id} length={16} prefix={false} />
      </div>
      <span>
        <RunStateBadge state={r.state} />
      </span>
      <span className={visual.label2}>{fmtDuration(r.duration_s)}</span>
      <RunTaskCounts run={r} t={t} />
      <span className={visual.label4}>${(r.spent_minor / 100000).toFixed(2)}</span>
      <span
        className={`mono ${visual.caption ?? ""}`}
        style={{ color: r.autonomy === "GUARDED_AUTONOMOUS" ? "var(--warn)" : "var(--fg-muted)" }}
      >
        {r.autonomy.replace("_", " ")}
      </span>
      <span className={visual.caption2}>
        {new Date(r.started_at).toISOString().replace("T", " ").slice(0, 16)}
      </span>
    </div>
  );
}
