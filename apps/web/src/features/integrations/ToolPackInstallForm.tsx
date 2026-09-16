import { useState } from "react";

import { api } from "../../api/client";
import { ErrorState } from "../../components/States";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import styles from "../shared/LivePage.module.css";
import { installHint, parseManifest, submitStatusText } from "./toolPackCopy";

/** 安装/更新表单（PLAN-065）：提交完整 manifest 文档（含 digest），控制面会重算校验。 */
export function ToolPackInstallForm({ zh, onInstalled }: { zh: boolean; onInstalled: () => void }) {
  const form = useInstallSubmit(zh, onInstalled);
  return (
    <div className={styles.card} data-testid="toolpack-install-form">
      <div className={styles.cardHead}>
        <h3 className={styles.cardTitle}>{zh ? "安装 / 提交更新" : "Install / submit update"}</h3>
      </div>
      <p className={styles.notice}>{installHint(zh)}</p>
      <textarea
        className={styles.code}
        rows={8}
        value={form.document}
        aria-label={zh ? "ToolPack manifest（JSON）" : "ToolPack manifest (JSON)"}
        data-testid="toolpack-manifest-input"
        onChange={(event) => {
          form.setDocument(event.target.value);
        }}
      />
      <div className={styles.cardHead}>
        <button
          className="btn sm"
          type="button"
          data-testid="toolpack-install-submit"
          disabled={form.busy || form.document.trim() === ""}
          onClick={form.submit}
        >
          {zh ? "提交" : "Submit"}
        </button>
      </div>
      <InstallFeedback
        localError={form.localError}
        serverError={form.serverError}
        result={form.result}
      />
    </div>
  );
}

/** 表单状态机：本地 JSON 解析 → 提交 → 结果口径（服务端 4xx detail 原样保留）。 */
function useInstallSubmit(zh: boolean, onInstalled: () => void) {
  const [document, setDocument] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const action = useAsyncAction(onInstalled);
  const submit = (): void => {
    const parsed = parseManifest(document, zh);
    if (typeof parsed === "string") {
      setLocalError(parsed);
      return;
    }
    setLocalError(null);
    setResult(null);
    action.run(async () => {
      setResult(submitStatusText(await api.installToolPack(parsed), zh));
    });
  };
  return {
    document,
    setDocument,
    localError,
    serverError: action.error,
    busy: action.busy,
    result,
    submit,
  };
}

/** 表单反馈：本地 JSON 错误、服务端 4xx detail、提交结果**都落在面板内**。 */
function InstallFeedback({
  localError,
  serverError,
  result,
}: {
  localError: string | null;
  serverError: string | null;
  result: string | null;
}) {
  return (
    <>
      {localError !== null && (
        <div data-testid="toolpack-install-local-error">
          <ErrorState message={localError} />
        </div>
      )}
      {serverError !== null && (
        <div data-testid="toolpack-install-error">
          <ErrorState message={serverError} />
        </div>
      )}
      {result !== null && (
        <p className={styles.notice} data-testid="toolpack-install-result">
          {result}
        </p>
      )}
    </>
  );
}
