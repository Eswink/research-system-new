import { useState } from "react";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { BudgetSectionField } from "./budget-section/BudgetSectionField";
import { BudgetSectionField2 } from "./budget-section/BudgetSectionField2";
import { BudgetSectionSection } from "./budget-section/BudgetSectionSection";
import visual from "./BudgetSection.module.css";
import { findErr } from "./findErr";
import { SectionHeader } from "./SectionHeader";
import { TooltipIcon } from "./TooltipIcon";

export const BudgetSection = ({ value, setP, errors, warnings = [] }: E.ProtocolSectionProps) => {
  const { t } = useI18n();
  const b = value.budget;
  const eRes = findErr(errors, "budget.reservations");
  const wRes = findErr(warnings, "budget.reservations");
  const wHs = findErr(warnings, "budget.hard_stop_on_breach");
  const [capConfirm, setCapConfirm] = useState(false);
  const [capDraft, setCapDraft] = useState(b.cap_minor);

  const sum = b.reservations.reduce((s, r) => s + (r.minor || 0), 0);
  const pct = Math.min(100, (sum / b.cap_minor) * 100);
  const palette = ["var(--accent)", "#8B7BD8", "#D9962A", "#35A56F", "#E0524C", "#4CB8C4"];

  return (
    <div>
      <SectionHeader title={t("pe.sec.budget")} subtitle={t("pe.sec.budgetDesc")} />

      {/* cap_minor */}
      <BudgetSectionField {...{ t, b, capDraft, setCapDraft, capConfirm, setCapConfirm, setP }} />

      {/* hard_stop_on_breach */}
      <BudgetSectionField2 {...{ t, wHs, setP, b }} />

      {/* Reservations table */}
      <div className={visual.surface2}>
        <BudgetReservationHeader {...{ t, eRes, wRes, sum, capMinor: b.cap_minor }} />

        <BudgetSectionSection {...{ eRes, b, palette, setP, t, pct }} />
      </div>
    </div>
  );
};

interface BudgetReservationHeaderProps {
  t: (key: string, fallback?: string) => string;
  eRes: ReturnType<typeof findErr>;
  wRes: ReturnType<typeof findErr>;
  sum: number;
  capMinor: number;
}

function BudgetReservationHeader(props: BudgetReservationHeaderProps) {
  const exact = props.sum === props.capMinor;
  const color = props.eRes ? "var(--danger)" : exact ? "var(--success)" : "var(--fg-muted)";
  const borderColor = props.eRes
    ? "var(--danger-line)"
    : exact
      ? "var(--success-line)"
      : "var(--border)";
  return (
    <div className={visual.row3}>
      <label className={visual.label2}>budget.reservations</label>
      <TooltipIcon text={props.t("pe.bd.tip.reservations")} />
      <span className="chip" style={{ color, borderColor }}>
        Σ ${(props.sum / 100000).toFixed(2)} / ${(props.capMinor / 100000).toFixed(2)}
      </span>
      {props.eRes && <span className={visual.caption}>· overflow</span>}
      {!props.eRes && props.wRes && <span className={visual.caption2}>· underplanned</span>}
    </div>
  );
}
