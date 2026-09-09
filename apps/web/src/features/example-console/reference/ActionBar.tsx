import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ActionBar.module.css";
import { Icon } from "./Icon";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const ActionBar = ({
  dirty,
  canApply,
  errorCount,
  warnCount,
  onDiscard,
  onApply,
}: {
  dirty: boolean;
  canApply: boolean;
  errorCount: number;
  warnCount: number;
  onDiscard: () => void;
  onApply: () => void;
}) => {
  const { t } = useI18n();
  return (
    <ActionBarSection {...{ dirty, t, errorCount, warnCount, onDiscard, onApply, canApply }} />
  );
};

interface ActionBarSectionProps {
  dirty: boolean;
  t: (key: string, fallback?: string) => string;
  errorCount: number;
  warnCount: number;
  onDiscard: () => void;
  onApply: () => void;
  canApply: boolean;
}

function ActionBarSection({
  dirty,
  t,
  errorCount,
  warnCount,
  onDiscard,
  onApply,
  canApply,
}: ActionBarSectionProps) {
  return (
    <div className={visual.row}>
      <ActionBarSection2 {...{ dirty, t, errorCount, warnCount }} />
      <div className={visual.row7}>
        <button className="btn sm" onClick={onDiscard} disabled={!dirty}>
          {t("pe.bar.discard")}
        </button>
        <button
          className="btn sm primary"
          onClick={onApply}
          disabled={!canApply}
          aria-disabled={!canApply}
          title={
            canApply
              ? ""
              : errorCount > 0
                ? t("pe.bar.applyBlockedErr")
                : t("pe.bar.applyBlockedNoChange")
          }
        >
          <Icon name="check" size={10} /> {t("pe.bar.apply")}
        </button>
      </div>
    </div>
  );
}

interface ActionBarSection2Props {
  dirty: boolean;
  t: (key: string, fallback?: string) => string;
  errorCount: number;
  warnCount: number;
}

function ActionBarSection2({ dirty, t, errorCount, warnCount }: ActionBarSection2Props) {
  return (
    <div className={visual.row2}>
      {!dirty ? (
        <span className={visual.row3}>
          <Icon name="check" size={10} /> {t("pe.bar.saved")}
        </span>
      ) : errorCount > 0 ? (
        <span className={visual.row4}>
          <Icon name="x" size={10} /> {errorCount} {t("pe.bar.errors")}
        </span>
      ) : warnCount > 0 ? (
        <span className={visual.row5}>
          <Icon name="warn-tri" size={10} /> {warnCount} {t("pe.bar.warnings")} ·{" "}
          {t("pe.bar.applyOk")}
        </span>
      ) : (
        <span className={visual.row6}>
          <Icon name="dot" size={10} /> {t("pe.bar.dirty")}
        </span>
      )}
    </div>
  );
}
