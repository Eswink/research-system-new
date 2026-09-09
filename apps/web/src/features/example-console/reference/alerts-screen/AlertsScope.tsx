import { FormRow } from "../FormRow";
import { Select } from "../Select";

interface AlertsScopeProps {
  t: (key: string, fallback?: string) => string;
}

export function AlertsScope({ t }: AlertsScopeProps) {
  return (
    <FormRow label={t("lbl.scope")}>
      <Select
        name="scope"
        defaultValue="budget"
        options={[
          { value: "budget", label: "Budget" },
          { value: "endpoint", label: "Endpoint" },
          { value: "model", label: "Model" },
          { value: "run", label: "Run" },
          { value: "claim", label: "Claim" },
        ]}
      />
    </FormRow>
  );
}
