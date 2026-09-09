import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { ApprovalCard } from "../ApprovalCard";
import visual from "../ApprovalsScreen.module.css";
import { Icon } from "../Icon";

interface ApprovalsSection4Props {
  t: (key: string, fallback?: string) => string;
  sorted: FixtureTypes.Approval[];
  selectedId: string;
  expanded: Record<string, boolean>;
  setSelectedId: Dispatch<SetStateAction<string>>;
  setExpanded: Dispatch<SetStateAction<Record<string, boolean>>>;
  setProcessed: Dispatch<SetStateAction<Record<string, string>>>;
}

export function ApprovalsSection4({
  t,
  sorted,
  selectedId,
  expanded,
  setSelectedId,
  setExpanded,
  setProcessed,
}: ApprovalsSection4Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="shield" size={12} className={visual.surface} />
        <span className={visual.label}>{t("ap.queue")}</span>
        <span className="chip">
          {sorted.length} {t("ap.pending")}
        </span>
        <div className={visual.row2}>
          <span>
            {t("ap.autonomy")}{" "}
            <span className={`mono ${visual.surface2 ?? ""}`}>GUARDED_AUTONOMOUS</span>
          </span>
        </div>
      </div>
      <div className={visual.label2}>
        <Icon name="q" size={10} className={visual.surface3} /> {t("ap.hint")}
      </div>
      <div className={visual.column}>
        {sorted.map((a) => (
          <ApprovalCard
            key={a.id}
            approval={a}
            selected={a.id === selectedId}
            expanded={!!expanded[a.id]}
            onSelect={() => {
              setSelectedId(a.id);
            }}
            onToggle={() => {
              setExpanded((prev) => ({ ...prev, [a.id]: !prev[a.id] }));
            }}
            onDecide={(decision) => {
              setProcessed((prev) => ({ ...prev, [a.id]: decision }));
            }}
          />
        ))}
      </div>
    </div>
  );
}
