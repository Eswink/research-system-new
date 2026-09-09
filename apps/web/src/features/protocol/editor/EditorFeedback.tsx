import { Chip } from "../../../components/Chip";
import { PanelSection } from "../../../components/PanelSection";
import { ErrorState, LoadingState } from "../../../components/States";
import { useI18n } from "../../../i18n/useI18n";
import styles from "../../shared/LivePage.module.css";
import type { EditorState } from "./editorState";

export function EditorFeedback({ state }: { state: EditorState }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div className={styles.page} data-testid="editor-feedback">
      {state.busy && (
        <LoadingState message={zh ? "正在等待后端响应…" : "Waiting for backend response…"} />
      )}
      {state.error !== null && <ErrorState message={state.error} />}
      {state.validation !== null && <ValidationResult state={state} />}
      {state.preflight !== null && <PreflightResult state={state} />}
      {state.startedRunId !== null && (
        <p role="status" className={styles.notice}>
          {zh ? "后端已创建运行：" : "Backend created run: "}
          <a href={`#/run/timeline?run=${encodeURIComponent(state.startedRunId)}`}>
            {state.startedRunId} →
          </a>
        </p>
      )}
    </div>
  );
}

function ValidationResult({ state }: { state: EditorState }) {
  const { language } = useI18n();
  const validation = state.validation;
  if (validation === null) return null;
  const stale = validation.text !== state.working;
  return (
    <PanelSection
      title={
        language === "zh" ? "服务端 Schema 校验（未保存）" : "Server schema validation (not saved)"
      }
      extra={
        <Chip tone={stale ? "warn" : validation.result.ok ? "success" : "danger"}>
          {stale ? "STALE" : validation.result.ok ? "VALID" : "INVALID"}
        </Chip>
      }
    >
      <p className="mono">
        {validation.result.protocol_id ?? "UNKNOWN"} · {validation.result.phase_count} phases
      </p>
      <ul className={styles.list}>
        {validation.result.issues.map((issue, index) => (
          <li key={index} className={styles.notice}>
            {issue.path} · {issue.code} · {issue.message}
          </li>
        ))}
      </ul>
    </PanelSection>
  );
}

function PreflightResult({ state }: { state: EditorState }) {
  const { language } = useI18n();
  const preflight = state.preflight;
  if (preflight === null) return null;
  return (
    <PanelSection
      title={language === "zh" ? "受控模板预检报告" : "Controlled-template preflight report"}
      extra={
        <Chip tone={state.preflightStale ? "warn" : "neutral"}>
          {preflight.report.status}
          {state.preflightStale ? " · STALE" : ""}
        </Chip>
      }
    >
      <ul className={styles.list}>
        {preflight.report.findings.map((finding, index) => (
          <li key={index} className={styles.notice}>
            {finding.severity} · {finding.code} · {finding.message}
          </li>
        ))}
      </ul>
      <p className={styles.notice}>
        {language === "zh"
          ? "预检与 Dry-run 返回的是静态检查，不表示运行已经执行。"
          : "Preflight and dry-run are static checks, not executed research runs."}
      </p>
    </PanelSection>
  );
}
