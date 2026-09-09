import { type Dispatch, type SetStateAction } from "react";
import { FormRow } from "../FormRow";
import { Icon } from "../Icon";
import { NotifRow } from "../NotifRow";
import { Select } from "../Select";
import visual from "../SettingsScreen.module.css";

interface SettingsSTwoFAProps {
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

export function SettingsSTwoFA({ t, prefs, setPrefs }: SettingsSTwoFAProps) {
  return (
    <div className={visual.column3}>
      <NotifRow
        label={t("st.s.twoFA")}
        desc={t("st.s.twoFADesc")}
        value={prefs.twoFA}
        onChange={(v) => {
          setPrefs({ ...prefs, twoFA: v });
        }}
      />
      <NotifRow
        label={t("st.s.ssoOnly")}
        desc={t("st.s.ssoOnlyDesc")}
        value={prefs.ssoOnly}
        onChange={(v) => {
          setPrefs({ ...prefs, ssoOnly: v });
        }}
      />
      <div className={visual.row4}>
        <Icon name="warn-tri" size={13} className={visual.surface4} />
        <div>
          <div className={visual.label4}>{t("st.s.sessionsTitle")}</div>
          <div className={visual.label5}>3 {t("st.s.sessions")} · Tokyo · Kyoto · Yokohama</div>
          <button className={`btn sm ${visual.action2 ?? ""}`}>{t("st.s.revokeAll")}</button>
        </div>
      </div>
      <FormRow label={t("st.s.defaultAutonomy")} hint={t("st.s.autonomyHint")}>
        <Select
          value={prefs.autonomyDefault}
          onChange={(v) => {
            setPrefs({ ...prefs, autonomyDefault: v });
          }}
          options={[
            { value: "MANUAL", label: "MANUAL" },
            { value: "SUPERVISED", label: "SUPERVISED" },
            { value: "GUARDED_AUTONOMOUS", label: "GUARDED_AUTONOMOUS" },
            { value: "AUTONOMOUS", label: "AUTONOMOUS" },
          ]}
        />
      </FormRow>
    </div>
  );
}
