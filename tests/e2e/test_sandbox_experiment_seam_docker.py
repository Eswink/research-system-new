"""沙箱实验缝的**真实容器**那一段（GOAL-011 EC-03 的机械面）。

判的是：合约（`m12_experiment_execution`）**自己 pin** 的脚本/镜像/命令，经**产品缝**
（`services/api/experiment_support.sandbox_experiment_runner` + `docker_experiment_assembly`
⇒ 既有 `DockerExecutionBackend`）真的在容器里跑完，且产物 / 证据 / 预算三者在**读面**可读。

为什么这个文件必须存在：`tests/application/run_orchestration/test_sandbox_experiment_dispatch.py`
的模块 docstring 早就把「真实容器那一段」指给本文件名——而**此前该文件并不存在**
（`ls tests/e2e/ | grep sandbox` 只有 `test_sandbox_experiment_reachability.py`）。真实后端
此前只在**间接**路径上被测过（`tests/integration/test_ig1_full_chain_docker.py` 直接调
`ExperimentExecutor`）；**缝**自 cycle 6 接上以来只被 Fake 后端走过，于是三处缺陷
（计划 id / 策略 scope / 工作区登记，见 `tests/api/test_sandbox_experiment_seam.py`）
一直到 cycle 9 首次真实派发才暴露。本文件把它们之后的形态钉住。

**如实写明的两条边界**：

- 本文件判的是**机械面**（实验真的跑了、产物/证据/可读面齐备）。**carrier 协议本身**
  （m12 的 7 个 phase 跑到 `SUCCEEDED`）今天仍止步于 discovery 的验收门。这条边界原记载
  理由是「`SCHEMA_VALID` 未接线 + `EVIDENCE_COVERAGE: 3 < 10`」：前者已由 GOAL-014
  cycle 6（`PLAN-20260924-160`）接通输入面，故不再适用；后者属该合约**自带**的判据，
  本轮一字未改（`examples/contracts/task_contracts.yaml` 不在本轮改动面内）。本文件
  **不**粉饰、也不放宽任何判据：启动 carrier run 只为取得一个**真实存在**的 run 行，
  好让 run 级读面对得上，该 run 的终态仍如实为 `FAILED`（下面显式断言）。
- 容器内不触网（纯标准库脚本）；本机 Docker daemon 可用即可，故挂 `requires_docker`：
  非 Linux 容器的守护进程下如实 skip（`tests/conftest.py` 的守卫），
  `container-quality` 作业（`-m requires_docker`）真跑。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID, Digest
from packages.domain.enums import ActivationPolicy, ModelBindingMode, RoleCategory
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "m12_reference_research_v1.yaml"
CONTRACT_ID = "m12_experiment_execution"


def _deps() -> Any:
    from tests.api.run_fixtures import make_run_ready_deps

    return make_run_ready_deps()


def _spec() -> SessionSpecContext:
    return SessionSpecContext(
        role=RoleDefinition(
            id="experiment_engineer",
            role_type="experiment_engineer",
            category=RoleCategory.EXPERIMENT,
            activation_default=ActivationPolicy.ALWAYS,
        ),
        agent=AgentSpec(
            id="engineer",
            role="experiment_engineer",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        frozen_tool_set=(),
        declared_input_artifacts=(),
        run_chain_tool_ids=(),
    )


def _seam(deps: Any, contract: Any) -> Any:
    """产品缝：执行体 = 既有 `DockerExecutionBackend`，镜像/脚本取**合约自己的**声明。"""
    from services.api.assembly import policy_bindings
    from services.api.experiment_support import (
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    declaration = contract.experiment
    assert declaration is not None, f"{CONTRACT_ID} must pin its experiment"
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "examples/config/policy.yaml must be loadable"
    return sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            policy=policy,
            script=declaration.script,
            image=declaration.image,
            experiment_store=deps.experiment_store,
        )
    )


def _carrier_run_id(client: Any) -> str:
    """起一次 carrier run，只为一个**真实存在**的 run 行（它的终态如实断言为 FAILED）。"""
    started = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": "ec03-seam-docker"},
    )
    assert started.status_code == 200, started.text
    assert started.json()["state"] == "FAILED", started.json()
    return str(started.json()["id"])


def _assert_scientific_products(result: Any) -> Any:
    """段 2：脚本真的跑了——语义指标摘要非空、指标里有训练/测试样本量。"""
    assert result.outcome == "SUCCEEDED", result.message
    outcome = result.experiment_outcome
    assert outcome is not None, result.message
    experiment_run = outcome.run
    assert str(experiment_run.state) == "SUCCEEDED", experiment_run.state
    record = experiment_run.result
    assert record is not None
    assert record.semantic_metrics_digest is not None
    metric_names = {item.metric.name for item in record.metrics}
    assert {"n_train", "n_test"} <= metric_names, metric_names
    return experiment_run


def _assert_evidence_admitted(deps: Any, result: Any) -> None:
    """段 3：证据经**唯一准入入口**落 canonical，内容 digest 可重算（防篡改）。"""
    admission = result.experiment_admission
    assert admission is not None, "experiment evidence was not admitted"
    assert admission.evidence, admission
    for evidence in admission.evidence:
        assert evidence.artifact_id is not None
        content = deps.artifacts.get(evidence.artifact_id)
        assert Digest.of_bytes(content) == Digest.parse(evidence.content_digest)


def _assert_run_read_faces(client: Any, run_id: str, experiment_run_id: str) -> None:
    """段 4：run 级读面看得到这次实验（EC-03 的「读面可读」）。"""
    view = client.get(f"/runs/{run_id}/experiments").json()
    assert [item["experiment_run_id"] for item in view["experiments"]] == [experiment_run_id], view
    artifacts = client.get(f"/runs/{run_id}/artifacts").json()
    assert artifacts, "experiment artifacts must be visible on the run's artifact face"
    assert any(str(item["id"]).endswith(":experiment_result.json") for item in artifacts), [
        item["id"] for item in artifacts
    ]


def test_the_contract_declared_experiment_runs_in_the_container() -> None:
    """主干：声明 → 缝 → 容器 → 产物/证据/canonical 读面（零出网）。

    四段（科学产物 / 证据准入 / run 级读面 / carrier 终态）各由上面的 helper 判，
    便于失败时一眼看出断在哪一段。
    """
    from fastapi.testclient import TestClient

    from services.api.app import create_app

    deps = _deps()
    context = deps.preflight_override
    assert context is not None
    contract = context.catalog.task_contracts[CONTRACT_ID]
    runner = _seam(deps, contract)

    with TestClient(create_app(deps)) as client:
        run_id = _carrier_run_id(client)
        task = ResearchTask(id=ID.generate(), run_id=ID(run_id), contract_id=CONTRACT_ID, attempt=1)
        result = runner(task, contract, _spec(), "trace-ec03-seam-docker")
        experiment_run = _assert_scientific_products(result)
        _assert_evidence_admitted(deps, result)
        _assert_run_read_faces(client, run_id, experiment_run.id.value)


def test_the_container_is_really_used_not_a_stub() -> None:
    """反证面：制品与摘要**来自容器**——桩执行体给不出镜像摘要与 stdout/stderr 两份制品。"""
    deps = _deps()
    context = deps.preflight_override
    assert context is not None
    contract = context.catalog.task_contracts[CONTRACT_ID]
    declaration = contract.experiment
    assert declaration is not None
    assert Path(declaration.script).is_file(), declaration.script

    task = ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id=CONTRACT_ID, attempt=1)
    result = _seam(deps, contract)(task, contract, _spec(), "trace-ec03-seam-image")
    experiment_run = _assert_scientific_products(result)
    record = experiment_run.result
    assert record is not None
    assert record.image_digest, "the container's image digest must be recorded"
    assert experiment_run_id_of(str(task.run_id.value)) == experiment_run.id.value

    refs = {ref.rsplit(":", 1)[-1] for ref in record.artifact_refs}
    assert {"stdout.log", "stderr.log"} <= refs, refs
    stored = json.loads(deps.artifacts.get(f"{experiment_run.id.value}:experiment_result.json"))
    assert stored["experiment_run_id"] == experiment_run.id.value
