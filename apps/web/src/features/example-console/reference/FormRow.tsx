import { useId, type ReactNode } from "react";
import { ExampleFieldContext } from "../fieldContext";
import visual from "./FormRow.module.css";

/** A visible field label supplies a shared accessible name to its native controls. */
export function FormRow({
  label,
  hint,
  required = false,
  children,
}: {
  label: ReactNode;
  hint?: ReactNode;
  required?: boolean;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <div className={visual.surface}>
      <div className={visual.row}>
        <span id={id} className={visual.label}>
          {label} {required && <span className={visual.surface2}>*</span>}
        </span>
        {hint && (
          <span id={`${id}-hint`} className={visual.caption}>
            {hint}
          </span>
        )}
      </div>
      <ExampleFieldContext.Provider value={{ labelId: id, hintId: `${id}-hint`, required }}>
        {children}
      </ExampleFieldContext.Provider>
    </div>
  );
}
