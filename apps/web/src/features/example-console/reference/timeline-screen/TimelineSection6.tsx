import FIX_PHASES from "../../data/phases.json";
import { Icon } from "../Icon";
import visual from "../TimelineScreen.module.css";
import { TimelineSection } from "./TimelineSection";

interface TimelineSection6Props {
  t: (key: string, fallback?: string) => string;
  totalDuration: number;
}

export function TimelineSection6({ t, totalDuration }: TimelineSection6Props) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <div className={visual.row5}>
        <Icon name="hex" size={12} className={visual.surface9} />
        <span className={visual.label2}>{t("tl.phasesTasks")}</span>
        <span className="chip">{FIX_PHASES.reduce((a, p) => a + p.tasks.length, 0)}</span>
        <div className={visual.row6}>
          {["SUCCEEDED", "RUNNING", "FAILED", "PENDING"].map((s) => {
            const count = FIX_PHASES.flatMap((p) => p.tasks).filter((t) => t.status === s).length;
            return (
              <span
                key={s}
                className="chip"
                style={{
                  color:
                    s === "SUCCEEDED"
                      ? "var(--success)"
                      : s === "RUNNING"
                        ? "var(--accent)"
                        : s === "FAILED"
                          ? "var(--danger)"
                          : "var(--fg-faint)",
                  borderColor:
                    s === "SUCCEEDED"
                      ? "var(--success-line)"
                      : s === "RUNNING"
                        ? "var(--accent-line)"
                        : s === "FAILED"
                          ? "var(--danger-line)"
                          : "var(--border)",
                }}
              >
                {s.toLowerCase()} {count}
              </span>
            );
          })}
        </div>
      </div>
      <TimelineSection {...{ totalDuration }} />
    </div>
  );
}
