import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../EndpointsScreen.module.css";

interface EndpointsSection6Props {
  ep: FixtureTypes.Endpoint;
  t: (key: string, fallback?: string) => string;
  healthColor: string;
}

export function EndpointsSection6({ ep, t, healthColor }: EndpointsSection6Props) {
  return (
    <div className={visual.row3}>
      <span>
        {ep.models_count} {t("ep.models")}
      </span>
      <span>·</span>
      <span style={{ color: healthColor }}>
        {ep.latency_ms != null ? (
          `${String(ep.latency_ms)}ms`
        ) : (
          <span className={visual.surface5}>{t("ep.latencyUnknown")}</span>
        )}
      </span>
      <span className={visual.surface6}>
        {ep.credential === "configured" ? t("ep.credConfig") : t("ep.credMissing")}
      </span>
    </div>
  );
}
