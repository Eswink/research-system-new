import * as React from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ExperimentCalendar.module.css";

interface ExperimentCalendarSectionProps {
  days: number;
  hours: number[];
  experiments: FixtureTypes.Experiment[];
}

export function ExperimentCalendarSection({
  days,
  hours,
  experiments,
}: ExperimentCalendarSectionProps) {
  return (
    <div
      className={visual.grid}
      style={{ gridTemplateColumns: `56px repeat(${String(days)}, 1fr)` }}
    >
      <div />
      {Array.from({ length: days }).map((_, day) => (
        <CalendarDayHeader key={day} day={day} />
      ))}
      {hours.map((h) => (
        <React.Fragment key={h}>
          <div className={visual.caption3}>{String(h).padStart(2, "0")}:00</div>
          {Array.from({ length: days }).map((_, day) => (
            <CalendarExperimentCell key={day} {...{ day, hour: h, experiments }} />
          ))}
        </React.Fragment>
      ))}
    </div>
  );
}

const WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"] as const;

function CalendarDayHeader({ day }: { day: number }) {
  const date = new Date(2026, 7, 26 + day);
  const weekdayIndex = date.getDay() === 0 ? 6 : date.getDay() - 1;
  return (
    <div className={visual.caption2}>
      <div>{WEEKDAYS[weekdayIndex]}</div>
      <div className={visual.label2}>{date.getDate()}</div>
    </div>
  );
}

interface CalendarExperimentCellProps {
  day: number;
  hour: number;
  experiments: FixtureTypes.Experiment[];
}

function CalendarExperimentCell({ day, hour, experiments }: CalendarExperimentCellProps) {
  const hasExperiment = (day * 7 + hour) % 5 < 2;
  const experiment = experiments[(day + hour) % experiments.length];
  const durationMinutes = Math.round((experiment?.duration_s ?? 1200) / 60);
  return (
    <div
      className={visual.surface2}
      style={{
        background: hasExperiment ? "var(--accent-dim)" : "var(--bg-sunken)",
        border: `1px solid ${hasExperiment ? "var(--accent-line)" : "var(--border-subtle)"}`,
      }}
    >
      {hasExperiment && experiment && (
        <>
          <div className={visual.caption4}>{experiment.label.slice(0, 22)}</div>
          <div className={visual.caption5}>~{durationMinutes}m</div>
        </>
      )}
    </div>
  );
}
