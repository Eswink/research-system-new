import type * as E from "../../exampleTypes";
import { INPUT_MONO } from "../inputMono";

interface TeamSectionselectProps {
  ov:
    | { role: string; instances: number; collapse_when: string }
    | { role: string; instances: null; collapse_when: string };
  setP: E.UpdateProtocol;
  i: number;
  roleOptions: string[];
}

export function TeamSectionselect({ ov, setP, i, roleOptions }: TeamSectionselectProps) {
  return (
    <select
      value={ov.role}
      onChange={(e) => {
        setP((p) => {
          const row = p.team.overrides[i];
          if (row) row.role = e.target.value;
        });
      }}
      style={INPUT_MONO}
    >
      {roleOptions.map((r) => (
        <option key={r}>{r}</option>
      ))}
    </select>
  );
}
