import type * as E from "../../exampleTypes";
import { INPUT_MONO } from "../inputMono";

interface TeamSectioninputProps {
  ov:
    | { role: string; instances: number; collapse_when: string }
    | { role: string; instances: null; collapse_when: string };
  setP: E.UpdateProtocol;
  i: number;
}

export function TeamSectioninput({ ov, setP, i }: TeamSectioninputProps) {
  return (
    <input
      type="number"
      value={ov.instances ?? ""}
      onChange={(e) => {
        setP((p) => {
          const row = p.team.overrides[i];
          if (row) row.instances = e.target.value === "" ? null : Number(e.target.value);
        });
      }}
      placeholder="—"
      style={INPUT_MONO}
    />
  );
}
