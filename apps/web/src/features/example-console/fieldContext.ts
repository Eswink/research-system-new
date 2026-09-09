import { createContext, useContext } from "react";

export interface ExampleField {
  labelId?: string;
  hintId?: string;
  required?: boolean;
}

export const ExampleFieldContext = createContext<ExampleField>({});

export function useExampleField() {
  const field = useContext(ExampleFieldContext);
  return {
    "aria-labelledby": field.labelId,
    "aria-describedby": field.hintId,
    required: field.required,
  };
}
