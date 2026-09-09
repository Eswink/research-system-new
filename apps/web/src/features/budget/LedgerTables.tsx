import type { BudgetViewDto, UsageEntryDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { ledgerMinorText, ledgerQuantityText } from "./ledgerPresentation";

export function LedgerTables({ view }: { view: BudgetViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <>
      <PanelSection
        title={zh ? "使用账本明细" : "Usage ledger entries"}
        count={view.entries.length}
      >
        <Table
          columns={usageColumns(zh)}
          rows={view.entries}
          rowKey={(entry) => entry.entry_id}
          ariaLabel={zh ? "使用账本" : "Usage ledger"}
          empty={<EmptyState message={zh ? "没有已记录用量" : "No recorded usage"} />}
        />
      </PanelSection>
      <PanelSection
        title={zh ? "资源预留 · 不等于已计费" : "Reservations · not incurred cost"}
        count={view.reservations.length}
      >
        <Table
          columns={reservationColumns(zh)}
          rows={view.reservations}
          rowKey={(reservation) => reservation.id}
          ariaLabel={zh ? "资源预留" : "Resource reservations"}
          empty={<EmptyState message={zh ? "没有资源预留记录" : "No reservation records"} />}
        />
      </PanelSection>
    </>
  );
}

function usageColumns(zh: boolean): Column<UsageEntryDto>[] {
  return [
    {
      key: "id",
      header: "Entry",
      render: (entry) => (
        <span className="mono" title={entry.entry_id}>
          {entry.entry_id.slice(0, 16)}
        </span>
      ),
    },
    { key: "resource", header: zh ? "资源" : "Resource", render: (entry) => entry.resource_type },
    {
      key: "quantity",
      header: zh ? "数量与计量状态" : "Quantity and metering",
      render: ledgerQuantityText,
    },
    {
      key: "status",
      header: zh ? "费用状态" : "Cost state",
      render: (entry) => (
        <Chip tone={entry.cost_status === "UNKNOWN" ? "unknown" : "neutral"}>
          {entry.cost_status}
        </Chip>
      ),
    },
    {
      key: "estimated",
      header: zh ? "估算金额" : "Estimated amount",
      render: (entry) => ledgerMinorText(entry.estimated_cost_minor, entry.currency),
    },
    {
      key: "actual",
      header: zh ? "实际金额" : "Actual amount",
      render: (entry) => ledgerMinorText(entry.actual_cost_minor, entry.currency),
    },
    { key: "attempt", header: "Attempt", render: (entry) => entry.attempt },
  ];
}

function reservationColumns(zh: boolean): Column<BudgetViewDto["reservations"][number]>[] {
  return [
    { key: "id", header: "ID", render: (reservation) => reservation.id },
    { key: "scope", header: zh ? "范围" : "Scope", render: (reservation) => reservation.scope },
    {
      key: "resource",
      header: zh ? "资源" : "Resource",
      render: (reservation) => reservation.resource_type,
    },
    {
      key: "quantity",
      header: zh ? "数量" : "Quantity",
      render: (reservation) => `${String(reservation.quantity)} ${reservation.unit}`,
    },
  ];
}
