"""Durable personal-production Reference Research Workflow.

This entrypoint composes only PostgreSQL-backed canonical stores and the
RemoteExecutionBackend. A separately running worker gateway and real Docker/GPU
worker execute the experiment. The completed Run, Manifest artifact,
Experiment entities, Artifact/Evidence/Claim, EvalReport, Usage, Memory, and
Deliverable artifact remain restorable after this process exits.
"""

# The documented entrypoint is executed by file path from the repository root;
# bootstrap the repository import root before importing project packages.
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

import docker
import yaml

from adapters.contracts.models_loaders import (
    load_llm_endpoints,
    load_model_profiles,
    load_models,
)
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
    load_skills,
    load_team_templates,
)
from adapters.contracts.tasks_loaders import load_task_contracts
from adapters.execution.gpu_probe import GPU_SANDBOX_IMAGE_DEFAULT
from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.postgres.artifact_store import PostgresArtifactStore
from adapters.postgres.budget_ledger import PostgresBudgetLedger
from adapters.postgres.db import migrate
from adapters.postgres.eval_report_store import PostgresEvalReportStore
from adapters.postgres.evidence_ledger import PostgresEvidenceLedger
from adapters.postgres.execution_job_queue import PostgresExecutionJobQueue
from adapters.postgres.experiment_store import PostgresExperimentStore
from adapters.postgres.memory_store import PostgresMemoryStore
from adapters.postgres.run_store import PostgresRunStore
from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.gateway import OpenAIChatGateway
from adapters.workspace.file_backend import FileWorkspaceBackend
from packages.application.m12_reference.clean_run import run_clean_workflow
from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.application.ports.eval_report_store import EvalReportStore
from packages.application.ports.experiment_store import ExperimentStore
from packages.application.ports.run_store import RunStore
from packages.domain.core import ID
from packages.domain.enums import EndpointHealth, MemoryType
from packages.domain.workspace import Workspace

_PROTOCOL_PATH = "examples/protocols/m17_gpu_research_v1.yaml"
_EXPERIMENT_PATH = "examples/experiments/m17_gpu_research.py"
_PLAN_ID = ID("5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a")
_DEFAULT_GPU_IMAGE = GPU_SANDBOX_IMAGE_DEFAULT


@dataclass(frozen=True, slots=True)
class _Persistence:
    run_store: RunStore
    experiment_store: ExperimentStore
    eval_report_store: EvalReportStore


@dataclass(slots=True)
class _Resources:
    deps: CleanRunDeps
    closables: tuple[Any, ...]

    def close(self) -> None:
        for resource in reversed(self.closables):
            close = getattr(resource, "close", None)
            if callable(close):
                close()


@dataclass(frozen=True, slots=True)
class _Canonical:
    artifacts: PostgresArtifactStore
    ledger: PostgresEvidenceLedger
    budget: PostgresBudgetLedger
    memory: PostgresMemoryStore
    jobs: PostgresExecutionJobQueue
    remote: RemoteExecutionBackend
    persistence: _Persistence

    def closables(self) -> tuple[Any, ...]:
        return (
            self.persistence.eval_report_store,
            self.persistence.experiment_store,
            self.persistence.run_store,
            self.remote,
            self.jobs,
            self.memory,
            self.budget,
            self.ledger,
            self.artifacts,
        )


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _tool_pack_digests() -> dict[str, str]:
    path = Path("examples/contracts/toolpack_ncbi_eutils.yaml")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("digest"), str):
        return {}
    return {"ncbi_eutils": str(payload["digest"])}


def _catalog() -> CatalogSnapshot:
    providers = load_tool_providers("examples/config/tool_providers.yaml")
    active_providers = {key: value for key, value in providers.items() if key != "research_mcp"}
    return CatalogSnapshot(
        roles=load_roles("examples/config/roles.yaml"),
        agents=load_agents("examples/config/agents.yaml"),
        team_templates=load_team_templates("examples/config/team_templates.yaml"),
        task_contracts=load_task_contracts("examples/contracts/task_contracts.yaml"),
        budget_policies=load_budget_policies("examples/config/budgets.yaml"),
        workspaces=load_workspaces("examples/config/backends.yaml"),
        tool_providers=active_providers,
        models=load_models("examples/config/models.yaml"),
        model_profiles=load_model_profiles("examples/config/model_profiles.yaml"),
        endpoints=load_llm_endpoints("examples/config/llm_endpoints.yaml"),
        skills=load_skills("examples/config/skills.yaml"),
        tool_pack_digests=_tool_pack_digests(),
        policy=load_policy("examples/config/policy.yaml"),
    )


def _project() -> ProjectSettings:
    return ProjectSettings.from_mapping(
        "project-personal-reference",
        load_project("examples/config/project.yaml"),
    )


def _context(catalog: CatalogSnapshot, project: ProjectSettings) -> PreflightContext:
    if catalog.policy is None:
        raise RuntimeError("reference catalog requires a policy")
    return PreflightContext(
        catalog=catalog,
        project=project,
        credentials=EnvCredentialResolver(),
        endpoint_health={key: EndpointHealth.HEALTHY for key in catalog.endpoints},
        policy_evaluator=NativePolicyEvaluator(catalog.policy),
    )


