import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import { Field } from "../Field";
import { BudgetSectionSection3 } from "./BudgetSectionSection3";

interface BudgetSectionFieldProps {
  t: (key: string, fallback?: string) => string;
  b: {
    cap_minor: number;
    hard_stop_on_breach: boolean;
    reservations: { resource: string; minor: number }[];
  };
  capDraft: number;
  setCapDraft: Dispatch<SetStateAction<number>>;
  capConfirm: boolean;
  setCapConfirm: Dispatch<SetStateAction<boolean>>;
  setP: E.UpdateProtocol;
}

export function BudgetSectionField({
  t,
  b,
  capDraft,
  setCapDraft,
  capConfirm,
  setCapConfirm,
  setP,
}: BudgetSectionFieldProps) {
  return (
    <Field
      label="budget.cap_minor"
      tooltip={t("pe.bd.tip.cap")}
      hint={`≈ $${(b.cap_minor / 100000).toFixed(2)} example units ${t("pe.bd.capHint")}`}
    >
      <BudgetSectionSection3
        {...{ capDraft, setCapDraft, b, capConfirm, setCapConfirm, t, setP }}
      />
    </Field>
  );
}
