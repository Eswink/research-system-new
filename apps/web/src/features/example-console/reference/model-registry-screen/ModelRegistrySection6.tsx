import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ModelRegistryScreen.module.css";
import { UnknownValue } from "../UnknownValue";

interface ModelRegistrySection6Props {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.RegisteredModel;
}

export function ModelRegistrySection6({ t, selected }: ModelRegistrySection6Props) {
  return (
    <div>
      <div className={visual.caption7}>{t("mr.section.specs")}</div>
      <div className={visual.grid2}>
        <span className={visual.surface6}>{t("mr.spec.context")}</span>
        <span>
          {selected.context.toLocaleString()} {t("mr.tokens")}
        </span>
        <span className={visual.surface7}>{t("mr.spec.license")}</span>
        <span>{selected.license}</span>
        <span className={visual.surface8}>{t("mr.spec.costIn")}</span>
        <span>
          {selected.cost_1k_in != null ? `$${selected.cost_1k_in.toFixed(4)}` : <UnknownValue />}
        </span>
        <span className={visual.surface9}>{t("mr.spec.costOut")}</span>
        <span>
          {selected.cost_1k_out != null ? `$${selected.cost_1k_out.toFixed(4)}` : <UnknownValue />}
        </span>
      </div>
    </div>
  );
}
