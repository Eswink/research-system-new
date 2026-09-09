import { useRef, useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type { RunDetailDto } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";

export function canRequestCancellation(state: string): boolean {
  return !new Set(["SUCCEEDED", "FAILED", "CANCELLED", "REJECTED"]).has(state);
}

/** No start shortcut bypasses the editor's compile/preflight flow. Cancellation is explicit. */
export function RunActions({
  run,
  busy,
  onChanged,
}: {
  run: RunDetailDto;
  busy: boolean;
  onChanged: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [confirm, setConfirm] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const active = useRef(false);
  const cancel = async () => {
    if (active.current || busy || !canRequestCancellation(run.state)) return;
    active.current = true;
    setPending(true);
    setError(null);
    try {
      await api.cancelRun(run.id);
      onChanged();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Cancellation failed");
    } finally {
      active.current = false;
      setPending(false);
      setConfirm(false);
    }
  };
  return <RunActionsSection {...{ busy, pending, run, setConfirm, zh, error, confirm, cancel }} />;
}

interface RunActionsSectionProps {
  busy: boolean;
  pending: boolean;
  run: RunDetailDto;
  setConfirm: Dispatch<SetStateAction<boolean>>;
  zh: boolean;
  error: string | null;
  confirm: boolean;
  cancel: () => Promise<void>;
}

function RunActionsSection({
  busy,
  pending,
  run,
  setConfirm,
  zh,
  error,
  confirm,
  cancel,
}: RunActionsSectionProps) {
  return (
    <div>
      <button
        type="button"
        className="btn sm"
        data-testid="run-cancel"
        disabled={busy || pending || !canRequestCancellation(run.state)}
        onClick={() => {
          setConfirm(true);
        }}
      >
        {zh ? "取消运行" : "Cancel run"}
      </button>
      {error !== null && <ErrorState message={error} />}
      <RunActionsConfirmDialog {...{ confirm, pending, zh, run, setConfirm, cancel }} />
    </div>
  );
}

interface RunActionsConfirmDialogProps {
  confirm: boolean;
  pending: boolean;
  zh: boolean;
  run: RunDetailDto;
  setConfirm: Dispatch<SetStateAction<boolean>>;
  cancel: () => Promise<void>;
}

function RunActionsConfirmDialog({
  confirm,
  pending,
  zh,
  run,
  setConfirm,
  cancel,
}: RunActionsConfirmDialogProps) {
  return (
    <ConfirmDialog
      open={confirm}
      danger
      busy={pending}
      title={zh ? "确认取消运行" : "Confirm cancellation"}
      consequence={
        <p>
          {run.id} ·{" "}
          {zh
            ? "向后端请求取消。已经产生的副作用可能无法撤销；界面等待后端状态，不假定任务立即停止。"
            : [
                "Request backend cancellation. Existing side effects may be irreversible; ",
                "tasks are not assumed to stop immediately.",
              ].join("")}
        </p>
      }
      confirmLabel={zh ? "请求取消" : "Request cancellation"}
      cancelLabel={zh ? "继续运行" : "Keep running"}
      onCancel={() => {
        setConfirm(false);
      }}
      onConfirm={() => {
        void cancel();
      }}
    />
  );
}
