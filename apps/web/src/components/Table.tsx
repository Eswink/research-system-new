import { useMemo, useState, type ReactNode } from "react";

import { cx } from "./cx";
import { Icon } from "./Icon";
import styles from "./Table.module.css";

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

/** 数据表格：行选择、列排序、键盘可达；行高/密度走令牌。 */
export function Table<Row>(props: TableProps<Row>) {
  const { columns, rows, onSortChange } = props;
  const [sort, setSort] = useState<SortState>(null);
  const sorted = useMemo(() => sortRows(rows, columns, sort), [rows, columns, sort]);
  const toggleSort = (key: string): void => {
    const next: SortState =
      sort?.key === key ? (sort.dir === "asc" ? { key, dir: "desc" } : null) : { key, dir: "asc" };
    setSort(next);
    onSortChange?.(next);
  };
  return (
    <div className={styles.scroller} role="region" aria-label={props.ariaLabel} tabIndex={0}>
      <table className={styles.table} aria-label={props.ariaLabel}>
        <TableHead
          columns={columns}
          sort={sort}
          onToggleSort={toggleSort}
          multiSelect={props.multiSelect === true}
        />
        <tbody>
          {sorted.length === 0 && (
            <tr>
              <td
                colSpan={columns.length + (props.multiSelect === true ? 1 : 0)}
                className={styles.emptyCell}
              >
                {props.empty}
              </td>
            </tr>
          )}
          {sorted.map((row) => (
            <TableRow key={props.rowKey(row)} row={row} {...props} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function sortRows<Row>(
  rows: readonly Row[],
  columns: readonly Column<Row>[],
  sort: SortState,
): readonly Row[] {
  if (sort === null) {
    return rows;
  }
  const column = columns.find((c) => c.key === sort.key);
  if (column?.sortValue === undefined) {
    return rows;
  }
  const factor = sort.dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const va = column.sortValue?.(a);
    const vb = column.sortValue?.(b);
    if (typeof va === "number" && typeof vb === "number") {
      return (va - vb) * factor;
    }
    return String(va ?? "").localeCompare(String(vb ?? "")) * factor;
  });
}

function TableHead<Row>({
  columns,
  sort,
  onToggleSort,
  multiSelect,
}: {
  columns: readonly Column<Row>[];
  sort: SortState;
  onToggleSort: (key: string) => void;
  multiSelect: boolean;
}) {
  return (
    <thead>
      <tr>
        {multiSelect && <th className={styles.checkCol} aria-label="选择" />}
        {columns.map((column) => (
          <th
            key={column.key}
            style={{ width: column.width, textAlign: column.align ?? "left" }}
            aria-sort={
              sort?.key === column.key
                ? sort.dir === "asc"
                  ? "ascending"
                  : "descending"
                : undefined
            }
          >
            {column.sortable === true ? (
              <button
                type="button"
                className={styles.sortBtn}
                onClick={() => { onToggleSort(column.key); }}
              >
                {column.header}
                <SortIcon
                  active={sort?.key === column.key}
                  desc={sort?.key === column.key && sort.dir === "desc"}
                />
              </button>
            ) : (
              column.header
            )}
          </th>
        ))}
      </tr>
    </thead>
  );
}

function SortIcon({ active, desc }: { active: boolean; desc: boolean }) {
  return (
    <Icon
      name={desc ? "chevron-d" : "chevron-r"}
      size={9}
      className={active ? styles.sortActive : styles.sortIdle}
      style={desc ? undefined : { transform: "rotate(-90deg)" }}
    />
  );
}

function TableRow<Row>({
  row,
  columns,
  rowKey,
  selectable,
  selectedKey,
  onSelectRow,
  multiSelect,
  selectedKeys,
  onToggleRow,
  rowHref,
}: TableProps<Row> & { row: Row }) {
  const key = rowKey(row);
  const selected =
    multiSelect === true
      ? selectedKeys?.has(key) === true
      : selectable === true && key === selectedKey;
  const interactive = selectable === true || multiSelect === true;
  const activate = (): void => {
    if (multiSelect === true) {
      onToggleRow?.(row);
    } else {
      onSelectRow?.(row);
    }
  };
  return (
    <tr
      className={cx(styles.row, selected && styles.selected)}
      aria-selected={interactive ? selected : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? activate : undefined}
      onKeyDown={interactive ? (event) => { onRowKey(event, activate); } : undefined}
    >
      {multiSelect === true && (
        <td className={styles.checkCol}>
          <input
            type="checkbox"
            checked={selected}
            readOnly
            tabIndex={-1}
            aria-label={`选择 ${key}`}
          />
        </td>
      )}
      <RowCells row={row} columns={columns} href={rowHref?.(row)} />
    </tr>
  );
}

function onRowKey(event: React.KeyboardEvent, activate: () => void): void {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    activate();
  }
}

function RowCells<Row>({
  row,
  columns,
  href,
}: {
  row: Row;
  columns: readonly Column<Row>[];
  href: string | undefined;
}) {
  return (
    <>
      {columns.map((column) => (
        <td key={column.key} style={{ textAlign: column.align ?? "left" }}>
          {href !== undefined ? (
            <a href={href} className={styles.rowLink}>
              {column.render(row)}
            </a>
          ) : (
            column.render(row)
          )}
        </td>
      ))}
    </>
  );
}
