import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import visual from "../SettingsScreen.module.css";
import { SettingsProfile } from "./SettingsProfile";

interface SettingsSection2Props {
  t: (key: string, fallback?: string) => string;
  sections: { id: string; icon: string; label: string }[];
  setSection: Dispatch<SetStateAction<string>>;
  section: string;
  lang: string;
  prefs: {
    notifyApprovals: boolean;
    notifyAlerts: boolean;
    notifyDigest: boolean;
    notifyClaims: boolean;
    twoFA: boolean;
    ssoOnly: boolean;
    autonomyDefault: string;
  };
  setPrefs: Dispatch<
    SetStateAction<{
      notifyApprovals: boolean;
      notifyAlerts: boolean;
      notifyDigest: boolean;
      notifyClaims: boolean;
      twoFA: boolean;
      ssoOnly: boolean;
      autonomyDefault: string;
    }>
  >;
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
  setLang: (next: string) => void;
}

export function SettingsSection2({
  t,
  sections,
  setSection,
  section,
  lang,
  prefs,
  setPrefs,
  apiKeys,
  setLang,
}: SettingsSection2Props) {
  return (
    <div className={visual.grid}>
      {/* Section rail */}
      <aside className={`panel ${visual.panel ?? ""}`}>
        <div className={visual.caption}>{t("st.title")}</div>
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => {
              setSection(s.id);
            }}
            className={visual.row}
            style={{
              background: section === s.id ? "var(--accent-dim)" : "transparent",
              color: section === s.id ? "var(--accent)" : "var(--fg-muted)",
            }}
          >
            <Icon name={s.icon} size={12} /> {s.label}
          </button>
        ))}
      </aside>

      {/* Content */}
      <SettingsProfile {...{ section, t, lang, prefs, setPrefs, apiKeys, setLang }} />
    </div>
  );
}
