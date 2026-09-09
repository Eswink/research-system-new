import FIX_RUN from "../../data/run.json";
import { DigestText } from "../DigestText";
import { Icon } from "../Icon";
import { LiveIndicator } from "../LiveIndicator";
import { RunStateBadge } from "../RunStateBadge";
import visual from "../TimelineScreen.module.css";

interface TimelineSection9Props {
  t: (key: string, fallback?: string) => string;
  liveState: string;
}

export function TimelineSection9({ t, liveState }: TimelineSection9Props) {
  return (
    <div className={visual.row}>
      <div className={visual.row2}>
        <RunStateBadge state="RUNNING" />
        <span className={visual.label}>{FIX_RUN.id}</span>
      </div>
      <div className={`vr ${visual.surface ?? ""}`} />
      <DigestText value={FIX_RUN.manifest_digest} label="manifest:" length={12} />
      <DigestText value={FIX_RUN.protocol_digest} label="protocol:" length={10} />
      <div className={`vr ${visual.surface2 ?? ""}`} />
      <div className={visual.row3}>
        <span>
          <span className={visual.surface3}>{t("lbl.started").toLowerCase()}</span>{" "}
          2026-08-27T14:03:22Z
        </span>
        <span>
          <span className={visual.surface4}>{t("dr.elapsed")}</span> 00:38:12
        </span>
        <span>
          <span className={visual.surface5}>{t("lbl.tasks").toLowerCase()}</span>{" "}
          {FIX_RUN.progress.tasks_done}/{FIX_RUN.progress.tasks_total} ·{" "}
          <span className={visual.surface6}>
            {FIX_RUN.progress.tasks_running} {t("exp.running")}
          </span>{" "}
          ·{" "}
          <span className={visual.surface7}>
            {FIX_RUN.progress.tasks_failed} {t("rh.failed")}
          </span>
        </span>
      </div>
      <div className={visual.row4}>
        <LiveIndicator state={liveState} />
        <div className={`vr ${visual.surface8 ?? ""}`} />
        <button className="btn sm">
          <Icon name="pause" size={10} /> {t("act.pause")}
        </button>
        <button className="btn sm">
          <Icon name="fork" size={10} /> {t("act.fork")}
        </button>
        <button className={`btn sm ${visual.action ?? ""}`}>
          <Icon name="stop" size={10} /> {t("tl.cancel")}
        </button>
      </div>
    </div>
  );
}
