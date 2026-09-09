import type * as E from "../../exampleTypes";
import { INPUT_MONO } from "../inputMono";
import { RESOURCE_TYPES } from "../resourceTypes";

interface BudgetSectionselectProps {
  r: { resource: string; minor: number };
  setP: E.UpdateProtocol;
  i: number;
}

export function BudgetSectionselect({ r, setP, i }: BudgetSectionselectProps) {
  return (
    <select
      value={r.resource}
      onChange={(e) => {
        setP((p) => {
          const row = p.budget.reservations[i];
          if (row) row.resource = e.target.value;
        });
      }}
      style={{
        ...INPUT_MONO,
        fontSize: 11,
        padding: "0 6px",
        minWidth: 0,
        width: "100%",
      }}
    >
      {RESOURCE_TYPES.map((rt) => (
        <option key={rt.id} value={rt.id}>
          {rt.id}
        </option>
      ))}
    </select>
  );
}
