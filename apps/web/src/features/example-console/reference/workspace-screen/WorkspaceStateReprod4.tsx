import { type Dispatch, type SetStateAction } from "react";
import FIX_EXPERIMENTS from "../../data/experiments.json";
import { DigestText } from "../DigestText";
import visual from "../WorkspaceScreen.module.css";
import { WorkspaceSection } from "./WorkspaceSection";
import { WorkspaceStateReprod5 } from "./WorkspaceStateReprod5";

interface WorkspaceStateReprod4Props {
  t: (key: string, fallback?: string) => string;
  setSelectedExp: Dispatch<SetStateAction<string>>;
  selectedExp: string;
}

export function WorkspaceStateReprod4({
  t,
  setSelectedExp,
  selectedExp,
}: WorkspaceStateReprod4Props) {
  return (
    <div className={visual.surface6}>
      <div className={`row head ${visual.surface7 ?? ""}`}>
        <span>{t("ws.colLabelId")}</span>
        <span>{t("ws.colMetrics")}</span>
        <span>{t("ws.colReprod")}</span>
        <span>{t("lbl.duration")}</span>
        <span>{t("lbl.started")}</span>
      </div>
      {FIX_EXPERIMENTS.map((e) => (
        <div
          key={e.experiment_run_id}
          onClick={() => {
            setSelectedExp(e.experiment_run_id);
          }}
          className={`row ${visual.surface8 ?? ""}`}
          style={{
            background: selectedExp === e.experiment_run_id ? "var(--bg-hover)" : undefined,
          }}
        >
          <div className={visual.surface9}>
            <div className={visual.label5}>{e.label}</div>
            <DigestText value={e.experiment_run_id} length={20} prefix={false} />
          </div>
          <WorkspaceSection {...{ e }} />
          <WorkspaceStateReprod5 {...{ e, t }} />
          <span className={`mono ${visual.label6 ?? ""}`}>
            {Math.floor(e.duration_s / 60)}m{e.duration_s % 60}s
          </span>
          <span className={visual.caption3}>{e.started_at.slice(11, 16)}</span>
        </div>
      ))}
    </div>
  );
}
