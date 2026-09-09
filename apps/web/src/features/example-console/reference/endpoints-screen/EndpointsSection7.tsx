import { type Dispatch, type SetStateAction } from "react";
import FIX_ENDPOINTS from "../../data/endpoints.json";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../EndpointsScreen.module.css";
import { Icon } from "../Icon";

interface EndpointsSection7Props {
  t: (key: string, fallback?: string) => string;
  selectedEndpointId: string;
  models: FixtureTypes.Model[];
  setFilter: Dispatch<SetStateAction<string>>;
  filter: string;
}

export function EndpointsSection7({
  t,
  selectedEndpointId,
  models,
  setFilter,
  filter,
}: EndpointsSection7Props) {
  return (
    <div className={visual.row4}>
      <Icon name="hex" size={12} className={visual.surface7} />
      <span className={visual.label3}>
        {t("ep.models2")} · {FIX_ENDPOINTS.find((e) => e.id === selectedEndpointId)?.name}
      </span>
      <span className="chip">{models.length}</span>
      <div className={visual.row5}>
        {(
          [
            ["all", t("tl.filterAll")],
            ["enabled", t("ep.filterEnabled")],
            ["fp-unavailable", t("ep.filterFp")],
            ["drift", t("ep.filterDrift")],
          ] as const
        ).map(([v, l]) => (
          <button
            key={v}
            onClick={() => {
              setFilter(v);
            }}
            className="btn sm ghost"
            style={{
              background: filter === v ? "var(--bg-hover)" : "transparent",
              color: filter === v ? "var(--fg)" : "var(--fg-muted)",
            }}
          >
            {l}
          </button>
        ))}
        <div className={`vr ${visual.surface8 ?? ""}`} />
        <button className="btn sm">
          <Icon name="flask" size={10} /> {t("ep.probeAll")}
        </button>
        <button className="btn sm">
          <Icon name="search" size={10} /> {t("ep.discover")}
        </button>
      </div>
    </div>
  );
}
