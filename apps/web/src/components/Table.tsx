import { useMemo, useState } from "react";
import styles from "./Table.module.css";
import { TableHeader } from "./TableHeader";
import { TableRow } from "./TableRows";
import { sortRows } from "./tableSorting";
import type { SortState, TableProps } from "./tableTypes";

export type { Column, SortState, TableProps } from "./tableTypes";

/** Presentation-only selection and sorting; the caller remains the owner of business commands. */
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
        <TableHeader
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
