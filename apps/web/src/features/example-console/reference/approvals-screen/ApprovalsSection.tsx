import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ApprovalsScreen.module.css";
import { Icon } from "../Icon";
import { ApprovalsConsAffects } from "./ApprovalsConsAffects";
import { ApprovalsSection2 } from "./ApprovalsSection2";
import { ApprovalsSection3 } from "./ApprovalsSection3";

interface ApprovalsSectionProps {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.Approval | undefined;
}

export function ApprovalsSection({ t, selected }: ApprovalsSectionProps) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <div className={visual.surface4}>
        <div className={visual.caption}>{t("ap.consequence")}</div>
        <div className={visual.label3}>{selected?.action.verb.replace(/_/g, " ")}</div>
      </div>
      {selected && <ApprovalSelection {...{ selected, t }} />}
    </div>
  );
}

function ApprovalSelection({
  selected,
  t,
}: {
  selected: FixtureTypes.Approval;
  t: ApprovalsSectionProps["t"];
}) {
  return (
    <div className={visual.column2}>
      <ApprovalsSection2 {...{ selected, t }} />
      <div className={visual.label4}>
        <div className={visual.caption2}>{t("ap.action")}</div>
        {JSON.stringify(selected.action, null, 2)
          .split("\n")
          .map((line) => (
            <div key={line} className={visual.label5}>
              {line}
            </div>
          ))}
      </div>
      <ApprovalsConsAffects {...{ t, selected }} />
      <ApprovalsSection3 {...{ t, selected }} />
      <div className={visual.row4}>
        <button className={`btn primary ${visual.action ?? ""}`}>
          <Icon name="check" size={11} /> {t("act.approve")}
          {selected.risk === "high" && <span className={visual.caption5}>{t("ap.confirm")}</span>}
        </button>
        <button className={`btn danger ${visual.action2 ?? ""}`}>
          <Icon name="x" size={11} /> {t("act.deny")}
        </button>
      </div>
      <div className={visual.caption6}>
        Idempotency-Key:{" "}
        <span className={visual.surface8}>
          ik_{selected.id.slice(4)}_{Date.now().toString(36).slice(-6)}
        </span>
      </div>
    </div>
  );
}
