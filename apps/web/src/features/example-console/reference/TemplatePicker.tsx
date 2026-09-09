import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./TemplatePicker.module.css";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const TemplatePicker = ({
  onPick,
  onClose,
}: {
  onPick: (id: string) => void;
  onClose: () => void;
}) => {
  const { t } = useI18n();
  const items = [
    { id: "prior_study", icon: "book", label: t("pe.tmpl.prior"), desc: t("pe.tmpl.priorDesc") },
    { id: "stat_heavy", icon: "shield", label: t("pe.tmpl.stat"), desc: t("pe.tmpl.statDesc") },
    { id: "minimal", icon: "flask", label: t("pe.tmpl.minimal"), desc: t("pe.tmpl.minimalDesc") },
    { id: "reset", icon: "ban", label: t("pe.tmpl.reset"), desc: t("pe.tmpl.resetDesc") },
  ];
  return (
    <div className={visual.surface}>
      <div className={visual.row}>
        <span>{t("pe.tmpl.header")}</span>
        <button className={`btn sm ghost ${visual.action ?? ""}`} onClick={onClose}>
          <Icon name="x" size={9} />
        </button>
      </div>
      <div className={visual.grid}>
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => {
              onPick(item.id);
            }}
            className={visual.row2}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-line)")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
          >
            <Icon name={item.icon} size={12} className={visual.surface2} />
            <div className={visual.surface3}>
              <div className={visual.label}>{item.label}</div>
              <div className={visual.caption}>{item.desc}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
