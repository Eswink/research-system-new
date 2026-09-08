import type { ReactNode } from "react";

import { Icon } from "../../../components/Icon";
import { cx } from "../../../components/cx";
import { useI18n } from "../../../i18n/useI18n";
import styles from "./EditorLayout.module.css";

export type SectionId = "identity" | "phases";

interface SectionMeta {
  id: SectionId;
  labelKey: "editor.section.identity" | "editor.section.phases";
  icon: "shield" | "hex";
}

const SECTIONS: readonly SectionMeta[] = [
  { id: "identity", labelKey: "editor.section.identity", icon: "shield" },
  { id: "phases", labelKey: "editor.section.phases", icon: "hex" },
];

export interface SectionIssueCounts {
  identity: { errors: number; warnings: number };
  phases: { errors: number; warnings: number };
}

/** 左侧区块导航（错误计数徽章 + 底部汇总；键盘可达） */
export function SectionNav({
  active,
  onChange,
  counts,
}: {
  active: SectionId;
  onChange: (section: SectionId) => void;
  counts: SectionIssueCounts;
}) {
  const { t } = useI18n();
  const totalErrors = SECTIONS.reduce((sum, s) => sum + counts[s.id].errors, 0);
  const totalWarns = SECTIONS.reduce((sum, s) => sum + counts[s.id].warnings, 0);
  return (
    <nav className={styles.sectionNav} aria-label={t("editor.nav.header")}>
      <div className={styles.sectionNavHeader}>{t("editor.nav.header")}</div>
      <div className={styles.sectionNavItems}>
        {SECTIONS.map((section) => (
          <SectionNavItem
            key={section.id}
            section={section}
            active={section.id === active}
            counts={counts[section.id]}
            onChange={onChange}
          />
        ))}
      </div>
      <SectionSummary totalErrors={totalErrors} totalWarns={totalWarns} />
    </nav>
  );
}

function SectionNavItem({
  section,
  active,
  counts,
  onChange,
}: {
  section: SectionMeta;
  active: boolean;
  counts: { errors: number; warnings: number };
  onChange: (section: SectionId) => void;
}) {
  const { t } = useI18n();
  return (
    <button
      type="button"
      className={cx(styles.sectionItem, active && styles.sectionItemActive)}
      aria-current={active ? "true" : undefined}
      onClick={() => {
        onChange(section.id);
      }}
    >
      <Icon name={section.icon} size={11} />
      <span className={styles.sectionLabel}>{t(section.labelKey)}</span>
      {counts.errors > 0 && <CountPill tone="danger" n={counts.errors} />}
      {counts.warnings > 0 && counts.errors === 0 && <CountPill tone="warn" n={counts.warnings} />}
    </button>
  );
}

function SectionSummary({ totalErrors, totalWarns }: { totalErrors: number; totalWarns: number }) {
  const { t } = useI18n();
  return (
    <div className={styles.sectionNavFooter}>
      <div className={styles.summaryRow}>
        <span>{t("editor.nav.errors")}</span>
        <span className={totalErrors > 0 ? styles.summaryDanger : styles.summaryOk}>
          {totalErrors}
        </span>
      </div>
      <div className={styles.summaryRow}>
        <span>{t("editor.nav.warnings")}</span>
        <span className={totalWarns > 0 ? styles.summaryWarn : styles.summaryFaint}>
          {totalWarns}
        </span>
      </div>
    </div>
  );
}

function CountPill({ tone, n }: { tone: "danger" | "warn"; n: number }) {
  return (
    <span className={cx(styles.pill, tone === "danger" ? styles.pillDanger : styles.pillWarn)}>
      {n}
    </span>
  );
}

/** 区块头（标题 + 副标题 + 右侧 extra chip） */
export function SectionHeader({
  title,
  subtitle,
  extra,
}: {
  title: string;
  subtitle: string;
  extra?: ReactNode;
}) {
  return (
    <div className={styles.sectionHeader}>
      <div>
        <div className={styles.sectionTitle}>{title}</div>
        <div className={styles.sectionSubtitle}>{subtitle}</div>
      </div>
      {extra !== undefined && <div className={styles.sectionExtra}>{extra}</div>}
    </div>
  );
}
