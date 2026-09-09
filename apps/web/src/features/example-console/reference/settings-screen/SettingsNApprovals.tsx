import { type Dispatch, type SetStateAction } from "react";
import { NotifRow } from "../NotifRow";
import visual from "../SettingsScreen.module.css";

interface SettingsNApprovalsProps {
  t: (key: string, fallback?: string) => string;
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
}

export function SettingsNApprovals({ t, prefs, setPrefs }: SettingsNApprovalsProps) {
  return (
    <div className={visual.column2}>
      <NotifRow
        label={t("st.n.approvals")}
        desc={t("st.n.approvalsDesc")}
        value={prefs.notifyApprovals}
        onChange={(v) => {
          setPrefs({ ...prefs, notifyApprovals: v });
        }}
      />
      <NotifRow
        label={t("st.n.alerts")}
        desc={t("st.n.alertsDesc")}
        value={prefs.notifyAlerts}
        onChange={(v) => {
          setPrefs({ ...prefs, notifyAlerts: v });
        }}
      />
      <NotifRow
        label={t("st.n.digest")}
        desc={t("st.n.digestDesc")}
        value={prefs.notifyDigest}
        onChange={(v) => {
          setPrefs({ ...prefs, notifyDigest: v });
        }}
      />
      <NotifRow
        label={t("st.n.claims")}
        desc={t("st.n.claimsDesc")}
        value={prefs.notifyClaims}
        onChange={(v) => {
          setPrefs({ ...prefs, notifyClaims: v });
        }}
      />
    </div>
  );
}
