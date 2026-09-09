import { useState } from "react";
import FIX_SCHEDULES from "../data/schedules.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { SchedulesTitle } from "./schedules-screen/SchedulesTitle";

export const SchedulesScreen = () => {
  const { t } = useI18n();
  const [drawer, setDrawer] = useState<{ mode?: string } | null>(null);
  const [schedules, setSchedules] = useState(FIX_SCHEDULES);

  return <SchedulesTitle {...{ t, setDrawer, schedules, setSchedules, drawer }} />;
};
