import type * as E from "../../exampleTypes";
import visual from "../BudgetSection.module.css";
import { Icon } from "../Icon";
import { BudgetSectioninput } from "./BudgetSectioninput";
import { BudgetSectionselect } from "./BudgetSectionselect";

interface BudgetSectionSection2Props {
  eRes: E.ProtocolIssue | undefined;
  b: {
    cap_minor: number;
    hard_stop_on_breach: boolean;
    reservations: { resource: string; minor: number }[];
  };
  palette: string[];
  setP: E.UpdateProtocol;
  t: (key: string, fallback?: string) => string;
}

export function BudgetSectionSection2({ eRes, b, palette, setP, t }: BudgetSectionSection2Props) {
  return (
    <div
      className={visual.surface3}
      style={{ border: `1px solid ${eRes ? "var(--danger-line)" : "var(--border)"}` }}
    >
      {b.reservations.map((r, i) => {
        const rowPct = (r.minor / b.cap_minor) * 100;
        return (
          <div
            key={i}
            className={visual.grid2}
            style={{
              borderBottom:
                i < b.reservations.length - 1 ? "1px solid var(--border-subtle)" : "none",
            }}
          >
            <div className={visual.surface4} style={{ background: palette[i % palette.length] }} />
            <BudgetSectionselect {...{ r, setP, i }} />
            <BudgetSectioninput {...{ r, setP, i }} />
            <span className={visual.caption3}>{rowPct.toFixed(0)}%</span>
            <button
              className={`btn sm ghost ${visual.action3 ?? ""}`}
              onClick={() => {
                setP((p) => {
                  p.budget.reservations.splice(i, 1);
                });
              }}
            >
              <Icon name="x" size={9} />
            </button>
          </div>
        );
      })}
      <button
        className={`btn sm ghost ${visual.action4 ?? ""}`}

        onClick={() => {
          setP((p) => {
            p.budget.reservations.push({ resource: "external_tools", minor: 100000 });
          });
        }}
      >
        <Icon name="plus" size={10} /> {t("pe.bd.addResv")}
      </button>
    </div>
  );
}
