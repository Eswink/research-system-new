import FIX_ROLES from "../../data/roles.json";
import { Icon } from "../Icon";
import visual from "../TeamScreen.module.css";
import { TeamSection8 } from "./TeamSection8";

interface TeamSection6Props {
  t: (key: string, fallback?: string) => string;
}

export function TeamSection6({ t }: TeamSection6Props) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <div className={visual.row2}>
        <Icon name="menu" size={12} className={visual.surface2} />
        <span className={visual.label3}>{t("tm.roles")}</span>
        <span className="chip">
          {FIX_ROLES.filter((r) => r.active > 0).length}/{FIX_ROLES.length}
        </span>
      </div>
      <TeamSection8 {...{ t }} />
    </div>
  );
}
