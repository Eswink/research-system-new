import { FormRow } from "../FormRow";
import { Select } from "../Select";

interface ModelRegistryFormProviderProps {
  t: (key: string, fallback?: string) => string;
}

export function ModelRegistryFormProvider({ t }: ModelRegistryFormProviderProps) {
  return (
    <FormRow label={t("mr.form.provider")} required>
      <Select
        name="provider"
        defaultValue="Anthropic"
        options={[
          { value: "Anthropic", label: "Anthropic" },
          { value: "OpenAI", label: "OpenAI" },
          { value: "Google", label: "Google" },
          { value: "Meta", label: "Meta" },
          { value: "Alibaba", label: "Alibaba" },
          { value: "custom", label: t("mr.form.providerOther") },
        ]}
      />
    </FormRow>
  );
}
