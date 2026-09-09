import type * as E from "../../exampleTypes";
import { INPUT_MONO } from "../inputMono";

interface BudgetSectioninputProps {
  r: { resource: string; minor: number };
  setP: E.UpdateProtocol;
  i: number;
}

export function BudgetSectioninput({ r, setP, i }: BudgetSectioninputProps) {
  return (
    <input
      type="number"
      step="10000"
      value={r.minor}
      onChange={(e) => {
        setP((p) => {
          const row = p.budget.reservations[i];
          if (row) row.minor = Number(e.target.value);
        });
      }}
      style={{ ...INPUT_MONO, textAlign: "right", fontSize: 11, padding: "0 6px" }}
    />
  );
}
