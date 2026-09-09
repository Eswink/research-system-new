import { Icon } from "./Icon";
import visual from "./SearchInput.module.css";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const SearchInput = ({
  value,
  onChange,
  placeholder = "Filter…",
  width = 200,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  width?: number;
}) => (
  <div className={visual.row} style={{ width }}>
    <Icon name="search" size={11} className={visual.surface} />
    <input
      value={value}
      onChange={(e) => {
        onChange(e.target.value);
      }}
      placeholder={placeholder}
      className={visual.field}
    />
  </div>
);
