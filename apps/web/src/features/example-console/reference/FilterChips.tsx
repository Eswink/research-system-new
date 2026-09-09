import visual from "./FilterChips.module.css";
import { Icon } from "./Icon";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const FilterChips = ({
  filters,
  onRemove,
}: {
  filters: { key: string; field: string; value: string }[];
  onRemove?: (key: string) => void;
}) =>
  filters.length === 0 ? null : (
    <div className={visual.row}>
      {filters.map((f) => (
        <span key={f.key} className={`chip ${visual.surface ?? ""}`}>
          <span className={visual.surface2}>{f.field}:</span> {f.value}
          <button onClick={() => onRemove?.(f.key)} className={visual.action}>
            <Icon name="x" size={8} />
          </button>
        </span>
      ))}
    </div>
  );
