import { useState } from "react";

import { api } from "../../api/client";
import type { LlmEndpointReadDto } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ErrorState } from "../../components/States";
import styles from "../shared/LivePage.module.css";

/**
 * 端点删除动作（WP-C 接线 WP-B DELETE /llm-endpoints/{id}）。
 *
 * 后端在 relay 被用户模型引用时返回 409（错误文案直接呈现）；凭据是进程内
 * 注册表，删除配置不回显任何密钥。
 */
export function EndpointDeleteAction({
  endpoint,
  zh,
  onDeleted,
}: {
  endpoint: LlmEndpointReadDto;
  zh: boolean;
  onDeleted: () => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runDelete = (): void => {
    setBusy(true);
    setError(null);
    void api
      .removeEndpoint(endpoint.id)
      .then(onDeleted)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : String(reason));
        setBusy(false);
        setConfirming(false);
      });
  };
  return (
    <>
      <DeleteButton zh={zh} busy={busy} onClick={() => { setConfirming(true); }} />
      {error !== null && <ErrorState message={error} />}
      <EndpointDeleteConfirm
        open={confirming}
        busy={busy}
        zh={zh}
        endpoint={endpoint}
        onConfirm={runDelete}
        onCancel={() => {
          setConfirming(false);
        }}
      />
    </>
  );
}

function DeleteButton({ zh, busy, onClick }: { zh: boolean; busy: boolean; onClick: () => void }) {
  return (
    <button
      className="btn sm danger"
      type="button"
      data-testid="endpoint-delete"
      disabled={busy}
      onClick={onClick}
    >
      {zh ? "删除端点" : "Delete endpoint"}
    </button>
  );
}

function EndpointDeleteConfirm({
  open,
  busy,
  zh,
  endpoint,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  busy: boolean;
  zh: boolean;
  endpoint: LlmEndpointReadDto;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <ConfirmDialog
      open={open}
      title={zh ? "确认删除端点" : "Confirm endpoint deletion"}
      consequence={
        <p className={styles.notice}>
          {endpoint.name} ·{" "}
          {zh
            ? "将删除该端点配置；被模型引用的端点会被后端拒绝（409）。凭据不落盘，随进程重启消散。"
            : [
                "This endpoint configuration will be deleted; endpoints referenced by ",
                "models are rejected by the backend (409). Credentials are process-local.",
              ].join("")}
        </p>
      }
      busy={busy}
      confirmLabel={zh ? "删除" : "Delete"}
      cancelLabel={zh ? "取消" : "Cancel"}
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  );
}
