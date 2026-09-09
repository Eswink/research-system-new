import { useState } from "react";
import FIX_INTEGRATIONS from "../data/integrations.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { IntegrationsTitle } from "./integrations-screen/IntegrationsTitle";

export const IntegrationsScreen = () => {
  const { t } = useI18n();
  const [tab, setTab] = useState("all");
  const filtered =
    tab === "all" ? FIX_INTEGRATIONS : FIX_INTEGRATIONS.filter((i) => i.status === tab);

  return <IntegrationsTitle {...{ t, tab, setTab, filtered }} />;
};
