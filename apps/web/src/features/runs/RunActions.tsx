import type { RunDetailDto } from "../../api/types";

const TERMINAL_STATES = new Set(["SUCCEEDED", "FAILED", "CANCELLED"]);

/**
 * Run 动作（M13-R1 WP-P3）：
 * - 终态 run 不再可点击 Cancel（后端已守卫 409，前端不再提供误导按钮）；
 * - Cancel 破坏性操作需二次确认（window.confirm）。
 */
export function RunActions({
  run,
  busy,
  onStart,
  onCancel,
}: {
  run: RunDetailDto | null;
  busy: boolean;
  onStart: () => void;
  onCancel: () => void;
}) {
  const requestCancel = () => {
    if (run === null) {
      return;
    }
    if (
      window.confirm(
        `Cancel run ${run.id.slice(0, 8)}? This may be irreversible for running work.`,
      )
    ) {
      onCancel();
    }
  };

  const cancellable = run !== null && !TERMINAL_STATES.has(run.state);
  return (
    <>
      <button
        type="button"
        onClick={onStart}
        disabled={busy || run !== null}
        data-testid="run-start"
      >
        {busy ? "Starting…" : "Start Research Run"}
      </button>
      {cancellable && (
        <button
          type="button"
          onClick={requestCancel}
          disabled={busy}
          data-testid="run-cancel"
        >
          {busy ? "Working…" : "Cancel"}
        </button>
      )}
    </>
  );
}
