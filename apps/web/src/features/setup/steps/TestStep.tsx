import { Button } from "../../../components/Button";
import { cx } from "../../../components/cx";
import { StatusBadge } from "../../../components/StatusBadge";
import { useI18n } from "../../../i18n/useI18n";
import type { EndpointHealthDto, LlmEndpointReadDto } from "../../../api/types";
import styles from "./steps.module.css";

function HealthValue({ health }: { health: EndpointHealthDto }) {
  const { t } = useI18n();
  return (
    <>
      <StatusBadge
        tone={health.ok ? "success" : "danger"}
        label={health.ok ? t("setup.test.reachable") : t("setup.test.unreachable")}
      />
      {!health.ok && health.error_category !== null && (
        <span className="chip">{health.error_category}</span>
      )}
      {!health.ok && health.error_message_redacted !== null && (
        <span className="chip mono">{health.error_message_redacted}</span>
      )}
    </>
  );
}

function TestRows({
  endpoint,
  health,
}: {
  endpoint: LlmEndpointReadDto;
  health: EndpointHealthDto | null;
}) {
  const { t } = useI18n();
  return (
    <div className={styles.kv}>
      <div className={styles.kvRow}>
        <span className={styles.kvKey}>{t("setup.test.credential")}</span>
        <span className={styles.kvValue}>
          <span className="chip">{endpoint.credential}</span>
        </span>
      </div>
      {health !== null && (
        <div className={styles.kvRow} data-testid="wizard-health">
          <span className={styles.kvKey}>{t("setup.test.health")}</span>
          <span className={styles.kvValue}>
            <HealthValue health={health} />
          </span>
        </div>
      )}
    </div>
  );
}

/** Test 步骤：端点凭据状态 + 健康检查结果如实呈现（null 不渲染为可达）。 */
export function TestStep({
  endpoint,
  health,
  busy,
  onContinue,
  onProbe,
}: {
  endpoint: LlmEndpointReadDto;
  health: EndpointHealthDto | null;
  busy: boolean;
  onContinue: () => void;
  onProbe: () => void;
}) {
  const { t } = useI18n();
  return (
    <div className={cx("panel", styles.panel)} data-testid="wizard-test-step">
      <div className={styles.head}>
        <div className={styles.title}>{t("setup.test.title")}</div>
        <div className={styles.desc}>
          {t("setup.test.created")} · <span className="mono">{endpoint.name}</span>
        </div>
      </div>
      <TestRows endpoint={endpoint} health={health} />
      <div className={styles.actions}>
        <Button
          variant="primary"
          onClick={onContinue}
          disabled={busy}
          data-testid="wizard-continue"
        >
          {t("setup.test.continue")}
        </Button>
        <Button icon="flask" onClick={onProbe} disabled={busy} data-testid="wizard-probe">
          {busy ? t("setup.probing") : t("setup.test.probe")}
        </Button>
      </div>
    </div>
  );
}
