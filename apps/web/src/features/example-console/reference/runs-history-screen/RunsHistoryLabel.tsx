import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../RunsHistoryScreen.module.css";

interface RunsHistoryLabelProps {
  on: boolean;
  setSelectedIds: Dispatch<SetStateAction<string[]>>;
  r: FixtureTypes.Run;
}

export function RunsHistoryLabel({ on, setSelectedIds, r }: RunsHistoryLabelProps) {
  return (
    <span>
      <input
        type="checkbox"
        checked={on}
        onChange={() => {
          setSelectedIds((prev) =>
            on
              ? prev.filter((id) => id !== r.id)
              : prev.length >= 2
                ? [...prev.slice(-1), r.id]
                : [...prev, r.id],
          );
        }}
        className={visual.field}
      />
    </span>
  );
}
