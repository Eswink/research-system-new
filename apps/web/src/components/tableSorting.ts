import type { Column, SortState } from "./tableTypes";

export function sortRows<Row>(
  rows: readonly Row[],
  columns: readonly Column<Row>[],
  sort: SortState,
): readonly Row[] {
  if (sort === null) return rows;
  const sortValue = columns.find((column) => column.key === sort.key)?.sortValue;
  if (sortValue === undefined) return rows;
  const factor = sort.dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const left = sortValue(a);
    const right = sortValue(b);
    return typeof left === "number" && typeof right === "number"
      ? (left - right) * factor
      : String(left).localeCompare(String(right)) * factor;
  });
}
