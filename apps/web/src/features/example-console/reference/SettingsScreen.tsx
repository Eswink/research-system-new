import { useState } from "react";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { SettingsSection2 } from "./settings-screen/SettingsSection2";

export const SettingsScreen = () => {
  const { t, lang, setLang } = useI18n();
  const [section, setSection] = useState("profile");
  const [prefs, setPrefs] = useState({
    notifyApprovals: true,
    notifyAlerts: true,
    notifyDigest: true,
    notifyClaims: false,
    twoFA: true,
    ssoOnly: false,
    autonomyDefault: "SUPERVISED",
  });

  const sections = settingsSections(t);

  return (
    <SettingsSection2
      {...{ t, sections, setSection, section, lang, prefs, setPrefs, apiKeys: API_KEYS, setLang }}
    />
  );
};

function settingsSections(t: (key: string, fallback?: string) => string) {
  return [
    { id: "profile", icon: "circle", label: t("st.profile") },
    { id: "notifications", icon: "menu", label: t("st.notifications") },
    { id: "apikeys", icon: "lock", label: t("st.apikeys") },
    { id: "security", icon: "shield", label: t("st.security") },
    { id: "workspace", icon: "hex", label: t("st.workspace") },
    { id: "preferences", icon: "diamond", label: t("st.preferences") },
    { id: "billing", icon: "graph", label: t("st.billing") },
  ];
}

const API_KEYS = [
  {
    id: "key_1",
    label: "prod-writer",
    scope: "runs:write · claims:read",
    created: "2026-08-01",
    last_used: "2026-08-27T14:20:00Z",
    masked: "sk-••••••••abc7f2",
  },
  {
    id: "key_2",
    label: "readonly-dashboard",
    scope: "*:read",
    created: "2026-07-14",
    last_used: "2026-08-27T13:55:00Z",
    masked: "sk-••••••••b3d891",
  },
  {
    id: "key_3",
    label: "ci-pipeline",
    scope: "runs:write · endpoints:invoke",
    created: "2026-06-02",
    last_used: null,
    masked: "sk-••••••••7fa2c1",
  },
];
