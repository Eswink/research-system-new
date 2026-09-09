import type * as E from "../../exampleTypes";
import visual from "../BudgetSection.module.css";
import { Field } from "../Field";
import { Icon } from "../Icon";

interface BudgetSectionField2Props {
  t: (key: string, fallback?: string) => string;
  wHs: E.ProtocolIssue | undefined;
  setP: E.UpdateProtocol;
  b: {
    cap_minor: number;
    hard_stop_on_breach: boolean;
    reservations: { resource: string; minor: number }[];
  };
}

export function BudgetSectionField2({ t, wHs, setP, b }: BudgetSectionField2Props) {
  return (
    <Field
      label="budget.hard_stop_on_breach"
      tooltip={t("pe.bd.tip.hardstop")}
      hint={wHs ? wHs.message : null}
    >
      <div className={visual.row2}>
        {[true, false].map((v) => (
          <button
            key={String(v)}
            onClick={() => {
              setP((p) => {
                p.budget.hard_stop_on_breach = v;
              });
            }}
            className={visual.action2}
            style={{
              background:
                b.hard_stop_on_breach === v
                  ? v
                    ? "var(--success-dim)"
                    : "var(--danger-dim)"
                  : "var(--bg-sunken)",
              border: `1px solid ${
                b.hard_stop_on_breach === v
                  ? v
                    ? "var(--success-line)"
                    : "var(--danger-line)"
                  : "var(--border)"
              }`,
              color:
                b.hard_stop_on_breach === v
                  ? v
                    ? "var(--success)"
                    : "var(--danger)"
                  : "var(--fg-muted)",
            }}
          >
            <Icon name={v ? "check" : "ban"} size={10} /> {v ? "HARD_STOP" : "SOFT_WARN"}
          </button>
        ))}
      </div>
    </Field>
  );
}
