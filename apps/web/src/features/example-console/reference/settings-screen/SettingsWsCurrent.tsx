import FIX_WORKSPACES from "../../data/workspaces.json";
import { Icon } from "../Icon";
import visual from "../SettingsScreen.module.css";
import { StatusBadge } from "../StatusBadge";

interface SettingsWsCurrentProps {
  t: (key: string, fallback?: string) => string;
}

export function SettingsWsCurrent({ t }: SettingsWsCurrentProps) {
  return (
    <div className={visual.column4}>
      {FIX_WORKSPACES.map((w) => (
        <div
          key={w.id}
          className={`panel ${visual.panel4 ?? ""}`}
          style={{
            borderLeft: w.current ? "3px solid var(--accent)" : "1px solid var(--border)",
          }}
        >
          <div className={visual.row5}>{w.name.slice(0, 2).toUpperCase()}</div>
          <div className={visual.surface5}>
            <div className={visual.label6}>{w.name}</div>
            <div className={visual.caption5}>
              {w.role.toUpperCase()} · {w.members} {t("st.ws.members")} · {w.plan}
            </div>
          </div>
          {w.current && (
            <StatusBadge tone="success" icon="check" label={t("st.ws.current")} filled />
          )}
          {!w.current && <button className="btn sm">{t("st.ws.switch")}</button>}
        </div>
      ))}
      <button className={`btn sm ghost ${visual.action3 ?? ""}`}>
        <Icon name="plus" size={11} /> {t("st.ws.create")}
      </button>
    </div>
  );
}
