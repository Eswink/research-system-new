import { useI18n } from "../../../i18n/useI18n";
import { PasswordField, SelectField, TextField } from "./fields";

const API_STYLE_OPTIONS = [
  { value: "chat_completions", label: "chat/completions" },
  { value: "responses", label: "responses" },
] as const;

export interface FormFieldsProps {
  name: string;
  setName: (value: string) => void;
  baseUrl: string;
  setBaseUrl: (value: string) => void;
  apiStyle: string;
  setApiStyle: (value: string) => void;
  apiKey: string;
  setApiKey: (value: string) => void;
}

export function FormFields({
  name,
  setName,
  baseUrl,
  setBaseUrl,
  apiStyle,
  setApiStyle,
  apiKey,
  setApiKey,
}: FormFieldsProps) {
  const { t } = useI18n();
  return (
    <>
      <TextField
        label={t("setup.f.name")}
        value={name}
        onChange={setName}
        placeholder="my-relay"
        autoComplete="off"
      />
      <TextField
        label={t("setup.f.baseUrl")}
        value={baseUrl}
        onChange={setBaseUrl}
        placeholder="https://relay.example.com/api/v1"
        autoComplete="url"
        required
        mono
      />
      <SelectField
        label={t("setup.f.apiStyle")}
        value={apiStyle}
        onChange={setApiStyle}
        options={API_STYLE_OPTIONS}
      />
      <PasswordField
        label={t("setup.f.apiKey")}
        hint={t("setup.f.apiKeyHint")}
        value={apiKey}
        onChange={setApiKey}
      />
    </>
  );
}
