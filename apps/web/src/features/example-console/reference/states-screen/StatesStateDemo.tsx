import { Icon } from "../Icon";
import { StateDemo } from "../StateDemo";
import visual from "../StatesScreen.module.css";

interface StatesStateDemoProps {
  t: (key: string, fallback?: string) => string;
}

export function StatesStateDemo({ t }: StatesStateDemoProps) {
  const partialCountClass = `mono ${visual.surface6 ?? ""}`;
  return (
    <StateDemo>
      <div className={visual.surface5}>
        <div className={visual.label4}>
          {t("sm.demo.partialShowing")} <span className={partialCountClass}>4/7</span>{" "}
          {t("sm.demo.partialLangs")}
        </div>
        <div className={visual.grid}>
          <span>
            <Icon name="check" size={9} className={visual.surface7} /> en · es · zh · ar
          </span>
          <span>
            <Icon name="q" size={9} className={visual.surface8} /> pt · fr · ja
          </span>
        </div>
        <div className={visual.label5}>{t("sm.demo.partialNote")}</div>
      </div>
    </StateDemo>
  );
}
