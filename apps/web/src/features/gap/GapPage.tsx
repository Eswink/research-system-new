import type { ReactNode } from "react";

import { useI18n } from "../../i18n/useI18n";
import type { PageSupport } from "../../navigation/pageSupport";
import type { Route } from "../../navigation/registry";
import { Chip } from "../../components/Chip";
import { Icon } from "../../components/Icon";
import styles from "./GapPage.module.css";

/**
 * 缺口/部分支持页脚手架：呈现页面身份、支持等级与原因，
 * 保留工具栏/分栏结构占位，禁用未实现操作（不冒充"即将推出"卡片）。
 * T24-T27 将逐页替换为完整设计布局。
 */
export function GapPage({ route, support }: { route: Route; support: PageSupport }) {
  const { t } = useI18n();
  const title = t(`page.${route.domain}.${route.page}` as Parameters<typeof t>[0]);
  const levelLabel =
    support.level === "gap"
      ? t("support.gap")
      : support.level === "partial"
        ? t("support.partial")
        : t("support.full");
  return (
    <div className={styles.page} data-testid={`gap-page-${route.domain}-${route.page}`}>
      <div className={styles.toolbar}>
        <div className={styles.titleWrap}>
          <h2 className={styles.title}>{title}</h2>
          <Chip tone={support.level === "gap" ? "warn" : "accent"}>{levelLabel}</Chip>
        </div>
        <div className={styles.actions}>
          <button
            type="button"
            className="btn sm"
            disabled
            aria-disabled="true"
            title={support.reason}
          >
            <Icon name="plus" size={10} />
            {t("action.create")}
          </button>
        </div>
      </div>
      {support.reason !== undefined && (
        <div className={styles.reason}>
          <Icon name="q" size={12} />
          <span>{support.reason}</span>
        </div>
      )}
      <GapBody />
    </div>
  );
}

function GapBody(): ReactNode {
  const { t } = useI18n();
  return (
    <div className={styles.body}>
      <div className={styles.list}>
        <div className="row head">
          <span>{t("gap.column.item")}</span>
          <span>{t("gap.column.status")}</span>
        </div>
        <div className={styles.emptyRow}>
          <span className="empty-mark">{t("gap.noData")}</span>
        </div>
      </div>
      <aside className={styles.detail}>
        <div className={styles.detailTitle}>{t("gap.detail")}</div>
        <p className={styles.detailText}>{t("gap.detailHint")}</p>
      </aside>
    </div>
  );
}
