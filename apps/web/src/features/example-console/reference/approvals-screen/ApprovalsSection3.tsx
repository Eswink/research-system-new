import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ApprovalsScreen.module.css";

interface ApprovalsSection3Props {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.Approval;
}

export function ApprovalsSection3({ t, selected }: ApprovalsSection3Props) {
  return (
    <div>
      <div className={visual.caption4}>{t("ap.context")}</div>
      <div className={visual.label6}>
        {Object.entries(selected.context).map(([k, v]) => (
          <div key={k}>
            <span className={visual.surface6}>{k}</span> ·{" "}
            <span className={visual.surface7}>
              {typeof v === "number"
                ? k.includes("minor")
                  ? `$${(v / 100000).toFixed(2)}`
                  : v
                : String(v)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
