/** 编辑器状态条（拆分自主组件）：保存状态 + 预检状态 + 启动门禁。 */

import { canStart, type EditorState } from "./editorState";
import styles from "./EditorShell.module.css";

export function EditorStatusBar(props: {
  state: EditorState;
  dirty: boolean;
  stale: boolean;
  ackWarnings: boolean;
  onAckWarnings: (next: boolean) => void;
  onSave: () => void;
  onDiscard: () => void;
  onStart: () => void;
  onPreflight: () => void;
}): React.JSX.Element {
  const report = props.state.preflight?.report ?? null;
  const warnCount = countWarnings(report?.findings);
  const startable = canStart(props.state) && (!props.stale || props.ackWarnings);
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
      <ActionBarButtons
        state={props.state}
        dirty={props.dirty}
        startable={startable}
        onDiscard={props.onDiscard}
        onSave={props.onSave}
        onPreflight={props.onPreflight}
        onStart={props.onStart}
      />
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
  startable: boolean;
  onDiscard: () => void;
  onSave: () => void;
  onPreflight: () => void;
  onStart: () => void;
}): React.JSX.Element {
  return (
    <>
      <button type="button" className="btn sm" disabled={!props.dirty} onClick={props.onDiscard}>
        Discard
      </button>
      <button
        type="button"
        className="btn sm"
        disabled={props.state.saveStatus === "saving" || !props.dirty}
        onClick={props.onSave}
      >
        Save
      </button>
      <button type="button" className="btn sm" onClick={props.onPreflight}>
        Preflight
      </button>
      <button
        type="button"
        className="btn sm primary"
        disabled={!props.startable}
        data-testid="editor-start"
        onClick={props.onStart}
      >
        Start
      </button>
    </>
  );
}

function countWarnings(findings: { severity: string }[] | undefined): number {
  if (findings === undefined) {
    return 0;
  }
  return findings.filter((finding) => finding.severity === "WARNING").length;
}

function saveStatusText(status: EditorState["saveStatus"], dirty: boolean, saved: boolean): string {
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
