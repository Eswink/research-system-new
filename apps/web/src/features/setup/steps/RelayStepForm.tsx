import type { LlmEndpointCreateDto } from "../../../api/types";
import { FormFields } from "./FormFields";
import { useRelayForm } from "./useRelayForm";

export function RelayStepForm({
  busy,
  error,
  onSubmit,
}: {
  busy: boolean;
  error: string | null;
  onSubmit: (payload: LlmEndpointCreateDto) => void;
}) {
  const form = useRelayForm(onSubmit);
  const formReady = form.baseUrl.length > 0;

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        form.submit();
      }}
    >
      <FormFields
        name={form.name}
        setName={form.setName}
        baseUrl={form.baseUrl}
        setBaseUrl={form.setBaseUrl}
        apiStyle={form.apiStyle}
        setApiStyle={form.setApiStyle}
        apiKey={form.apiKey}
        setApiKey={form.setApiKey}
      />
      {error !== null && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button type="submit" disabled={busy || !formReady}>
        {busy ? "Saving…" : "Create & Test Endpoint"}
      </button>
    </form>
  );
}