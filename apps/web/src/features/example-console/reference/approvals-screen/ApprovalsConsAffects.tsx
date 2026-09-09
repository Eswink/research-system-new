import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ApprovalsScreen.module.css";
import { ConsRow } from "../ConsRow";

interface ApprovalsConsAffectsProps {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.Approval;
}

export function ApprovalsConsAffects({ t, selected }: ApprovalsConsAffectsProps) {
  return (
    <div>
      <div className={visual.caption3}>{t("ap.willHappen")}</div>
      <ul className={visual.column3}>
        <ConsRow
          icon="graph"
          tone="warn"
          label={t("ap.cons.affects")
            .replace("{n}", String(selected.consequence.affected_tasks))
            .replace("{s}", selected.consequence.affected_tasks !== 1 ? "s" : "")}
        />
        <ConsRow
          icon={selected.consequence.produces_manifest_revision ? "fork" : "check"}
          tone={selected.consequence.produces_manifest_revision ? "danger" : "success"}
          label={
            selected.consequence.produces_manifest_revision ? t("ap.cons.mrYes") : t("ap.cons.mrNo")
          }
        />
        <ConsRow
          icon="external"
          tone={selected.consequence.external_side_effects ? "danger" : "success"}
          label={
            selected.consequence.external_side_effects ? t("ap.cons.extYes") : t("ap.cons.extNo")
          }
        />
        <ConsRow
          icon={selected.consequence.produces_fork ? "fork" : "check"}
          tone={selected.consequence.produces_fork ? "warn" : "success"}
          label={selected.consequence.produces_fork ? t("ap.cons.forkYes") : t("ap.cons.forkNo")}
        />
      </ul>
    </div>
  );
}
