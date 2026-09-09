import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../EndpointsScreen.module.css";
import { EndpointsSection } from "./EndpointsSection";
import { EndpointsSection7 } from "./EndpointsSection7";

interface EndpointsSection5Props {
  t: (key: string, fallback?: string) => string;
  selectedEndpointId: string;
  models: FixtureTypes.Model[];
  setFilter: Dispatch<SetStateAction<string>>;
  filter: string;
}

export function EndpointsSection5({
  t,
  selectedEndpointId,
  models,
  setFilter,
  filter,
}: EndpointsSection5Props) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <EndpointsSection7 {...{ t, selectedEndpointId, models, setFilter, filter }} />

      <EndpointsSection {...{ t, models }} />
    </div>
  );
}
