import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import { SettingsPage } from "../SettingsPage";
import visual from "../SettingsScreen.module.css";
import { SettingsBDue } from "./SettingsBDue";
import { SettingsBPlan } from "./SettingsBPlan";
import { SettingsNApprovals } from "./SettingsNApprovals";
import { SettingsPfLanguage } from "./SettingsPfLanguage";
import { SettingsPName } from "./SettingsPName";
import { SettingsSection } from "./SettingsSection";
import { SettingsSTwoFA } from "./SettingsSTwoFA";
import { SettingsWsCurrent } from "./SettingsWsCurrent";

interface SettingsProfileProps {
  section: string;
  t: (key: string, fallback?: string) => string;
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

export function SettingsProfile({
  section,
  t,
  lang,
  prefs,
  setPrefs,
  apiKeys,
  setLang,
}: SettingsProfileProps) {
  return (
    <main className={`panel ${visual.panel2 ?? ""}`}>
      <SettingsPrimarySections {...{ section, t, lang, prefs, setPrefs, apiKeys }} />
      <SettingsSecondarySections {...{ section, t, lang, setLang }} />
    </main>
  );
}

function SettingsPrimarySections(props: Omit<SettingsProfileProps, "setLang">) {
  const { section, t, lang, prefs, setPrefs, apiKeys } = props;
  return (
    <>
      {section === "profile" && (
        <SettingsPage title={t("st.profile")} subtitle={t("st.profileSub")}>
          <SettingsPName {...{ t, lang }} />
        </SettingsPage>
      )}

      {section === "notifications" && (
        <SettingsPage title={t("st.notifications")} subtitle={t("st.notificationsSub")}>
          <SettingsNApprovals {...{ t, prefs, setPrefs }} />
          <div className={visual.label}>
            <Icon name="q" size={11} className={visual.surface} />
            {t("st.n.channel")}:{" "}
            <span className="mono">slack:@leo.tanaka · email:leo.tanaka@research.io</span>
          </div>
        </SettingsPage>
      )}

      {section === "apikeys" && (
        <SettingsPage
          title={t("st.apikeys")}
          subtitle={t("st.apikeysSub")}
          action={
            <button className="btn primary sm">
              <Icon name="plus" size={11} /> {t("st.k.new")}
            </button>
          }
        >
          <SettingsSection {...{ t, apiKeys }} />
        </SettingsPage>
      )}

      {section === "security" && (
        <SettingsPage title={t("st.security")} subtitle={t("st.securitySub")}>
          <SettingsSTwoFA {...{ t, prefs, setPrefs }} />
        </SettingsPage>
      )}
    </>
  );
}

function SettingsSecondarySections(
  props: Pick<SettingsProfileProps, "section" | "t" | "lang" | "setLang">,
) {
  const { section, t, lang, setLang } = props;
  return (
    <>
      {section === "workspace" && (
        <SettingsPage title={t("st.workspace")} subtitle={t("st.workspaceSub")}>
          <SettingsWsCurrent {...{ t }} />
        </SettingsPage>
      )}

      {section === "preferences" && (
        <SettingsPage title={t("st.preferences")} subtitle={t("st.preferencesSub")}>
          <SettingsPfLanguage {...{ t, lang, setLang }} />
        </SettingsPage>
      )}

      {section === "billing" && (
        <SettingsPage title={t("st.billing")} subtitle={t("st.billingSub")}>
          <SettingsBPlan {...{ t }} />
          <SettingsBDue {...{ t }} />
        </SettingsPage>
      )}
    </>
  );
}
