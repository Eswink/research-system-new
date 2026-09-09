import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../SchedulesScreen.module.css";
import { SchedulesSection2 } from "./SchedulesSection2";

interface SchedulesSectionProps {
  t: (key: string, fallback?: string) => string;
  schedules: FixtureTypes.Schedule[];
  setSchedules: Dispatch<SetStateAction<FixtureTypes.Schedule[]>>;
}

export function SchedulesSection({ t, schedules, setSchedules }: SchedulesSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={`row head ${visual.surface ?? ""}`}>
        <span>{t("al.colOn")}</span>
        <span>{t("sc.colSchedule")}</span>
        <span>{t("lbl.cron")}</span>
        <span>{t("lbl.target")}</span>
        <span>{t("lbl.lastRun")}</span>
        <span>{t("lbl.nextRun")}</span>
        <span>{t("lbl.streak")}</span>
      </div>
      <SchedulesSection2 {...{ schedules, setSchedules, t }} />
    </div>
  );
}
