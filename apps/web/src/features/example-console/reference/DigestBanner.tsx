import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./DigestBanner.module.css";
import { Icon } from "./Icon";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const DigestBanner = () => {
  const { t } = useI18n();
  return (
    <div className={visual.row}>
      <Icon name="warn-tri" size={11} className={visual.surface} />
      <span className={visual.surface2}>
        <strong className={visual.surface3}>{t("pe.digest.warn")}</strong>{" "}
        <span className={visual.surface4}>{t("pe.digest.detail")}</span>{" "}
        <span className={`mono ${visual.caption ?? ""}`}>
          37b2c9… → <span className={visual.surface5}>dirty</span>
        </span>
      </span>
    </div>
  );
};
