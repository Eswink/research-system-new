import { useState } from "react";

import { RunActions } from "./RunActions";
import { TimelineView } from "./TimelineView";
import { mergeEvents, useRunEventStream } from "./useRunEventStream";
import { useRunPanel } from "./useRunPanel";
import type { RunDetailDto, TaskDto } from "../../api/types";

const PROTOCOLS = [
  "console_demo_research_v1.yaml",
  "m12_reference_research_v1.yaml",
  "ai_ml_research_v0_4_0.yaml",
];

function ProtocolSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      Protocol
      <select
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      >
        {PROTOCOLS.map((protocol) => (
          <option key={protocol} value={protocol}>
            {protocol}
          </option>
        ))}
      </select>
    </label>
  );
}

function RunStatus({
  run,
  manifest,
  connected,
  runs,
  onChange,
}: {
  run: RunDetailDto;
  manifest: string;
  connected: boolean;
  runs: RunDetailDto[];
  onChange: (runId: string) => void;
}) {
  const selector =
    runs.length > 1 ? (
      <label>
        Recent runs
        <select
          value={run.id}
          onChange={(event) => {
            onChange(event.target.value);
          }}
        >
          {runs.map((item) => (
            <option key={item.id} value={item.id}>
              {item.state} · {item.id.slice(0, 8)}
            </option>
          ))}
        </select>
      </label>
    ) : null;
  return (
    <>
      <p data-testid="run-state">
        state: <strong>{run.state}</strong> · manifest: {manifest} ·{" "}
        <span data-testid="run-live-state">{connected ? "live" : "reconnecting"}</span>
      </p>
      {selector}
    </>
  );
}

function RunTaskList({ tasks }: { tasks: TaskDto[] }) {
  return (
    <div data-testid="run-tasks">
      <h3>Tasks</h3>
      <ul>
        {tasks.map((task) => (
          <li key={task.task_id}>
            {task.task_id.slice(0, 8)} · {task.contract_id} · {task.status} · attempt{" "}
            {String(task.attempt)}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Run 控制面板：启动 / 状态 / Timeline（JSON replay + SSE live）/ Tasks。
 * M13-R1 WP-M2/M4：刷新后自动恢复最近 run；SSE 实时增量、断线重连
 * 由 EventSource 原生 Last-Event-ID 续传 + 客户端 event_id 去重。
 * 执行体为受控 Fake Runtime（UI 如实披露，不冒充真实研究执行）。
 */
export function RunPanel() {
  const flow = useRunPanel();
  const [protocolPath, setProtocolPath] = useState(PROTOCOLS[0] ?? "");
  const stream = useRunEventStream(flow.run?.id ?? null);
  const events = mergeEvents(flow.events, stream.events);

  const submit = () => {
    void flow.start(protocolPath);
  };

  const cancel = () => {
    void flow.cancel();
  };

  const manifestLabel = flow.run?.manifest_digest?.slice(0, 16) ?? "not frozen";

  return (
    <section className="run-panel" data-testid="run-panel">
      <h2>Run Control</h2>
      <p className="note" data-testid="run-runtime-note">
        Agent 研究执行体为受控 Fake Runtime（非真实 LLM 推理）；真实研究执行
        走 M12 参考流程（Docker 实验 / live relay 为 opt-in 能力）。
      </p>
      <ProtocolSelect value={protocolPath} onChange={setProtocolPath} />
      <RunActions run={flow.run} busy={flow.busy} onStart={submit} onCancel={cancel} />
      {flow.error !== null && (
        <p className="error" role="alert">
          {flow.error}
        </p>
      )}
      {flow.run !== null && (
        <RunStatus
          run={flow.run}
          manifest={manifestLabel}
          connected={stream.connected}
          runs={flow.runs}
          onChange={(runId) => {
            void flow.loadRun(runId);
          }}
        />
      )}
      {events.length > 0 && <TimelineView events={events} />}
      {flow.tasks.length > 0 && <RunTaskList tasks={flow.tasks} />}
    </section>
  );
}
