import { InlineSelect, InlineTextInput } from "../../components/InlineFields";

export const PROVIDER_KINDS = ["REST", "MCP", "CLI", "REMOTE_WORKER", "NATIVE"] as const;

export interface RegistryDraft {
  providerId: string;
  kind: string;
  capabilities: string;
  pin: string;
}

export const EMPTY_DRAFT: RegistryDraft = {
  providerId: "",
  kind: "REST",
  capabilities: "",
  pin: "",
};

/** 注册表单的字段区（单独成文件：让 RegistryForm 主体保持在 50 行内）。 */
export function RegistryDraftFields({
  draft,
  patch,
  zh,
}: {
  draft: RegistryDraft;
  patch: (next: Partial<RegistryDraft>) => void;
  zh: boolean;
}) {
  return (
    <>
      <InlineTextInput
        value={draft.providerId}
        onChange={(next) => {
          patch({ providerId: next });
        }}
        placeholder="provider id"
        testid="registry-id"
      />
      <InlineSelect
        value={draft.kind}
        onChange={(next) => {
          patch({ kind: next });
        }}
        options={PROVIDER_KINDS}
        testid="registry-kind"
      />
      <InlineTextInput
        value={draft.capabilities}
        onChange={(next) => {
          patch({ capabilities: next });
        }}
        placeholder={zh ? "能力（逗号分隔）" : "capabilities (comma separated)"}
        testid="registry-capabilities"
      />
      <InlineTextInput
        value={draft.pin}
        onChange={(next) => {
          patch({ pin: next });
        }}
        placeholder="sha256:<hex>"
        testid="registry-pin"
      />
    </>
  );
}
