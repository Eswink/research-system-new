import type { CostAmountDto, CostDimensionDto, CostViewDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

export function costAmountText(amount: CostAmountDto): string {
  return amount.minor_units === null
    ? `${amount.status} · n/a (not 0)`
    : `${amount.status} · ${String(amount.minor_units)} ${amount.currency} minor units`;
}

export function CostView({ cost }: { cost: CostViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div className={styles.page} data-testid="cost-view">
      <PanelSection
        title={zh ? "费用投影 · 账本来源" : "Cost projection · ledger source"}
        extra={
          <Chip tone={cost.total.minor_units === null ? "unknown" : "accent"}>
            {costAmountText(cost.total)}
          </Chip>
        }
      >
        <KeyValueList
          fields={[
            { label: "Run", value: cost.run_id },
            { label: "Pricing version", value: cost.pricing_version },
            { label: "Pricing digest", value: cost.pricing_digest },
            { label: "Pricing state", value: cost.pricing_frozen ? "FROZEN" : "NOT FROZEN" },
            { label: "Method", value: cost.total.calculation_method ?? "UNKNOWN" },
            { label: "Effective from", value: cost.total.effective_from ?? "UNKNOWN" },
          ]}
        />
        {cost.pricing_degraded_reason !== null && (
          <p className={styles.notice} data-testid="cost-degraded">
            {cost.pricing_degraded_reason}
          </p>
        )}
        <p className={styles.notice}>
          {zh
            ? "金额、币种与五态费用分类来自服务端。不同维度不相加，未知不归零，也不在浏览器推导价格。"
            : [
                "Amounts, currencies and five-state cost classifications come from the ",
                "server. Dimensions are not summed; unknown is not zero; no browser-side ",
                "pricing.",
              ].join("")}
        </p>
      </PanelSection>
      <CostDimensions dimensions={cost.dimensions} />
    </div>
  );
}

function CostDimensions({ dimensions }: { dimensions: CostDimensionDto[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const columns: Column<CostDimensionDto>[] = [
    { key: "dimension", header: zh ? "维度" : "Dimension", render: (item) => item.dimension },
    {
      key: "resource",
      header: zh ? "资源" : "Resource",
      render: (item) => <span className="mono">{item.resource_key}</span>,
    },
    {
      key: "amount",
      header: zh ? "状态与原始金额" : "Status and raw amount",
      render: (item) => costAmountText(item.amount),
    },
    { key: "entries", header: zh ? "条目" : "Entries", render: (item) => item.entry_count },
  ];
  return (
    <PanelSection title={zh ? "分维度明细" : "Dimension breakdown"}>
      <Table
        columns={columns}
        rows={dimensions}
        rowKey={(item) => `${item.dimension}/${item.resource_key}`}
        ariaLabel={zh ? "费用维度明细" : "Cost dimensions"}
        empty={
          <EmptyState message={zh ? "没有可投影的费用维度" : "No projected cost dimensions"} />
        }
      />
    </PanelSection>
  );
}
