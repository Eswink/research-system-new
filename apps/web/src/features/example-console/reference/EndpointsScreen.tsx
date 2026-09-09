import { useState } from "react";
import FIX_MODELS from "../data/models.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./EndpointsScreen.module.css";
import { EndpointsSection2 } from "./endpoints-screen/EndpointsSection2";
import { EndpointsSection5 } from "./endpoints-screen/EndpointsSection5";

export const EndpointsScreen = () => {
  const { t } = useI18n();
  const [selectedEndpointId, setSelectedEndpointId] = useState("ep_anthropic_direct");
  const [filter, setFilter] = useState("all");

  let models = FIX_MODELS.filter((m) => m.endpoint_id === selectedEndpointId);
  if (filter === "enabled") models = models.filter((m) => m.enabled);
  if (filter === "fp-unavailable") models = models.filter((m) => !m.provider_fingerprint_available);
  if (filter === "drift") models = models.filter((m) => m.drift_alert);

  return (
    <div className={visual.grid}>
      {/* Endpoint list */}
      <EndpointsSection2 {...{ t, selectedEndpointId, setSelectedEndpointId }} />

      {/* Models table */}
      <EndpointsSection5 {...{ t, selectedEndpointId, models, setFilter, filter }} />
    </div>
  );
};
