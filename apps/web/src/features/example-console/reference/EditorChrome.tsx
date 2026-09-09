import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./EditorChrome.module.css";
import { Icon } from "./Icon";
import { SegmentedToggle } from "./SegmentedToggle";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const EditorChrome = ({
  mode,
  setMode,
  dirty,
  onTemplates,
}: {
  mode: string;
  setMode: (mode: string) => void;
  dirty: boolean;
  onTemplates: () => void;
}) => {
  const { t } = useI18n();
  return (
    <div className={visual.row}>
      <Icon name="book" size={12} className={visual.surface} />
      <span className={visual.label}>protocol.yaml</span>
      {dirty && <span className={visual.caption}>DIRTY</span>}

      {/* Segmented toggle */}
      <div className={visual.row2}>
        <SegmentedToggle
          value={mode}
          onChange={setMode}
          options={[
            { value: "form", icon: "edit", label: t("pe.mode.form") },
            { value: "yaml", icon: "code", label: t("pe.mode.yaml") },
          ]}
        />
        <div className={`vr ${visual.surface2 ?? ""}`} />
        <button
          className={`btn sm ghost ${visual.action ?? ""}`}
          onClick={onTemplates}
          title={t("pe.templates.tip")}
        >
          <Icon name="copy" size={10} /> {t("pe.templates")}
          <Icon name="chevron-d" size={9} />
        </button>
        <button className={`btn sm ghost ${visual.action2 ?? ""}`} title={t("pe.diff.tip")}>
          <Icon name="fork" size={10} />
        </button>
        <button className={`btn sm ghost ${visual.action3 ?? ""}`} title={t("pe.validate.tip")}>
          <Icon name="check" size={10} />
        </button>
      </div>
    </div>
  );
};
