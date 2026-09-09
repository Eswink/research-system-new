import type { BudgetViewDto, UsageEntryDto } from "../../api/types";

export function ledgerMinorText(value: number | null, currency: string | null): string {
  if (value === null) return "UNKNOWN (not 0)";
  const unit = currency === null || currency === "" ? "UNKNOWN CURRENCY" : currency;
  return `${String(value)} ${unit} minor units`;
}

/** An unmetered quantity is not rendered as a measured zero. */
export function ledgerQuantityText(entry: UsageEntryDto): string {
  return entry.quantity_status === "KNOWN"
    ? `${String(entry.quantity)} ${entry.unit}`
    : `${entry.quantity_status} · ${entry.unavailable_reason ?? "quantity unavailable"}`;
}

export function ledgerSummary(view: BudgetViewDto | null) {
  return {
    total:
      view === null ? "—" : ledgerMinorText(view.total_estimated_cost_minor, view.total_currency),
    subtotal:
      view === null ? "—" : ledgerMinorText(view.known_cost_subtotal_minor, view.total_currency),
    unknownEntries: view === null ? "—" : String(view.unknown_cost_entries),
    reservations: view === null ? "—" : String(view.reservations.length),
  };
}
