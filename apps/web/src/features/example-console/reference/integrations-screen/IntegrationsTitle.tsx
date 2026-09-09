import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../IntegrationsScreen.module.css";
import { PageToolbar } from "../PageToolbar";
import { ViewSwitcher } from "../ViewSwitcher";
import { IntegrationsStatConnected } from "./IntegrationsStatConnected";

interface IntegrationsTitleProps {
  t: (key: string, fallback?: string) => string;
  tab: string;
  setTab: Dispatch<SetStateAction<string>>;
  filtered: FixtureTypes.Integration[];
}

export function IntegrationsTitle({ t, tab, setTab, filtered }: IntegrationsTitleProps) {
  return (
    <div className={visual.column}>
      <PageToolbar title={t("in.title")} subtitle={t("in.subtitle")}>
        <ViewSwitcher
          value={tab}
          onChange={setTab}
          views={[
            { value: "all", label: t("in.viewAll") },
            { value: "connected", label: t("in.viewConn") },
            { value: "available", label: t("in.viewAvail") },
            { value: "disconnected", label: t("in.viewDisc") },
          ]}
        />
      </PageToolbar>

      <IntegrationsStatConnected {...{ filtered, t }} />
    </div>
  );
}
