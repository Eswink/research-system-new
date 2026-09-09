import { type Dispatch, type SetStateAction } from "react";
import FIX_ENDPOINTS from "../../data/endpoints.json";
import visual from "../EndpointsScreen.module.css";
import { Icon } from "../Icon";
import { EndpointsSection4 } from "./EndpointsSection4";

interface EndpointsSection2Props {
  t: (key: string, fallback?: string) => string;
  selectedEndpointId: string;
  setSelectedEndpointId: Dispatch<SetStateAction<string>>;
}

export function EndpointsSection2({
  t,
  selectedEndpointId,
  setSelectedEndpointId,
}: EndpointsSection2Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="wifi" size={12} className={visual.surface} />
        <span className={visual.label}>{t("ep.endpoints")}</span>
        <span className="chip">{FIX_ENDPOINTS.length}</span>
        <button className={`btn sm ${visual.action ?? ""}`}>
          <Icon name="plus" size={10} /> {t("ep.add")}
        </button>
      </div>
      <EndpointsSection4 {...{ selectedEndpointId, setSelectedEndpointId, t }} />
    </div>
  );
}
