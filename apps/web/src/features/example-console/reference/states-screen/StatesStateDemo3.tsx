import { Icon } from "../Icon";
import { StateDemo } from "../StateDemo";
import visual from "../StatesScreen.module.css";

interface StatesStateDemo3Props {
  t: (key: string, fallback?: string) => string;
}

export function StatesStateDemo3({ t }: StatesStateDemo3Props) {
  return (
    <StateDemo>
      <div className={visual.surface12}>
        <div className={visual.row3}>
          <Icon name="clock" size={11} /> {t("sm.demo.staleTitle")}
        </div>
        <div className={visual.label8}>
          last_updated: 2026-08-27T13:44:11Z
          <br />
          <span className={visual.surface13}>~ 20 min {t("sm.demo.staleAgo")}</span>
        </div>
        <button className="btn sm">
          <Icon name="spin" size={10} /> {t("act.refresh")}
        </button>
      </div>
    </StateDemo>
  );
}
