import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentQueue.module.css";
import { Icon } from "../Icon";
import { ExperimentQueueSection2 } from "./ExperimentQueueSection2";

interface ExperimentQueueSectionProps {
  t: (key: string, fallback?: string) => string;
  queue: FixtureTypes.Experiment[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export function ExperimentQueueSection({
  t,
  queue,
  selectedId,
  onSelect,
}: ExperimentQueueSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="flask" size={12} className={visual.surface} />
        <span className={visual.label}>{t("exp.queue")}</span>
        <span className="chip">{queue.length}</span>
        <span className={visual.caption}>
          {queue.filter((e) => e.status === "RUNNING").length} {t("exp.running")} ·{" "}
          {queue.filter((e) => e.status === "QUEUED").length} {t("exp.queued")}
        </span>
      </div>
      <ExperimentQueueSection2 {...{ queue, selectedId, onSelect }} />
    </div>
  );
}
