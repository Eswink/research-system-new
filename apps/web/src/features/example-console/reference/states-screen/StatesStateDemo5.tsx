import { Icon } from "../Icon";
import { StateDemo } from "../StateDemo";
import visual from "../StatesScreen.module.css";

interface StatesStateDemo5Props {
  t: (key: string, fallback?: string) => string;
}

export function StatesStateDemo5({ t }: StatesStateDemo5Props) {
  return (
    <StateDemo>
      <div className={visual.surface}>
        <div className={visual.row}>
          <Icon name="flask" size={16} className={visual.surface2} />
        </div>
        <div className={visual.label}>{t("sm.demo.emptyTitle")}</div>
        <div className={visual.label2}>{t("sm.demo.emptyDesc")}</div>
        <button className="btn primary sm">
          <Icon name="plus" size={10} /> {t("sm.demo.emptyCta")}
        </button>
      </div>
    </StateDemo>
  );
}
