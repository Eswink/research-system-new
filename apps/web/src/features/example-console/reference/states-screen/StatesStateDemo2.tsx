import { Icon } from "../Icon";
import { StateDemo } from "../StateDemo";
import visual from "../StatesScreen.module.css";

interface StatesStateDemo2Props {
  t: (key: string, fallback?: string) => string;
}

export function StatesStateDemo2({ t }: StatesStateDemo2Props) {
  return (
    <StateDemo>
      <div className={visual.surface3}>
        <div className={visual.row2}>
          <Icon name="x" size={12} /> {t("sm.demo.errTitle")}
        </div>
        <div className={visual.label3}>
          error_class: <span className={visual.surface4}>UPSTREAM_TIMEOUT</span>
          <br />
          error_message_redacted: "endpoint responded 504 after 60s (retryable=true)"
        </div>
        <button className="btn sm">
          <Icon name="spin" size={10} /> {t("act.retry")}
        </button>
      </div>
    </StateDemo>
  );
}
