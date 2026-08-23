"""M12 Reference Workflow CLI（M12-R1 WP8/WP10）。

一键 clean-run：python tools/m12_reference_workflow.py [--clean] [--live-relay]

--clean       从空状态重建（默认；不依赖开发者手工 populated DB/先前产物）
--live-relay  执行真实 LLM relay probe（需要 llm_main_key 环境变量；缺凭据时
              manifest 落 NOT VERIFIED 占位，不 Fake PASS）

输出：run_id / manifest digest / experiment ids / artifact digests /
evidence/claim ids / eval run id / budget summary / deliverable digest。
不泄漏 credentials（只输出 digest/status/model 名）。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.contracts.models_loaders import load_llm_endpoints, load_models
from adapters.contracts.protocol_loaders import load_protocol
from adapters.contracts.resource_loaders import (
    load_budget_policies,
    load_policy,
    load_project,
    load_tool_providers,
    load_workspaces,
)
from adapters.contracts.roles_loaders import (
    load_agents,
    load_roles,
    load_team_templates,
)
from adapters.contracts.tasks_loaders import load_task_contracts
from adapters.execution import DockerExecutionBackend
from adapters.fakes import FakeBudgetLedger
from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.gateway import OpenAIChatGateway
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.memory_store import SqliteMemoryStore
from adapters.workspace import FileWorkspaceBackend
from packages.application.m12_reference.clean_run import run_clean_workflow
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.domain.core import ID
from packages.domain.enums import EndpointHealth
from packages.domain.workspace import Workspace

PROTOCOL_PATH = "examples/protocols/m12_reference_research_v1.yaml"
EXPERIMENT_PATH = "examples/experiments/m12_reference_classification.py"
ROLES_PATH = "examples/config/roles.yaml"
AGENTS_PATH = "examples/config/agents.yaml"
TEAMS_PATH = "examples/config/team_templates.yaml"
TASKS_PATH = "examples/contracts/task_contracts.yaml"
BUDGETS_PATH = "examples/config/budgets.yaml"
POLICY_PATH = "examples/config/policy.yaml"
WORKSPACES_PATH = "examples/config/backends.yaml"
TOOLS_PATH = "examples/config/tool_providers.yaml"
PROJECT_PATH = "examples/config/project.yaml"
IMAGE_TAG = "research-os-sandbox:m9-test"
RUN_ID = "12121212-2222-4333-8444-555555555555"
PLAN_ID = ID("5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a")


def _catalog_and_project() -> tuple[CatalogSnapshot, ProjectSettings]:
    catalog = CatalogSnapshot(
        roles=load_roles(ROLES_PATH),
        agents=load_agents(AGENTS_PATH),
        team_templates=load_team_templates(TEAMS_PATH),
        task_contracts=load_task_contracts(TASKS_PATH),
        budget_policies=load_budget_policies(BUDGETS_PATH),
        workspaces=load_workspaces(WORKSPACES_PATH),
        tool_providers=load_tool_providers(TOOLS_PATH),
        policy=load_policy(POLICY_PATH),
    )
    raw_project = load_project(PROJECT_PATH)
    project = ProjectSettings.from_mapping("project-m12", raw_project)
    return catalog, project


def main() -> int:
    parser = argparse.ArgumentParser(description="M12 Reference Workflow clean-run")
    parser.add_argument("--clean", action="store_true", help="run from empty state (default)")
    parser.add_argument("--live-relay", action="store_true", help="run real LLM probe")
    args = parser.parse_args()

    protocol = load_protocol(PROTOCOL_PATH)
    catalog, project = _catalog_and_project()
    context = PreflightContext(
        catalog=catalog,
        project=project,
        credentials=EnvCredentialResolver(),
        endpoint_health={
            endpoint_id: EndpointHealth.HEALTHY for endpoint_id in catalog.endpoints
        },
    )

    tmp = tempfile.mkdtemp(prefix="m12-clean-run-")
    db_path = Path(tmp) / "state.sqlite"
    connection = sqlite3.connect(str(db_path))
    workspaces = FileWorkspaceBackend(Path(tmp) / "workspaces")
    workspace = Workspace(id=project.workspace_backend, name=project.workspace_backend)
    workspaces.create_workspace(workspace)
    artifacts = SqliteArtifactStore(blob_dir=Path(tmp) / "blobs")
    ledger = SqliteEvidenceLedger(connection)
    memory = SqliteMemoryStore(connection)
    budget = FakeBudgetLedger()

    deps = CleanRunDeps(
        protocol=protocol,
        catalog=catalog,
        project=project,
        context=context,
        execution=DockerExecutionBackend(image=IMAGE_TAG),
        workspaces=workspaces,
        workspace=workspace,
        artifacts=artifacts,
        ledger=ledger,
        memory=memory,
        budget=budget,
        run_id=RUN_ID,
    )
    if args.live_relay:
        endpoints = load_llm_endpoints("examples/config/llm_endpoints.yaml")
        models = load_models("examples/config/models.yaml")
        deps = CleanRunDeps(
            protocol=protocol,
            catalog=catalog,
            project=project,
            context=context,
            execution=DockerExecutionBackend(image=IMAGE_TAG),
            workspaces=workspaces,
            workspace=workspace,
            artifacts=artifacts,
            ledger=ledger,
            memory=memory,
            budget=budget,
            model_gateway=OpenAIChatGateway(),
            credentials=EnvCredentialResolver(),
            endpoint=endpoints["main"],
            model=models["research_alpha"],
            run_id=RUN_ID,
        )
    result = run_clean_workflow(
        deps,
        experiment_plan_id=PLAN_ID,
        experiment_command=f"python {EXPERIMENT_PATH}",
    )
    print(json.dumps(result.to_payload(), ensure_ascii=False, indent=2, sort_keys=True))
    print(f"state: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())