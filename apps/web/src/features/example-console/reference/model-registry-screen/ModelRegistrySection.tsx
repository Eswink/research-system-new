import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ModelRegistryScreen.module.css";
import { Sparkline } from "../Sparkline";
import { ModelRegistrySection4 } from "./ModelRegistrySection4";
import { ModelRegistrySection6 } from "./ModelRegistrySection6";

interface ModelRegistrySectionProps {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.RegisteredModel;
}

export function ModelRegistrySection({ t, selected }: ModelRegistrySectionProps) {
  return (
    <div className={visual.column2}>
      {/* Specs */}
      <ModelRegistrySection6 {...{ t, selected }} />

      {/* Evals */}
      <ModelRegistrySection4 {...{ t, selected }} />

      {/* Usage */}
      <div>
        <div className={visual.caption9}>{t("mr.section.usage")}</div>
        <div className={visual.surface11}>
          <div className={visual.row5}>
            <span className={visual.label6}>
              {selected.our_usage_30d > 0 ? `${(selected.our_usage_30d / 1e6).toFixed(2)}M` : "0"}
            </span>
            <span className={visual.label7}>{t("mr.tokens")}</span>
          </div>
          <Sparkline
            data={
              selected.our_usage_30d > 0
                ? Array.from({ length: 30 }, (_, i) =>
                    Math.max(0, (selected.our_usage_30d / 30) * (0.7 + Math.sin(i * 0.6) * 0.3)),
                  )
                : [0, 0, 0, 0, 0]
            }
            width={340}
            height={40}
          />
        </div>
      </div>
    </div>
  );
}
