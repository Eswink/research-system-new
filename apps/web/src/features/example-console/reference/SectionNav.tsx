import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ErrCount } from "./ErrCount";
import { Icon } from "./Icon";
import visual from "./SectionNav.module.css";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const SectionNav = ({
  active,
  onChange,
  errorsBySection,
  adminMode,
}: {
  active: string;
  onChange: (id: string) => void;
  errorsBySection: Record<string, { errors: number; warnings: number }>;
  adminMode: boolean;
}) => {
  const { t } = useI18n();
  const sections = [
    { id: "manifest", labelKey: "pe.sec.manifest", icon: "shield" },
    { id: "objectives", labelKey: "pe.sec.objectives", icon: "flask" },
    { id: "team", labelKey: "pe.sec.team", icon: "hex" },
    { id: "evaluation", labelKey: "pe.sec.evaluation", icon: "graph" },
    { id: "budget", labelKey: "pe.sec.budget", icon: "diamond" },
    { id: "gates", labelKey: "pe.sec.gates", icon: "circle-o" },
    { id: "policy", labelKey: "pe.sec.policy", icon: "lock", locked: !adminMode },
  ];
  const totalErrors = Object.values(errorsBySection).reduce((s, x) => s + x.errors, 0);
  const totalWarns = Object.values(errorsBySection).reduce((s, x) => s + x.warnings, 0);

  return (
    <SectionNavSection
      {...{ t, sections, active, errorsBySection, onChange, totalErrors, totalWarns }}
    />
  );
};

interface SectionNavSectionProps {
  t: (key: string, fallback?: string) => string;
  sections: (
    | { id: string; labelKey: string; icon: string; locked?: never }
    | { id: string; labelKey: string; icon: string; locked: boolean }
  )[];
  active: string;
  errorsBySection: Record<string, { errors: number; warnings: number }>;
  onChange: (id: string) => void;
  totalErrors: number;
  totalWarns: number;
}

function SectionNavSection({
  t,
  sections,
  active,
  errorsBySection,
  onChange,
  totalErrors,
  totalWarns,
}: SectionNavSectionProps) {
  return (
    <div className={visual.column}>
      <div className={visual.caption}>{t("pe.nav.header")}</div>
      <SectionNavSection2 {...{ sections, active, errorsBySection, onChange, t }} />
      {/* Summary */}
      <div className={visual.column2}>
        <div className={visual.row2}>
          <span>{t("pe.nav.errors")}</span>
          <span style={{ color: totalErrors > 0 ? "var(--danger)" : "var(--success)" }}>
            {totalErrors}
          </span>
        </div>
        <div className={visual.row3}>
          <span>{t("pe.nav.warnings")}</span>
          <span style={{ color: totalWarns > 0 ? "var(--warn)" : "var(--fg-faint)" }}>
            {totalWarns}
          </span>
        </div>
      </div>
    </div>
  );
}

interface SectionNavSection2Props {
  sections: (
    | { id: string; labelKey: string; icon: string; locked?: never }
    | { id: string; labelKey: string; icon: string; locked: boolean }
  )[];
  active: string;
  errorsBySection: Record<string, { errors: number; warnings: number }>;
  onChange: (id: string) => void;
  t: (key: string, fallback?: string) => string;
}

function SectionNavSection2({
  sections,
  active,
  errorsBySection,
  onChange,
  t,
}: SectionNavSection2Props) {
  return (
    <div className={visual.surface}>
      {sections.map((s) => {
        const isActive = s.id === active;
        const errs = errorsBySection[s.id]?.errors ?? 0;
        const warns = errorsBySection[s.id]?.warnings ?? 0;
        return (
          <button
            key={s.id}
            onClick={() => {
              onChange(s.id);
            }}
            className={visual.grid}
            style={{
              background: isActive ? "var(--bg-panel)" : "transparent",
              borderLeft: `2px solid ${isActive ? "var(--accent)" : "transparent"}`,
              color: isActive ? "var(--fg)" : "var(--fg-muted)",
            }}
            onMouseEnter={(e) => {
              if (!isActive) e.currentTarget.style.background = "var(--bg-hover)";
            }}
            onMouseLeave={(e) => {
              if (!isActive) e.currentTarget.style.background = "transparent";
            }}
          >
            <Icon name={s.icon} size={11} />
            <span className={visual.surface2}>{t(s.labelKey)}</span>
            <span className={visual.row}>
              {errs > 0 && <ErrCount tone="danger" n={errs} />}
              {warns > 0 && errs === 0 && <ErrCount tone="warn" n={warns} />}
              {s.locked && <Icon name="lock" size={9} className={visual.surface3} />}
            </span>
          </button>
        );
      })}
    </div>
  );
}
