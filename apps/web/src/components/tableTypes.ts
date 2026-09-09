import type { ReactNode } from "react";

export interface Column<Row> {
  key: string;
  header: string;
  width?: string;
  align?: "left" | "right";
  sortable?: boolean;
  sortValue?: (row: Row) => string | number;
  render: (row: Row) => ReactNode;
}

export type SortState = { key: string; dir: "asc" | "desc" } | null;

export interface TableProps<Row> {
  columns: readonly Column<Row>[];
  rows: readonly Row[];
  rowKey: (row: Row) => string;
  selectable?: boolean;
  selectedKey?: string;
  onSelectRow?: (row: Row) => void;
  multiSelect?: boolean;
  selectedKeys?: ReadonlySet<string>;
  onToggleRow?: (row: Row) => void;
  onSortChange?: (sort: SortState) => void;
  empty?: ReactNode;
  ariaLabel: string;
  rowHref?: (row: Row) => string;
}
