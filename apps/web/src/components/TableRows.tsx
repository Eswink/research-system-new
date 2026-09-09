import { useI18n } from "../i18n/useI18n";
import { cx } from "./cx";
import styles from "./Table.module.css";
import type { Column, TableProps } from "./tableTypes";

export function TableRow<Row>(props: TableProps<Row> & { row: Row }) {
  const { row, multiSelect, selectable } = props;
  const id = props.rowKey(row);
  const selected =
    multiSelect === true
      ? props.selectedKeys?.has(id) === true
      : selectable === true && id === props.selectedKey;
  const interactive = selectable === true || multiSelect === true;
  const activate = () => {
    if (multiSelect === true) props.onToggleRow?.(row);
    else props.onSelectRow?.(row);
  };
  return (
    <tr
      className={cx(styles.row, selected && styles.selected)}
      aria-selected={interactive ? selected : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={(event) => {
        if (
          interactive &&
          !(
            event.target instanceof Element &&
            event.target.closest("a,button,input,select,textarea")
          )
        )
          activate();
      }}
      onKeyDown={(event) => {
        if (
          interactive &&
          event.target === event.currentTarget &&
          (event.key === "Enter" || event.key === " ")
        ) {
          event.preventDefault();
          activate();
        }
      }}
    >
      {multiSelect === true && <SelectionCell selected={selected} id={id} onChange={activate} />}
      <RowCells row={row} columns={props.columns} href={props.rowHref?.(row)} />
    </tr>
  );
}

function SelectionCell({
  selected,
  id,
  onChange,
}: {
  selected: boolean;
  id: string;
  onChange: () => void;
}) {
  const { language } = useI18n();
  return (
    <td className={styles.checkCol}>
      <input
        type="checkbox"
        checked={selected}
        onChange={onChange}
        tabIndex={-1}
        aria-label={`${language === "zh" ? "选择" : "Select"} ${id}`}
      />
    </td>
  );
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
          {href === undefined ? (
            column.render(row)
          ) : (
            <a href={href} className={styles.rowLink}>
              {column.render(row)}
            </a>
          )}
        </td>
      ))}
    </>
  );
}
