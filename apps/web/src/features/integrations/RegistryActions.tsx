import { useState } from "react";

import { api } from "../../api/client";
import type { ToolProviderRegistrationDto } from "../../api/types";
import { ErrorState } from "../../components/States";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import styles from "../ops-view/OpsActions.module.css";

/**
 * 注册行内动作（G15）：健康复核 / 批准 / 吊销。
 *
 * - PENDING → 可批准；ACTIVE/ PENDING → 可吊销（理由必填，终态退出目录）；
 * - REVOKED 为终态：不再提供任何处置按钮（服务端也会 409）。
 */
export function RegistryActions({
  registration,
  zh,
  onDone,
}: {
  registration: ToolProviderRegistrationDto;
  zh: boolean;
  onDone: () => void;
}) {
  if (registration.state === "REVOKED") {
    return (
      <span className="mono" data-testid="registry-revoked">
        {registration.revoked_reason ?? (zh ? "已吊销" : "revoked")}
      </span>
    );
  }
  return (
    <span className={styles.row} data-testid="registry-actions">
      <HealthCheckButton providerId={registration.id} zh={zh} onDone={onDone} />
      {registration.state === "PENDING" && (
        <ApproveButton providerId={registration.id} zh={zh} onDone={onDone} />
      )}
      <RevokeControl providerId={registration.id} zh={zh} onDone={onDone} />
    </span>
  );
}

function HealthCheckButton({
  providerId,
  zh,
  onDone,
}: {
  providerId: string;
  zh: boolean;
  onDone: () => void;
}) {
  const action = useAsyncAction(onDone);
  return (
    <span className={styles.row}>
      <button
        className="btn sm ghost"
        type="button"
        data-testid="registry-health-check"
        disabled={action.busy}
        onClick={() => {
          action.run(() => api.healthCheckToolProvider(providerId));
        }}
      >
        {zh ? "健康复核" : "Health check"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </span>
  );
}

function ApproveButton({
  providerId,
  zh,
  onDone,
}: {
  providerId: string;
  zh: boolean;
  onDone: () => void;
}) {
  const action = useAsyncAction(onDone);
  return (
    <span className={styles.row}>
      <button
        className="btn sm"
        type="button"
        data-testid="registry-approve"
        disabled={action.busy}
        onClick={() => {
          action.run(() => api.approveToolProvider(providerId));
        }}
      >
        {zh ? "批准" : "Approve"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </span>
  );
}

function RevokeControl({
  providerId,
  zh,
  onDone,
}: {
  providerId: string;
  zh: boolean;
  onDone: () => void;
}) {
  const [reason, setReason] = useState("");
  const action = useAsyncAction(onDone);
  return (
    <span className={styles.row}>
      <input
        className="input"
        value={reason}
        placeholder={zh ? "吊销理由" : "Revocation reason"}
        data-testid="registry-revoke-reason"
        onChange={(event) => {
          setReason(event.target.value);
        }}
      />
      <button
        className="btn sm danger"
        type="button"
        data-testid="registry-revoke"
        disabled={action.busy || reason.trim() === ""}
        onClick={() => {
          action.run(() => api.revokeToolProvider(providerId, reason.trim()));
          setReason("");
        }}
      >
        {zh ? "吊销" : "Revoke"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </span>
  );
}
