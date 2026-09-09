import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type {
  AgentSpecDto,
  ModelReadDto,
  PreflightReportDto,
  RoleDefinitionDto,
  TeamTemplateDto,
} from "../../api/types";
import { Drawer } from "../../components/Drawer";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { useCommand } from "../../hooks/useCommand";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { AgentBindingEditor } from "./AgentBindingEditor";
import { AgentCards } from "./TeamAgentCards";
import { RoleDefinitions, TeamTemplates } from "./TeamDefinitions";
import { TEAM_REFERENCE_PROTOCOL, TeamPreflight } from "./TeamPreflight";

export function TeamPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  const agents = useResource("team-agents", () => api.listAgents());
  const models = useResource("team-models", () => api.listModels());
  const roles = useResource("team-roles", () => api.listRoles());
  const templates = useResource("team-templates", () => api.listTeamTemplates());
  const preflight = useCommand((path: string) => api.compileAndPreflight(path));
  const checkReference = () => {
    void preflight.run(TEAM_REFERENCE_PROTOCOL);
  };
  const afterSave = () => {
    agents.reload();
    checkReference();
  };
  const refresh = () => {
    agents.reload();
    models.reload();
    roles.reload();
    templates.reload();
  };
  return (
    <TeamPagesection
      {...{ zh, refresh, agents, models, afterSave, roles, templates, preflight, checkReference }}
    />
  );
}

interface TeamPagesectionProps {
  zh: boolean;
  refresh: () => void;
  agents: ResourceState<AgentSpecDto[]>;
  models: ResourceState<ModelReadDto[]>;
  afterSave: () => void;
  roles: ResourceState<RoleDefinitionDto[]>;
  templates: ResourceState<TeamTemplateDto[]>;
  preflight: {
    run: (argument: string) => Promise<void>;
    pending: boolean;
    result: PreflightReportDto | null;
    error: string | null;
  };
  checkReference: () => void;
}

function TeamPagesection({
  zh,
  refresh,
  agents,
  models,
  afterSave,
  roles,
  templates,
  preflight,
  checkReference,
}: TeamPagesectionProps) {
  return (
    <section className={styles.page} data-testid="team-page">
      <TeamPagePageHeader {...{ zh, refresh }} />
      <ResourceBoundary state={agents}>
        {agents.data !== null && (
          <AgentCatalog
            agents={agents.data}
            models={models.phase === "ready" ? models.data : null}
            onSaved={afterSave}
          />
        )}
      </ResourceBoundary>
      <ResourceBoundary state={models}>{null}</ResourceBoundary>
      <div className={styles.split}>
        <ResourceBoundary state={roles}>
          {roles.data !== null && <RoleDefinitions roles={roles.data} />}
        </ResourceBoundary>
        <ResourceBoundary state={templates}>
          {templates.data !== null && <TeamTemplates templates={templates.data} />}
        </ResourceBoundary>
      </div>
      <TeamPreflight
        report={preflight.result}
        error={preflight.error}
        pending={preflight.pending}
        onCheck={checkReference}
      />
      <TeamWorkflowFooter zh={zh} />
    </section>
  );
}

function TeamWorkflowFooter({ zh }: { zh: boolean }) {
  return (
    <>
      <p className={styles.notice}>
        {zh
          ? "保存绑定不会重写冻结 Manifest，也不代表预检通过。后续运行请在协议编辑器重新编译和预检。"
          : [
              "Saving bindings does not rewrite frozen manifests or imply preflight ",
              "success. Compile and preflight again in the protocol editor.",
            ].join("")}
      </p>
      <a href="#/plan/protocol" className="btn">
        {zh ? "进入协议与预检" : "Open protocol and preflight"} →
      </a>
    </>
  );
}

interface TeamPagePageHeaderProps {
  zh: boolean;
  refresh: () => void;
}

function TeamPagePageHeader({ zh, refresh }: TeamPagePageHeaderProps) {
  return (
    <PageHeader
      title={zh ? "研究团队与 Agent" : "Research team and agents"}
      kicker="PLAN / TEAM"
      description={
        zh
          ? "职责、配置实例与模型绑定分开管理；所有状态来自实际项目接口。"
          : [
              "Responsibilities, agent instances and model bindings remain distinct, ",
              "using actual project APIs.",
            ].join("")
      }
      actions={
        <button type="button" className="btn" onClick={refresh}>
          {zh ? "刷新配置" : "Refresh configuration"}
        </button>
      }
    />
  );
}

function AgentCatalog({
  agents,
  models,
  onSaved,
}: {
  agents: AgentSpecDto[];
  models: ModelReadDto[] | null;
  onSaved: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [editingId, setEditingId] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const editing = agents.find((agent) => agent.id === editingId);
  const filtered = agents.filter((agent) =>
    `${agent.id} ${agent.role}`.toLocaleLowerCase().includes(filter.trim().toLocaleLowerCase()),
  );
  const acknowledge = () => {
    setSavedId(editingId);
    setEditingId(null);
    onSaved();
  };
  return (
    <TeamPageContent
      {...{
        zh,
        agents,
        filter,
        setFilter,
        filtered,
        setEditingId,
        savedId,
        editing,
        models,
        acknowledge,
      }}
    />
  );
}

interface TeamPageContentProps {
  zh: boolean;
  agents: AgentSpecDto[];
  filter: string;
  setFilter: Dispatch<SetStateAction<string>>;
  filtered: AgentSpecDto[];
  setEditingId: Dispatch<SetStateAction<string | null>>;
  savedId: string | null;
  editing: AgentSpecDto | undefined;
  models: ModelReadDto[] | null;
  acknowledge: () => void;
}

function TeamPageContent({
  zh,
  agents,
  filter,
  setFilter,
  filtered,
  setEditingId,
  savedId,
  editing,
  models,
  acknowledge,
}: TeamPageContentProps) {
  return (
    <>
      <TeamPagePanelSection {...{ zh, agents, filter, setFilter, filtered, setEditingId }} />
      {savedId !== null && (
        <p role="status" className={styles.notice}>
          {savedId} ·
          {zh
            ? "后端已确认保存配置；预检状态尚未确定。"
            : "Backend confirmed configuration saved; preflight remains undetermined."}
        </p>
      )}
      <Drawer
        open={editing !== undefined}
        onClose={() => {
          setEditingId(null);
        }}
        title={zh ? "编辑模型绑定" : "Edit model binding"}
      >
        {editing !== undefined && (
          <AgentBindingEditor
            key={`${editing.id}:${editing.version}`}
            agent={editing}
            models={models}
            onSaved={acknowledge}
          />
        )}
      </Drawer>
    </>
  );
}

interface TeamPagePanelSectionProps {
  zh: boolean;
  agents: AgentSpecDto[];
  filter: string;
  setFilter: Dispatch<SetStateAction<string>>;
  filtered: AgentSpecDto[];
  setEditingId: Dispatch<SetStateAction<string | null>>;
}

function TeamPagePanelSection({
  zh,
  agents,
  filter,
  setFilter,
  filtered,
  setEditingId,
}: TeamPagePanelSectionProps) {
  return (
    <PanelSection
      title={zh ? "Agent 配置实例" : "Configured agent instances"}
      count={agents.length}
      extra={
        <input
          type="search"
          className="input"
          value={filter}
          aria-label={zh ? "筛选 Agent" : "Filter agents"}
          placeholder={zh ? "按 ID 或职责筛选" : "Filter ID or role"}
          onChange={(event) => {
            setFilter(event.target.value);
          }}
        />
      }
    >
      <AgentCards agents={filtered} onEdit={setEditingId} />
    </PanelSection>
  );
}
