/** 编辑器状态条（拆分自主组件）：保存状态 + 预检状态 + 启动门禁。 */

import styles from "./EditorShell.module.css";
import { canStart, type EditorState } from "./editorState";

export function EditorStatusBar(props: {
  state: EditorState;
  dirty: boolean;
  stale: boolean;
  canPreflight: boolean;
  canCompile: boolean;
  canRecheck: boolean;
  ackWarnings: boolean;
  onAckWarnings: (next: boolean) => void;
  onSave: () => void;
  onDiscard: () => void;
  onStart: () => void;
  onPreflight: () => void;
  onCompile: () => void;
  onRecheck: () => void;
}): React.JSX.Element {
  const report = props.state.preflight?.report ?? null;
  const warnCount = countWarnings(report?.findings);
  const startable =
    canStart(props.state) && !props.stale && (report?.status !== "WARN" || props.ackWarnings);
  const needsAck = report !== null && report.status === "WARN" && !props.ackWarnings;
  return (
    <div className={styles.statusBar} data-testid="editor-status-bar">
      <StatusBadges state={props.state} dirty={props.dirty} stale={props.stale} />
      {needsAck && (
        <AckLabel
          ackWarnings={props.ackWarnings}
          warnCount={warnCount}
          onChange={props.onAckWarnings}
        />
      )}
      <span className={styles.statusSpacer} />
      <ActionBarButtons {...{ ...props, startable }} />
    </div>
  );
}

function StatusBadges(props: {
  state: EditorState;
  dirty: boolean;
  stale: boolean;
}): React.JSX.Element {
  const report = props.state.preflight?.report ?? null;
  return (
    <>
      <span className={styles.statusText} data-testid="editor-save-status">
        {saveStatusText(props.state.saveStatus, props.dirty, props.state.saved !== null)}
      </span>
      {report !== null && (
        <span className={styles.statusText} data-testid="editor-preflight-status">
          {report.status}
          {props.stale ? " (stale)" : ""}
        </span>
      )}
    </>
  );
}

function AckLabel(props: {
  ackWarnings: boolean;
  warnCount: number;
  onChange: (next: boolean) => void;
}): React.JSX.Element {
  return (
    <label className={styles.ackLabel}>
      <input
        type="checkbox"
        checked={props.ackWarnings}
        onChange={(event) => {
          props.onChange(event.target.checked);
        }}
      />
      ack {props.warnCount}
    </label>
  );
}

function ActionBarButtons(props: {
  state: EditorState;
  dirty: boolean;
  canPreflight: boolean;
  canCompile: boolean;
  canRecheck: boolean;
  startable: boolean;
  onDiscard: () => void;
  onSave: () => void;
  onPreflight: () => void;
  onCompile: () => void;
  onRecheck: () => void;
  onStart: () => void;
}): React.JSX.Element {
  return (
    <>
      <DraftSaveButtons {...props} />
      <VerificationButtons {...props} />
    </>
  );
}
function DraftSaveButtons(props: {
  state: EditorState;
  dirty: boolean;
  onDiscard: () => void;
  onSave: () => void;
}): React.JSX.Element {
  return (
    <>
      <button
        type="button"
        className="btn sm"
        disabled={!props.dirty || props.state.busy}
        onClick={props.onDiscard}
      >
        Discard
      </button>
      <button
        type="button"
        className="btn sm"
        disabled={props.state.busy || props.state.saveStatus === "saving" || !props.dirty}
        onClick={props.onSave}
      >
        Save
      </button>
    </>
  );
}

function VerificationButtons(props: {
  state: EditorState;
  canPreflight: boolean;
  canRecheck: boolean;
  canCompile: boolean;
  startable: boolean;
  onPreflight: () => void;
  onCompile: () => void;
  onRecheck: () => void;
  onStart: () => void;
}): React.JSX.Element {
  return (
    <>
      <button
        type="button"
        className="btn sm"
        disabled={!props.canCompile}
        onClick={props.onCompile}
        data-testid="editor-compile"
      >
        Compile
      </button>
      <button
        type="button"
        className="btn sm"
        onClick={props.onPreflight}
        disabled={!props.canPreflight}
        data-testid="editor-preflight"
      >
        Preflight
      </button>
      <button
        type="button"
        className="btn sm"
        disabled={!props.canRecheck}
        onClick={props.onRecheck}
        data-testid="editor-recheck"
      >
        Recheck
      </button>
      <StartRunButton startable={props.startable} onStart={props.onStart} />
    </>
  );
}

function StartRunButton({ startable, onStart }: { startable: boolean; onStart: () => void }) {
  return (
    <button
      type="button"
      className="btn sm primary"
      disabled={!startable}
      data-testid="editor-start"
      onClick={onStart}
    >
      Start
    </button>
  );
}

function countWarnings(findings: { severity: string }[] | undefined): number {
  if (findings === undefined) {
    return 0;
  }
  return findings.filter((finding) => finding.severity === "WARNING").length;
}

function saveStatusText(status: EditorState["saveStatus"], dirty: boolean, saved: boolean): string {
  if (status === "saving") return "saving…";
  if (status === "conflict") {
    return "conflict";
  }
  if (status === "invalid") {
    return "invalid";
  }
  if (dirty) {
    return "unsaved";
  }
  return saved ? "saved" : "empty";
}
