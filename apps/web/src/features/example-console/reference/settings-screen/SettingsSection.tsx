import { Icon } from "../Icon";
import visual from "../SettingsScreen.module.css";

interface SettingsSectionProps {
  t: (key: string, fallback?: string) => string;
  apiKeys: (
    | {
        id: string;
        label: string;
        scope: string;
        created: string;
        last_used: string;
        masked: string;
      }
    | { id: string; label: string; scope: string; created: string; last_used: null; masked: string }
  )[];
}

export function SettingsSection({ t, apiKeys }: SettingsSectionProps) {
  return (
    <div className={`panel ${visual.panel3 ?? ""}`}>
      <div className={`row head ${visual.surface2 ?? ""}`}>
        <span>{t("st.k.label")}</span>
        <span>{t("st.k.scope")}</span>
        <span>{t("st.k.masked")}</span>
        <span>{t("st.k.created")}</span>
        <span>{t("st.k.lastUsed")}</span>
        <span></span>
      </div>
      {apiKeys.map((k) => (
        <div key={k.id} className={`row ${visual.surface3 ?? ""}`}>
          <span className={visual.label2}>{k.label}</span>
          <span className={`mono ${visual.caption2 ?? ""}`}>{k.scope}</span>
          <span className={`mono ${visual.label3 ?? ""}`}>{k.masked}</span>
          <span className={`mono ${visual.caption3 ?? ""}`}>{k.created}</span>
          <span
            className={`mono ${visual.caption4 ?? ""}`}
            style={{ color: k.last_used ? "var(--fg-faint)" : "var(--fg-faint)" }}
          >
            {k.last_used ? (
              new Date(k.last_used).toISOString().slice(5, 16).replace("T", " ")
            ) : (
              <span className="empty-mark">{t("st.k.never")}</span>
            )}
          </span>
          <button className={`btn sm ghost ${visual.action ?? ""}`}>
            <Icon name="x" size={10} />
          </button>
        </div>
      ))}
    </div>
  );
}
