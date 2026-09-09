import { LiveIndicator } from "../LiveIndicator";
import { StateDemo } from "../StateDemo";
import visual from "../StatesScreen.module.css";

export function StatesStateDemo4() {
  return (
    <StateDemo>
      <div className={visual.surface14}>
        <div className={visual.surface15}>
          <LiveIndicator state="live" />
        </div>
        <div className={visual.label9}>
          <div>
            <span className={visual.surface16}>14:42:11</span> evidence.proposed · ev_006
          </div>
          <div className={visual.surface17}>
            <span className={visual.surface18}>14:42:14</span> tool.called · pubmed.search
          </div>
        </div>
      </div>
    </StateDemo>
  );
}
