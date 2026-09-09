import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../TeamScreen.module.css";

interface TeamSection7Props {
  model: FixtureTypes.Model | undefined;
  a: FixtureTypes.Agent;
  t: (key: string, fallback?: string) => string;
}

export function TeamSection7({ model, a, t }: TeamSection7Props) {
  return (
    <div className={visual.surface10}>
      <div className={visual.row12}>
        <Icon name="hex" size={10} className={visual.surface11} />
        <span className={`mono ${visual.label7 ?? ""}`}>{model?.model_id}</span>
        <span className={`chip ${visual.caption4 ?? ""}`}>
          {a.model_binding.kind.slice(0, 4).toLowerCase()}
        </span>
      </div>
      <div className={visual.row13}>
        <span>temp {a.temperature}</span>
        {model && !model.provider_fingerprint_available && (
          <span className={visual.surface12}>{t("tm.fpUnavail")}</span>
        )}
      </div>
    </div>
  );
}
