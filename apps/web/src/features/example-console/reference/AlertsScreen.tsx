import { useState } from "react";
import FIX_ALERT_RULES from "../data/alert-rules.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { AlertsMFiring } from "./alerts-screen/AlertsMFiring";

export const AlertsScreen = () => {
  const { t } = useI18n();
  const [tab, setTab] = useState("inbox");
  const [drawer, setDrawer] = useState<{ mode?: string } | null>(null);
  const [rules, setRules] = useState(FIX_ALERT_RULES);

  return <AlertsMFiring {...{ t, tab, setTab, setDrawer, rules, setRules, drawer }} />;
};
