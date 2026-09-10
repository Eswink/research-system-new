import { Button } from "../../../components/Button";
import { cx } from "../../../components/cx";
import { useI18n } from "../../../i18n/useI18n";
import type { LlmEndpointCreateDto } from "../../../api/types";
import { ErrorRow } from "./ErrorRow";
import { FormFields } from "./FormFields";
import styles from "./steps.module.css";
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
  const { t } = useI18n();
  const form = useRelayForm(onSubmit);
  const formReady = form.baseUrl.length > 0;

  return (
    <form
      className={cx("panel", styles.panel)}
      data-testid="wizard-relay-step"
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
      {error !== null && <ErrorRow message={error} />}
      <div className={styles.actions}>
        <Button
          type="submit"
          variant="primary"
          disabled={busy || !formReady}
          disabledReason={formReady ? undefined : t("setup.f.baseUrl")}
        >
          {busy ? t("setup.saving") : t("setup.relay.submit")}
        </Button>
      </div>
    </form>
  );
}
