import type { SelectHTMLAttributes } from "react";
import type { Option } from "../exampleTypes";
import { useExampleField } from "../fieldContext";
import visual from "./Select.module.css";

type Props = Omit<SelectHTMLAttributes<HTMLSelectElement>, "onChange"> & {
  onChange?: (value: string) => void;
  options: Option[];
};

/** Controlled and native draft fields share the same reference appearance. */
export function Select({ onChange, options, ...props }: Props) {
  const field = useExampleField();
  return (
    <select
      {...field}
      {...props}
      className={visual.field}
      onChange={(event) => {
        onChange?.(event.target.value);
      }}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value} disabled={option.disabled}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
