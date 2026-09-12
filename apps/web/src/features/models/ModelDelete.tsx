import { useState } from "react";

import { api } from "../../api/client";
import type { ModelReadDto } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

/** 模型删除动作（WP-C 接线 WP-B DELETE /models/{id}；被 agent 绑定 → 409）。 */
export function ModelDeleteAction({
  model,
  onDeleted,
}: {
  model: ModelReadDto;
  onDeleted: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runDelete = (): void => {
    setBusy(true);
    setError(null);
    void api
      .removeModel(model.id)
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
      <ConfirmDialog
        open={confirming}
        title={zh ? "确认删除模型" : "Confirm model deletion"}
        consequence={<ModelDeleteConsequence model={model} zh={zh} />}
        busy={busy}
        confirmLabel={zh ? "删除" : "Delete"}
        cancelLabel={zh ? "取消" : "Cancel"}
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
    <div className={styles.toolbar}>
      <button
        className="btn sm danger"
        type="button"
        data-testid="model-delete"
        disabled={busy}
        onClick={onClick}
      >
        {zh ? "删除模型" : "Delete model"}
      </button>
    </div>
  );
}

function ModelDeleteConsequence({ model, zh }: { model: ModelReadDto; zh: boolean }) {
  return (
    <p>
      {model.model_name} ·{" "}
      {zh
        ? "将删除该模型配置；被 Agent 显式绑定的模型会被后端拒绝（409）。"
        : [
            "This model configuration will be deleted; models explicitly bound by ",
            "agents are rejected by the backend (409).",
          ].join("")}
    </p>
  );
}
