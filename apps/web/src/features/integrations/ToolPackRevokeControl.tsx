import { useState } from "react";

import { api } from "../../api/client";
import type { ToolPackDto } from "../../api/types";
import { ErrorState } from "../../components/States";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import styles from "../ops-view/OpsActions.module.css";

/**
 * 吊销动作（G15 / PLAN-065）：理由必填，服务端同样拒绝空理由（422）。
 *
 * REVOKED 是终态——不再提供动作，避免用户以为还能恢复。
 */
export function ToolPackRevokeControl({
  pack,
  zh,
  onChanged,
}: {
  pack: ToolPackDto;
  zh: boolean;
  onChanged: () => void;
}) {
  if (pack.state === "REVOKED") {
    return (
      <span className="mono" data-testid={`toolpack-revoked-${pack.id}`}>
        {pack.revoked_reason ?? (zh ? "已吊销" : "revoked")}
      </span>
    );
  }
  return <RevokeForm packId={pack.id} zh={zh} onChanged={onChanged} />;
}

function RevokeForm({
  packId,
  zh,
  onChanged,
}: {
  packId: string;
  zh: boolean;
  onChanged: () => void;
}) {
  const [reason, setReason] = useState("");
  const action = useAsyncAction(onChanged);
  return (
    <span className={styles.row}>
      <input
        className="input"
        value={reason}
        placeholder={zh ? "吊销理由" : "Revocation reason"}
        aria-label={zh ? `吊销理由（${packId}）` : `Revocation reason (${packId})`}
        data-testid={`toolpack-revoke-reason-${packId}`}
        onChange={(event) => {
          setReason(event.target.value);
        }}
      />
      <button
        className="btn sm danger"
        type="button"
        data-testid={`toolpack-revoke-${packId}`}
        disabled={action.busy || reason.trim() === ""}
        onClick={() => {
          action.run(() => api.revokeToolPack(packId, reason.trim()));
          setReason("");
        }}
      >
        {zh ? "吊销" : "Revoke"}
      </button>
      {action.error !== null && (
        <span data-testid={`toolpack-revoke-error-${packId}`}>
          <ErrorState message={action.error} />
        </span>
      )}
    </span>
  );
}
