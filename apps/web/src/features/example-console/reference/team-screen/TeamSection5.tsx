import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../TeamScreen.module.css";

interface TeamSection5Props {
  a: FixtureTypes.Agent;
  role: FixtureTypes.Role | undefined;
  isConflict: boolean;
}

export function TeamSection5({ a, role, isConflict }: TeamSection5Props) {
  return (
    <div className={visual.row9}>
      <div
        className={visual.row10}
        style={{
          background: `hsl(${String((a.id.charCodeAt(3) * 37) % 360)}, 40%, 40%)`,
        }}
      >
        {a.name.slice(0, 2).toUpperCase()}
      </div>
      <div className={visual.surface9}>
        <div className={visual.label6}>{a.name}</div>
        <div className={visual.caption3}>{role?.name}</div>
      </div>
      {isConflict && (
        <span title="Heterogeneity conflict" className={visual.row11}>
          <Icon name="warn-tri" size={10} />
        </span>
      )}
    </div>
  );
}