def _open_canonical(run_id: str) -> _Canonical:
    dsn = _required_env("RESEARCHOS_POSTGRES_DSN")
    migrate(dsn)
    blob_root = Path(
        os.environ.get("RESEARCHOS_ARTIFACT_BLOB_DIR", "data/artifacts-blobs")
    ).resolve()
    artifacts = PostgresArtifactStore(dsn=dsn, blob_dir=blob_root)
    ledger = PostgresEvidenceLedger(dsn=dsn)
    budget = PostgresBudgetLedger(dsn=dsn)
    experiment_id = experiment_run_id_of(run_id)
    memory = PostgresMemoryStore(
        dsn=dsn,
        allowed_sources=tuple(
            f"{experiment_id}:{name}"
            for name in ("experiment_result.json", "stdout.log", "stderr.log")
        ),
    )
    jobs = PostgresExecutionJobQueue(dsn=dsn)
    remote = RemoteExecutionBackend.for_run(run_id, job_queue=jobs, artifacts=artifacts)
    run_store = PostgresRunStore(dsn=dsn)
    experiment_store = PostgresExperimentStore(dsn=dsn)
    eval_store = PostgresEvalReportStore(dsn=dsn)
    return _Canonical(
        artifacts,
        ledger,
        budget,
        memory,
        jobs,
        remote,
        _Persistence(run_store, experiment_store, eval_store),
    )


def _build_resources(
    run_id: str, live_relay: bool, expected_image_digest: str | None = None
) -> _Resources:
    stores = _open_canonical(run_id)
    workspaces = FileWorkspaceBackend(Path("data/reference-workspaces") / uuid4().hex)
    workspace = Workspace(id=f"reference-{run_id}", name="personal-reference")
    workspaces.create_workspace(workspace)
    catalog = _catalog()
    project = _project()
    gateway = OpenAIChatGateway() if live_relay else None
    credentials = EnvCredentialResolver() if live_relay else None
    endpoint = catalog.endpoints["main"] if live_relay else None
    model = catalog.models["research_alpha"] if live_relay else None
    deps = CleanRunDeps(
        protocol=load_protocol(_PROTOCOL_PATH),
        catalog=catalog,
        project=project,
        context=_context(catalog, project),
        execution=stores.remote,
        workspaces=workspaces,
        workspace=workspace,
        artifacts=stores.artifacts,
        ledger=stores.ledger,
        memory=stores.memory,
        budget=stores.budget,
        persistence=stores.persistence,
        expected_image_digest=expected_image_digest,
        model_gateway=gateway,
        credentials=credentials,
        endpoint=endpoint,
        model=model,
        run_id=run_id,
    )
    return _Resources(deps=_configure_m17(deps), closables=(workspaces, *stores.closables()))


def _configure_m17(deps: CleanRunDeps) -> CleanRunDeps:
    return replace(
        deps,
        experiment_script=_EXPERIMENT_PATH,
        resource_profile="gpu-small",
        hypothesis="mixed precision preserves accuracy under a fixed GPU training budget",
        objective="Compare FP32 and mixed-precision classification on the fixed M17 GPU workload",
        plan_name="m17-personal-gpu-reference",
        dataset_path="examples/eval/datasets/m17_gpu_v1.yaml",
        claim_statement=(
            "mixed precision preserves classification accuracy relative to FP32 "
            "under the fixed GPU training budget"
        ),
        memory_content=(
            "mixed precision accuracy met the evaluated FP32-relative threshold; "
            "throughput remains an observed metric"
        ),
        memory_kind=MemoryType.FACT,
    )


def _expected_image_id(image: str) -> str:
    client = docker.from_env()
    try:
        return str(client.images.get(image).id)
    finally:
        client.close()


def _verify_runtime_image(deps: CleanRunDeps, run_id: str, image: str) -> str:
    content = deps.artifacts.get(f"{run_id}:run_manifest.json")
    manifest = json.loads(content.decode("utf-8"))
    actual = str(manifest.get("image_digest") or "")
    expected = _expected_image_id(image)
    if actual != expected:
        raise RuntimeError(f"worker image drift: expected {expected}, got {actual}")
    return actual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=None, type=UUID)
    parser.add_argument("--gpu-image", default=_DEFAULT_GPU_IMAGE)
    parser.add_argument("--live-relay", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    os.chdir(_ROOT)
    run_id = str(args.run_id) if args.run_id is not None else ID.generate().value
    expected_image_digest = _expected_image_id(args.gpu_image)
    resources = _build_resources(run_id, args.live_relay, expected_image_digest)
    try:
        result = run_clean_workflow(
            resources.deps,
            experiment_plan_id=_PLAN_ID,
            experiment_command="python experiment.py",
            experiment_timeout_seconds=args.timeout,
        )
        payload = result.to_payload()
        payload["runtime_image_digest"] = _verify_runtime_image(
            resources.deps, run_id, args.gpu_image
        )
        payload["canonical_persistence"] = "POSTGRESQL"
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    finally:
        resources.close()


if __name__ == "__main__":
    raise SystemExit(main())
