import { useEffect, useState } from "react";

import { api } from "../../api/client";
import type {
  AgentSpecDto,
  ModelReadDto,
  PreflightReportDto,
  RoleDefinitionDto,
} from "../../api/types";

interface TeamState {
  agents: AgentSpecDto[];
  roles: RoleDefinitionDto[];
  models: ModelReadDto[];
  report: PreflightReportDto | null;
  busy: boolean;
  error: string | null;
}

function ModelBindingSelect({
  agent,
  models,
  busy,
  onSave,
}: {
  agent: AgentSpecDto;
  models: ModelReadDto[];
  busy: boolean;
  onSave: (modelId: string | null) => void;
}) {
  const current = agent.model_binding.value ?? "";
  const modelIds = new Set(models.map((model) => model.id));
  const isModelBinding = current === "" || modelIds.has(current);
  return (
    <span>
      {!isModelBinding && (
        <span data-testid="binding-display">
          current: {agent.model_binding.mode}:{current} ·{" "}
        </span>
      )}
      <select
        value={isModelBinding ? current : ""}
        disabled={busy}
        onChange={(event) => {
          onSave(event.target.value === "" ? null : event.target.value);
        }}
        aria-label={`model binding for ${agent.id}`}
      >
        <option value="">inherit</option>
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.model_name}
          </option>
        ))}
      </select>
    </span>
  );
}

function FindingList({ report }: { report: PreflightReportDto }) {
  if (report.findings.length === 0) {
    return <p data-testid="team-preflight-ok">preflight clear — no findings</p>;
  }
  return (
    <ul data-testid="team-preflight-findings">
      {report.findings.map((finding, index) => (
        <li key={`${finding.code}-${String(index)}`}>
          [{finding.severity}] {finding.message}
        </li>
      ))}
    </ul>
  );
}

function AgentList({
  agents,
  models,
  busy,
  onSave,
}: {
  agents: AgentSpecDto[];
  models: ModelReadDto[];
  busy: boolean;
  onSave: (agent: AgentSpecDto, modelId: string | null) => void;
}) {
  return (
    <ul>
      {agents.map((agent) => (
        <li key={agent.id} data-testid="agent-row">
          <strong>{agent.id}</strong> · {agent.role} ·{" "}
          <ModelBindingSelect
            agent={agent}
            models={models}
            busy={busy}
            onSave={(modelId) => {
              onSave(agent, modelId);
            }}
          />
        </li>
      ))}
    </ul>
  );
}

type TeamDispatch = (updater: (current: TeamState) => TeamState) => void;

const errorText = (err: unknown, fallback: string): string => {
  return err instanceof Error ? err.message : fallback;
};

async function loadTeam(dispatch: TeamDispatch) {
  try {
    const [agents, roles, models] = await Promise.all([
      api.listAgents(),
      api.listRoles(),
      api.listModels(),
    ]);
    dispatch((current) => ({ ...current, agents, roles, models, error: null }));
  } catch (err) {
    dispatch((current) => ({ ...current, error: errorText(err, "team load failed") }));
  }
}

async function refreshFindings(dispatch: TeamDispatch) {
  try {
    const report = await api.compileAndPreflight("console_demo_research_v1.yaml");
    dispatch((current) => ({ ...current, report, error: null }));
  } catch (err) {
    dispatch((current) => ({ ...current, error: errorText(err, "dry-run failed") }));
  }
}

async function saveBinding(agent: AgentSpecDto, modelId: string | null, dispatch: TeamDispatch) {
  dispatch((current) => ({ ...current, busy: true, error: null }));
  try {
    await api.updateAgent(
      agent.id,
      { model_binding: { mode: "EXPLICIT_MODEL", value: modelId } },
      agent.version,
    );
    await loadTeam(dispatch);
    await refreshFindings(dispatch);
  } catch (err) {
    dispatch((current) => ({ ...current, error: errorText(err, "save failed") }));
  } finally {
    dispatch((current) => ({ ...current, busy: false }));
  }
}

/**
 * Team / Agent 页面（WP-S2）：roles/templates + agents 列表，
 * per-Agent 模型绑定编辑（PATCH 持久化）；变更后触发 dry-run 展示后端
 * findings（AGENT_PERMISSION_DENIED / HETEROGENEITY / MODEL_ELIGIBILITY
 * 直接来自后端，客户端不做二次判定）。
 */
export function TeamPage() {
  const [state, setState] = useState<TeamState>({
    agents: [],
    roles: [],
    models: [],
    report: null,
    busy: false,
    error: null,
  });

  useEffect(() => {
    void loadTeam(setState);
  }, []);

  return (
    <section data-testid="team-page">
      <h2>Team &amp; Agent Assignment</h2>
      {state.error !== null && (
        <p className="error" role="alert">
          {state.error}
        </p>
      )}
      <p>Roles available: {state.roles.map((role) => role.id).join(", ")}</p>
      <h3>Agents</h3>
      <AgentList
        agents={state.agents}
        models={state.models}
        busy={state.busy}
        onSave={(agent, modelId) => {
          void saveBinding(agent, modelId, setState);
        }}
      />
      <h3>Preflight findings（保存后刷新，来自后端）</h3>
      {state.report !== null && <FindingList report={state.report} />}
    </section>
  );
}
