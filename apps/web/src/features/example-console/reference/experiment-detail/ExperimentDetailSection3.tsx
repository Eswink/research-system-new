import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentDetail.module.css";
import { Icon } from "../Icon";

interface ExperimentDetailSection3Props {
  e: FixtureTypes.Experiment;
  t: (key: string, fallback?: string) => string;
}

export function ExperimentDetailSection3({ e, t }: ExperimentDetailSection3Props) {
  return (
    <div className={visual.row8}>
      {e.status === "QUEUED" && (
        <button className="btn primary sm">
          <Icon name="play" size={10} /> {t("act.runNow")}
        </button>
      )}
      {e.status === "RUNNING" && (
        <button className="btn sm">
          <Icon name="pause" size={10} /> {t("act.pause")}
        </button>
      )}
      {(e.status === "PAUSED" || e.status === "QUEUED") && (
        <button className="btn sm">
          <Icon name="fork" size={10} /> {t("act.fork")}
        </button>
      )}
      {e.status === "FAILED" && (
        <button className="btn sm">
          <Icon name="spin" size={10} /> {t("act.retry")}
        </button>
      )}
      <button className="btn sm ghost">
        <Icon name="copy" size={10} /> {t("act.edit")}
      </button>
      <button className={`btn sm ghost ${visual.action ?? ""}`}>
        <Icon name="x" size={10} /> {t("tl.cancel")}
      </button>
    </div>
  );
}
