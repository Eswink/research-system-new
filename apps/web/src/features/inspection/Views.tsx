import type { BudgetViewDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

export function usageTotalText(usage: BudgetViewDto): string {
  if (usage.total_estimated_cost_minor === null) return "UNKNOWN (not 0)";
  return [
    String(usage.total_estimated_cost_minor),
    usage.total_currency ?? "UNKNOWN CURRENCY",
    "minor units",
  ].join(" ");
}

export function UsageView({ usage }: { usage: BudgetViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div data-testid="usage-view">
      <PanelSection title={zh ? "关联运行的使用账本" : "Associated run usage ledger"}>
        <p className={styles.notice}>
          {usageTotalText(usage)} · {zh ? "未知费用条目：" : "Unknown-cost entries: "}
          {usage.unknown_cost_entries} · UNKNOWN ≠ 0
        </p>
        {usage.entries.length === 0 ? (
          <EmptyState message={zh ? "没有账本条目" : "No ledger entries"} />
        ) : (
          <div className={styles.cards}>
            {usage.entries.map((entry) => (
              <article key={entry.entry_id} className={styles.card}>
                <div className={styles.cardHead}>
                  <strong>{entry.resource_type}</strong>
                  <Chip tone={entry.cost_status === "UNKNOWN" ? "unknown" : "neutral"}>
                    {entry.cost_status}
                  </Chip>
                </div>
                <span className="mono">
                  {entry.quantity} {entry.unit}
                </span>
              </article>
            ))}
          </div>
        )}
      </PanelSection>
    </div>
  );
}
