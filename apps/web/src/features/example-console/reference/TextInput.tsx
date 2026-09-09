import type { InputHTMLAttributes } from "react";
import { useExampleField } from "../fieldContext";
import visual from "./TextInput.module.css";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> & {
  onChange?: ((value: string) => void) | undefined;
  mono?: boolean;
};

export function TextInput({ onChange, mono, ...props }: Props) {
  const field = useExampleField();
  return (
    <input
      {...field}
      {...props}
      className={visual.field}
      style={{ fontFamily: mono ? "var(--font-mono)" : "inherit" }}
      onChange={(event) => {
        onChange?.(event.target.value);
      }}
    />
  );
}
