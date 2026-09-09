import { useI18n } from "../i18n/useI18n";
import { Icon } from "./Icon";
import styles from "./Table.module.css";
import type { Column, SortState } from "./tableTypes";

interface HeaderProps<Row> {
  columns: readonly Column<Row>[];
  sort: SortState;
  onToggleSort: (key: string) => void;
  multiSelect: boolean;
}

export function TableHeader<Row>({ columns, sort, onToggleSort, multiSelect }: HeaderProps<Row>) {
  const { language } = useI18n();
  return (
    <thead>
      <tr>
        {multiSelect && (
          <th className={styles.checkCol} aria-label={language === "zh" ? "选择" : "Selection"} />
        )}
        {columns.map((column) => (
          <ColumnHeading key={column.key} column={column} sort={sort} onToggleSort={onToggleSort} />
        ))}
      </tr>
    </thead>
  );
}

function ColumnHeading<Row>({
  column,
  sort,
  onToggleSort,
}: {
  column: Column<Row>;
  sort: SortState;
  onToggleSort: (key: string) => void;
}) {
  const active = sort?.key === column.key;
  const descending = active && sort.dir === "desc";
  return (
    <th
      style={{ width: column.width, textAlign: column.align ?? "left" }}
      aria-sort={active ? (descending ? "descending" : "ascending") : undefined}
    >
      {column.sortable === true ? (
        <button
          type="button"
          className={styles.sortBtn}
          onClick={() => {
            onToggleSort(column.key);
          }}
        >
          {column.header}
          <Icon
            name={descending ? "chevron-d" : "chevron-r"}
            size={9}
            className={active ? styles.sortActive : styles.sortIdle}
            style={descending ? undefined : { transform: "rotate(-90deg)" }}
          />
        </button>
      ) : (
        column.header
      )}
    </th>
  );
}
