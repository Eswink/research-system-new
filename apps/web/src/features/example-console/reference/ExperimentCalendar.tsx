import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ExperimentCalendarSection } from "./experiment-calendar/ExperimentCalendarSection";
import visual from "./ExperimentCalendar.module.css";

export const ExperimentCalendar = ({ experiments }: { experiments: E.Experiment[] }) => {
  const { t } = useI18n();
  const days = 7;
  const hours = [8, 10, 12, 14, 16, 18, 20, 22];
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.surface}>
        <div className={visual.caption}>{t("exp.calTitle")}</div>
        <div className={visual.label}>{t("exp.calRange")}</div>
      </div>
      <ExperimentCalendarSection {...{ days, hours, experiments }} />
    </div>
  );
};
