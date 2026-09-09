import type * as E from "../../exampleTypes";
import { BudgetDonut } from "../BudgetDonut";
import visual from "../BudgetSection.module.css";
import { BudgetSectionSection2 } from "./BudgetSectionSection2";

interface BudgetSectionSectionProps {
  eRes: E.ProtocolIssue | undefined;
  b: {
    cap_minor: number;
    hard_stop_on_breach: boolean;
    reservations: { resource: string; minor: number }[];
  };
  palette: string[];
  setP: E.UpdateProtocol;
  t: (key: string, fallback?: string) => string;
  pct: number;
}

export function BudgetSectionSection({
  eRes,
  b,
  palette,
  setP,
  t,
  pct,
}: BudgetSectionSectionProps) {
  return (
    <div className={visual.grid}>
      {/* Table */}
      <BudgetSectionSection2 {...{ eRes, b, palette, setP, t }} />

      {/* Donut / pie */}
      <div className={visual.column}>
        <BudgetDonut reservations={b.reservations} cap={b.cap_minor} palette={palette} />
        <div className={visual.caption4}>
          <div className={visual.label3} style={{ color: eRes ? "var(--danger)" : "var(--fg)" }}>
            {pct.toFixed(0)}%
          </div>
          <div>{t("pe.bd.ofCap")}</div>
        </div>
      </div>
    </div>
  );
}
