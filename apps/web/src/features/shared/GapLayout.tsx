import type { ReactNode } from "react";

import { Button } from "../../components/Button";
import { Chip } from "../../components/Chip";
import { Icon } from "../../components/Icon";
import { useI18n } from "../../i18n/useI18n";
import type { PageSupport } from "../../navigation/pageSupport";
import styles from "./GapLayout.module.css";

/**
 * 缺口页设计布局（T24-T27）：还原每页工具栏 + 主列表 + 详情分栏结构，
 * 逐操作禁用并说明后端缺口；不替换为统一"即将推出"卡片。
 */
export function GapLayout({
  title,
  support,
  columns,
  actions = [],
  detailTitle,
  detailHint,
  children,
}: {
  title: string;
  support: PageSupport;
  columns: readonly string[];
  actions?: readonly { label: string; reason?: string }[];
  detailTitle?: string;
  detailHint?: string;
  children?: ReactNode;
}) {
  const { t } = useI18n();
  const level = support.level === "gap" ? t("support.gap") : t("support.partial");
  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <div className={styles.titleWrap}>
          <h2 className={styles.title}>{title}</h2>
          <Chip tone={support.level === "gap" ? "warn" : "accent"}>{level}</Chip>
        </div>
        <div className={styles.actions}>
          {actions.map((action) => (
            <Button
              key={action.label}
              size="sm"
              icon="plus"
              disabledReason={action.reason ?? support.reason}
            >
              {action.label}
            </Button>
          ))}
        </div>
      </div>
      {support.reason !== undefined && <ReasonBanner reason={support.reason} />}
      <div className={styles.body}>
        <GapList columns={columns}>{children}</GapList>
        <aside className={styles.detail}>
          <div className={styles.detailTitle}>{detailTitle ?? t("gap.detail")}</div>
          <p className={styles.detailText}>{detailHint ?? t("gap.detailHint")}</p>
        </aside>
      </div>
    </div>
  );
}

function ReasonBanner({ reason }: { reason: string }) {
  return (
    <div className={styles.reason}>
      <Icon name="q" size={12} />
      <span>{reason}</span>
    </div>
  );
}

function GapList({ columns, children }: { columns: readonly string[]; children?: ReactNode }) {
  const { t } = useI18n();
  return (
    <div className={styles.list}>
      <div className="row head">
        {columns.map((c) => (
          <span key={c}>{c}</span>
        ))}
      </div>
      {children ?? (
        <div className={styles.emptyRow}>
          <span className="empty-mark">{t("gap.noData")}</span>
        </div>
      )}
    </div>
  );
}
