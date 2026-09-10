/** 连接测试：显式选择本端点下的一个模型，POST /llm-endpoints/{id}/test。 */

import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type {
  EndpointTestResultDto,
  LlmEndpointReadDto,
  ModelReadDto,
} from "../../api/types";
import { Chip } from "../../components/Chip";
import { KeyValueList } from "../shared/KeyValueList";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import styles from "../shared/LivePage.module.css";

export function ConnectionTest({
  endpoint,
  zh,
}: {
  endpoint: LlmEndpointReadDto;
  zh: boolean;
}) {
  const models = useResource(`endpoint-models:${endpoint.id}`, () =>
    api.listModels(endpoint.id),
  );
  const [result, setResult] = useState<EndpointTestResultDto | null>(null);
  return (
    <div className={styles.page} data-testid="endpoint-connection-test">
      <div className={styles.cardTitle}>{zh ? "连接测试" : "Connection test"}</div>
      <p className={styles.notice}>
        {zh
          ? "向所选模型发送一次真实请求，可能产生费用；不改变运行状态。"
          : "Sends one real request to the selected model and may incur cost; run state is kept."}
      </p>
      {models.phase === "loading" && <LoadingState message={zh ? "加载模型…" : "Loading models…"} />}
      {models.phase === "error" && models.error !== null && <ErrorState message={models.error} />}
      {models.phase === "ready" && (models.data ?? []).length === 0 && (
        <EmptyState
          message={zh ? "该端点下还没有模型，无法测试" : "No models registered under this endpoint"}
        />
      )}
      {(models.data ?? []).length > 0 && (
        <TestLauncher
          endpointId={endpoint.id}
          models={models.data ?? []}
          zh={zh}
          onResult={setResult}
        />
      )}
      {result !== null && <TestResult result={result} zh={zh} />}
    </div>
  );
}

function TestLauncher({
  endpointId,
  models,
  zh,
  onResult,
}: {
  endpointId: string;
  models: ModelReadDto[];
  zh: boolean;
  onResult: (result: EndpointTestResultDto) => void;
}) {
  const [modelId, setModelId] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const chosen = modelId.length > 0 ? modelId : (models[0]?.id ?? "");
  const run = async (): Promise<void> => {
    setBusy(true);
    setIssue(null);
    try {
      onResult(await api.testEndpoint(endpointId, chosen));
    } catch (err) {
      setIssue(problemText(err, "test failed"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <div className={styles.toolbar}>
        <ModelSelect {...{ models, chosen, busy, setModelId, zh }} />
        <TestButton busy={busy} disabled={chosen.length === 0} onRun={run} zh={zh} />
      </div>
      {issue !== null && <ErrorState message={issue} />}
    </>
  );
}

function ModelSelect({
  models,
  chosen,
  busy,
  setModelId,
  zh,
}: {
  models: ModelReadDto[];
  chosen: string;
  busy: boolean;
  setModelId: (id: string) => void;
  zh: boolean;
}) {
  return (
    <select
      className="input mono"
      aria-label={zh ? "选择测试模型" : "Test model"}
      value={chosen}
      disabled={busy}
      onChange={(event) => {
        setModelId(event.target.value);
      }}
    >
      {models.map((model) => (
        <option key={model.id} value={model.id}>
          {model.display_name ?? model.model_name}
        </option>
      ))}
    </select>
  );
}

function TestButton({
  busy,
  disabled,
  onRun,
  zh,
}: {
  busy: boolean;
  disabled: boolean;
  onRun: () => Promise<void>;
  zh: boolean;
}) {
  return (
    <button
      className="btn sm"
      type="button"
      disabled={busy || disabled}
      onClick={() => {
        void onRun();
      }}
    >
      {busy ? (zh ? "测试中…" : "Testing…") : zh ? "发送测试请求" : "Send test"}
    </button>
  );
}

function TestResult({ result, zh }: { result: EndpointTestResultDto; zh: boolean }) {
  return (
    <div data-testid="endpoint-test-result">
      <Chip tone={result.ok ? "success" : "danger"}>{result.ok ? "OK" : "ERROR"}</Chip>
      <KeyValueList
        fields={[
          {
            label: zh ? "返回模型名" : "Returned model",
            value: result.returned_model_name ?? "—",
          },
          { label: zh ? "指纹" : "Fingerprint", value: result.system_fingerprint ?? "—" },
          { label: zh ? "错误类别" : "Error category", value: result.error_category ?? "—" },
          {
            label: zh ? "脱敏详情" : "Redacted detail",
            value: result.error_message_redacted ?? "—",
          },
          { label: zh ? "测试时间" : "Probed at", value: result.probed_at ?? "—" },
        ]}
      />
    </div>
  );
}
