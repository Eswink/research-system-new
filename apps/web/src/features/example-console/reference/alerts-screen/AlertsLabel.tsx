import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";

interface AlertsLabelProps {
  a: FixtureTypes.Alert;
}

export function AlertsLabel({ a }: AlertsLabelProps) {
  return (
    <span>
      <Icon
        name={a.state === "firing" ? "warn-tri" : a.state === "acknowledged" ? "clock" : "check"}
        size={11}
        style={{
          color:
            a.state === "firing"
              ? "var(--danger)"
              : a.state === "acknowledged"
                ? "var(--warn)"
                : "var(--success)",
        }}
      />
    </span>
  );
}
