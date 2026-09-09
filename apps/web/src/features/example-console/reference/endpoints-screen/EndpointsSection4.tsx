import { type Dispatch, type SetStateAction } from "react";
import FIX_ENDPOINTS from "../../data/endpoints.json";
import visual from "../EndpointsScreen.module.css";
import { Icon } from "../Icon";
import { EndpointsSection6 } from "./EndpointsSection6";

interface EndpointsSection4Props {
  selectedEndpointId: string;
  setSelectedEndpointId: Dispatch<SetStateAction<string>>;
  t: (key: string, fallback?: string) => string;
}

export function EndpointsSection4({
  selectedEndpointId,
  setSelectedEndpointId,
  t,
}: EndpointsSection4Props) {
  return (
    <div className={visual.surface2}>
      {FIX_ENDPOINTS.map((ep) => {
        const selected = ep.id === selectedEndpointId;
        const healthColor =
          ep.health === "ok"
            ? "var(--success)"
            : ep.health === "fail"
              ? "var(--danger)"
              : "var(--unknown)";
        const healthIcon = ep.health === "ok" ? "circle" : ep.health === "fail" ? "x" : "circle-o";
        return (
          <div
            key={ep.id}
            onClick={() => {
              setSelectedEndpointId(ep.id);
            }}
            className={visual.surface3}
            style={{
              background: selected ? "var(--bg-hover)" : "transparent",
              borderLeft: `2px solid ${selected ? "var(--accent)" : "transparent"}`,
              opacity: ep.enabled ? 1 : 0.5,
            }}
          >
            <div className={visual.row2}>
              <Icon name={healthIcon} size={10} style={{ color: healthColor }} />
              <span className={visual.label2}>{ep.name}</span>
              {!ep.enabled && (
                <span className={`chip ${visual.surface4 ?? ""}`}>{t("ep.disabled")}</span>
              )}
            </div>
            <div className={visual.caption}>{ep.base_url}</div>
            <EndpointsSection6 {...{ ep, t, healthColor }} />
          </div>
        );
      })}
    </div>
  );
}
