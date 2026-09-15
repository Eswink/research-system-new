import { useState } from "react";

import { api } from "../../api/client";
import { ErrorState } from "../../components/States";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import {
  EMPTY_DRAFT,
  RegistryDraftFields,
  type RegistryDraft,
} from "./RegistryDraftFields";

/**
 * 注册 provider（G15：POST /tool-provider-registrations）。
 *
 * pin 必填且是 sha256:<hex>；服务端拒绝可漂移字面量（tag/分支名）。
 * 登记后为 PENDING——不进入目录，需显式批准才被 preflight/compile 看到。
 */
export function RegistryForm({ zh, onRegistered }: { zh: boolean; onRegistered: () => void }) {
  const [draft, setDraft] = useState<RegistryDraft>(EMPTY_DRAFT);
  const action = useAsyncAction(onRegistered);
  const patch = (next: Partial<RegistryDraft>): void => {
    setDraft((current) => ({ ...current, ...next }));
  };
  const capabilities = parseCapabilities(draft.capabilities);
  const ready =
    draft.providerId.trim() !== "" && capabilities.length > 0 && draft.pin.trim() !== "";
  const submit = (): void => {
    if (!ready) return;
    action.run(() =>
      api.registerToolProvider({
        id: draft.providerId.trim(),
        kind: draft.kind,
        capabilities,
        pinned_revision: draft.pin.trim(),
      }),
    );
    setDraft((current) => ({ ...current, capabilities: "" }));
  };
  return (
    <form
      className="toolbar"
      data-testid="registry-register"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <RegistryDraftFields draft={draft} patch={patch} zh={zh} />
      <button
        className="btn"
        type="submit"
        data-testid="registry-submit"
        disabled={action.busy || !ready}
      >
        {zh ? "登记" : "Register"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </form>
  );
}

function parseCapabilities(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item !== "");
}
