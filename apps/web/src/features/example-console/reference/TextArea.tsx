import type { TextareaHTMLAttributes } from "react";
import { useExampleField } from "../fieldContext";
import visual from "./TextArea.module.css";

type Props = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange"> & {
  onChange?: (value: string) => void;
  mono?: boolean;
};

export function TextArea({ onChange, mono, rows = 3, ...props }: Props) {
  const field = useExampleField();
  return (
    <textarea
      {...field}
      {...props}
      rows={rows}
      className={visual.field}
      style={{ fontFamily: mono ? "var(--font-mono)" : "inherit" }}
      onChange={(event) => {
        onChange?.(event.target.value);
      }}
    />
  );
}
