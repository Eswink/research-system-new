import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../EndpointsScreen.module.css";
import { Icon } from "../Icon";
import { ReproducibilityChip } from "../ReproducibilityChip";
import { EndpointsSection3 } from "./EndpointsSection3";

interface EndpointsSectionProps {
  t: (key: string, fallback?: string) => string;
  models: FixtureTypes.Model[];
}

export function EndpointsSection({ t, models }: EndpointsSectionProps) {
  return (
    <div className={visual.surface9}>
      <div className={`row head ${visual.surface10 ?? ""}`}>
        <span></span>
        <span>{t("ep.colHead.display")}</span>
        <span>{t("ep.colHead.caps")}</span>
        <span>{t("ep.colHead.ctx")}</span>
        <span>{t("ep.colHead.reprod")}</span>
        <span>{t("ep.colHead.enabled")}</span>
        <span>{t("ep.colHead.lastProbe")}</span>
        <span></span>
      </div>
      {models.map((model) => (
        <EndpointModelRow key={model.id} model={model} t={t} />
      ))}
    </div>
  );
}

function EndpointModelRow({
  model: m,
  t,
}: {
  model: FixtureTypes.Model;
  t: EndpointsSectionProps["t"];
}) {
  const lastProbe = m.last_probe?.slice(5, 16).replace("T", " ") ?? null;
  return (
    <div className={`row ${visual.surface11 ?? ""}`}>
      <Icon
        name="hex"
        size={12}
        style={{ color: m.enabled ? "var(--accent)" : "var(--fg-faint)" }}
      />
      <div className={visual.surface12}>
        <div className={visual.label4}>{m.display_name}</div>
        <div className={visual.caption2}>{m.model_id}</div>
        {m.drift_alert && (
          <div className={visual.row6}>
            <Icon name="warn-tri" size={9} /> {t("ep.returned")} {m.returned_model_name}
          </div>
        )}
      </div>
      <EndpointsSection3 {...{ m }} />
      <span className={`mono ${visual.label5 ?? ""}`}>{(m.context_window / 1000).toFixed(0)}k</span>
      <ReproducibilityChip
        fingerprint={m.system_fingerprint}
        providerAvailable={m.provider_fingerprint_available}
        compact={true}
      />
      <span className={visual.row9}>
        {m.enabled ? (
          <Icon name="check" size={11} className={visual.surface13} />
        ) : (
          <Icon name="ban" size={11} className={visual.surface14} />
        )}
        {m.enabled ? t("ep.on") : t("ep.off")}
      </span>
      <span className={visual.caption3}>
        {lastProbe ?? <span className={visual.surface15}>{t("ep.never")}</span>}
      </span>
      <button className="btn sm ghost">
        <Icon name="chevron-r" size={10} />
      </button>
    </div>
  );
}
