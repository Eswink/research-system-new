import { PasswordField, SelectField, TextField } from "./fields";

const API_STYLE_OPTIONS = [
  { value: "chat_completions", label: "chat/completions" },
  { value: "responses", label: "responses" },
] as const;

export function FormFields({
  name,
  setName,
  baseUrl,
  setBaseUrl,
  apiStyle,
  setApiStyle,
  apiKey,
  setApiKey,
}: {
  name: string;
  setName: (value: string) => void;
  baseUrl: string;
  setBaseUrl: (value: string) => void;
  apiStyle: string;
  setApiStyle: (value: string) => void;
  apiKey: string;
  setApiKey: (value: string) => void;
}) {
  return (
    <FormFieldsContent
      {...{ name, setName, baseUrl, setBaseUrl, apiStyle, setApiStyle, apiKey, setApiKey }}
    />
  );
}

interface FormFieldsContentProps {
  name: string;
  setName: (value: string) => void;
  baseUrl: string;
  setBaseUrl: (value: string) => void;
  apiStyle: string;
  setApiStyle: (value: string) => void;
  apiKey: string;
  setApiKey: (value: string) => void;
}

function FormFieldsContent({
  name,
  setName,
  baseUrl,
  setBaseUrl,
  apiStyle,
  setApiStyle,
  apiKey,
  setApiKey,
}: FormFieldsContentProps) {
  return (
    <>
      <TextField
        label="Name"
        value={name}
        onChange={setName}
        placeholder="my-relay"
        autoComplete="off"
      />
      <TextField
        label="Relay Base URL"
        value={baseUrl}
        onChange={setBaseUrl}
        placeholder="https://relay.example.com/api/v1"
        autoComplete="url"
        required
      />
      <SelectField
        label="API Style"
        value={apiStyle}
        onChange={setApiStyle}
        options={API_STYLE_OPTIONS}
      />
      <PasswordField
        label="API Key（仅发送一次，不保存于浏览器）"
        value={apiKey}
        onChange={setApiKey}
      />
    </>
  );
}
