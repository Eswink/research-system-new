import type { Dispatch, SetStateAction } from "react";

import type { RunDetailDto } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ErrorState } from "../../components/States";
import { canPauseRun, canRequestCancellation, canResumeRun } from "./runTransitions";
import type { ControlPlane } from "./useRunControlPlane";

interface RunActionButtonRowProps {
  run: RunDetailDto;
  zh: boolean;
  busy: boolean;
  control: ControlPlane;
  confirm: boolean;
  setConfirm: Dispatch<SetStateAction<boolean>>;
  cancel: () => Promise<void>;
  pause: () => void;
  resume: () => void;
}

export function RunActionButtonRow({
  run,
  zh,
  busy,
  control,
  confirm,
  setConfirm,
  cancel,
  pause,
  resume,
}: RunActionButtonRowProps) {
  const disabled = busy || control.pending;
  return (
    <div className="row">
      <button
        type="button"
        className="btn sm"
        data-testid="run-pause"
        disabled={disabled || !canPauseRun(run.state)}
        title={pauseTitle(run, zh)}
        onClick={pause}
      >
        {zh ? "暂停" : "Pause"}
      </button>
      <button
        type="button"
        className="btn sm"
        data-testid="run-resume"
        disabled={disabled || !canResumeRun(run.state)}
        title={resumeTitle(run, zh)}
        onClick={resume}
      >
        {zh ? "恢复" : "Resume"}
      </button>
      <button
        type="button"
        className="btn sm"
        data-testid="run-cancel"
        disabled={disabled || !canRequestCancellation(run.state)}
        onClick={() => {
          setConfirm(true);
        }}
      >
        {zh ? "取消运行" : "Cancel run"}
      </button>
      {control.error !== null && <ErrorState message={control.error} />}
      <RunCancelConfirmDialog {...{ confirm, control, zh, run, setConfirm, cancel }} />
    </div>
  );
}

function pauseTitle(run: RunDetailDto, zh: boolean): string | undefined {
  if (!canPauseRun(run.state)) return undefined;
  return zh
    ? "控制面状态迁移 RUNNING→PAUSED；不证明已在执行的 worker 任务被物理暂停"
    : "Control-plane transition RUNNING→PAUSED; in-flight worker tasks may keep running";
}

function resumeTitle(run: RunDetailDto, zh: boolean): string | undefined {
  if (!canResumeRun(run.state)) return undefined;
  return zh
    ? "恢复需冻结 manifest 摘要一致（mismatch 拒绝）"
    : "Resume requires the frozen manifest digest to match (mismatch is rejected)";
}

interface CancelDialogProps {
  confirm: boolean;
  control: ControlPlane;
  zh: boolean;
  run: RunDetailDto;
  setConfirm: Dispatch<SetStateAction<boolean>>;
  cancel: () => Promise<void>;
}

function RunCancelConfirmDialog({
  confirm,
  control,
  zh,
  run,
  setConfirm,
  cancel,
}: CancelDialogProps) {
  return (
    <ConfirmDialog
      open={confirm}
      danger
      busy={control.pending}
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
