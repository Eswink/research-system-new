"""沙箱实验缝（`services/api/experiment_support.py`）的离线判据。

背景（GOAL-011 cycle 9，实测）：cycle 6 把**既有**实验执行链接进编排的实验缝时，
那条路**从未被派发过**——首次真实派发连着撞上三处缺陷。三处都在本文件里被钉住，
执行体换成**既有 Fake 后端**（不起容器、不出网；真实容器那一段见
`tests/e2e/test_sandbox_experiment_seam_docker.py`）：

1. **计划 id 不是合法 UUID**：`_preregistered_plan` 曾用 `experiment_run_id_of(f"plan-…")`，
   而该函数要求输入**本身是 UUID**（`UUID(ID(x).value)`）⇒ 每次派发都在建计划时抛
   `ValueError: invalid UUID`（容器都起不来）。本文件第 1 条判据在这行会直接红。
2. **执行期策略缺 scope**：`GovernedExperimentExecutor._enforce_policy` 构造
   `PolicyRequest` 时不带 scope，而 `artifact.write` 在 `examples/config/policy.yaml`
   里是 `allow + scope: run` ⇒ 匹配不上，落到 `default_effect: DENY` ⇒ 真实策略下实验被拒
   （"preflight 放行、执行期拒绝" 的分裂，与工具面 `ScopedPolicy` 修过的是同一类）。
3. **沙箱工作区没在后端登记**：执行链会对 `request.workspace` 取租约，而后端对没登记过的
   id 直接 `unknown workspace: sandbox-experiment`。

判据走**装配面自身的构造**（`sandbox_experiment_runner` + `SandboxExperimentAssembly`）：
不是测试自搭一份平行装配——否则修好产品路径而判据仍绿，就白判了。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from adapters.fakes import FakeArtifactStore, FakeExecutionBackend
from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID
from packages.domain.enums import (
    AcceptanceCriterionType,
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import (
    AcceptanceCriterion,
    ExperimentExecutionSpec,
    ResearchTask,
    TaskContract,
)
from services.api.experiment_support import (
    SandboxExperimentAssembly,
    sandbox_experiment_runner,
)

_COMMAND = "python experiment.py"


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(), run_id=ID.generate(), contract_id="m12_experiment_execution", attempt=1
    )


def _contract() -> TaskContract:
    return TaskContract(
        id="m12_experiment_execution",
        version="1.0.0",
        purpose="sandboxed experiment for the seam judge",
        # 判据只关心「谁执行」这条声明：验收标准取一条最简的（本文件不判验收门）。
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="experiment_result.json"
            )
        ],
        experiment=ExperimentExecutionSpec(
            script="examples/experiments/m12_reference_classification.py",
            image="research-os-sandbox:m9-test",
            command=_COMMAND,
            timeout_seconds=60,
        ),
    )


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


def _seam(root: Path, backend: FakeExecutionBackend, policy: Any) -> Any:
    return sandbox_experiment_runner(
        SandboxExperimentAssembly(
            execution=backend,
            artifacts=FakeArtifactStore(),
            policy=policy,
            image="research-os-sandbox:m9-test",
            root=str(root),
            script=None,
        )
    )


def _write_result(root: Path, task: ResearchTask) -> None:
    """预期产物：执行体（本判据里是 Fake 后端）跑完后留在工作区的实验结果文件。

    `experiment_run_id` 必须**逐字**等于装配面交进容器的那个（解析器会比对），而它由
    `experiment_run_id_of(run_id)` 确定性派生 ⇒ 判据自己算得出来，不靠猜。
    """
    (root / "experiment_result.json").write_text(
        json.dumps({
            "experiment_run_id": experiment_run_id_of(str(task.run_id.value)),
            "status": "SUCCEEDED",
            "artifact_refs": [],
            "metrics": {"n": 1},
        }),
        encoding="utf-8",
    )


def _real_policy() -> Any:
    from services.api.assembly import policy_bindings

    policy = policy_bindings()["policy_evaluator"]
    assert policy is not None, "examples/config/policy.yaml must be loadable"
    return policy


def test_the_seam_runs_a_declared_experiment_under_the_real_policy(tmp_path: Path) -> None:
    """主干：声明了实验的合约经装配面的缝跑完，终态 `SUCCEEDED`（真实 policy.yaml 下）。

    这一条同时压住三处缺陷：计划 id（非法 UUID 会让本用例直接抛错）、
    执行期策略 scope（缺 scope ⇒ 真实策略判 DENY ⇒ 结果是 `FAILED`）、
    工作区登记（未登记 ⇒ 取租约时 `unknown workspace` ⇒ 同样 `FAILED`）。
    """
    task = _task()
    backend = FakeExecutionBackend()
    _write_result(tmp_path, task)
    result = _seam(tmp_path, backend, _real_policy())(task, _contract(), _spec(), "trace-seam")
    assert result.outcome == "SUCCEEDED", result.message
    assert backend.method_calls("execute") == 1, backend.method_calls("execute")


def test_a_policy_denied_capability_stops_before_any_execution(tmp_path: Path) -> None:
    """反证：策略判 DENY ⇒ 任务 `FAILED`、**一次执行都没有**（补齐 scope 不等于放宽）。

    `_CAPABILITIES` 里任一能力被判拒都走这条；这里用整体 DENY 的求值器，判的是
    「拒绝仍然有效、且发生在触达执行体之前」。
    """
    from adapters.fakes import FakePolicyEvaluator
    from packages.domain.enums import PolicyDecision

    policy = FakePolicyEvaluator()
    policy.set_decision("artifact.write", PolicyDecision.DENY)
    backend = FakeExecutionBackend()
    task = _task()
    _write_result(tmp_path, task)
    result = _seam(tmp_path, backend, policy)(task, _contract(), _spec(), "trace-seam-denied")
    assert result.outcome == "FAILED", result.message
    assert "policy denied" in result.message, result.message
    assert backend.method_calls("execute") == 0, "策略拒绝必须发生在执行体之前"


@pytest.mark.parametrize("capability", ["code.execute", "workspace.write.code", "artifact.write"])
def test_every_guarded_capability_is_denied_by_default(tmp_path: Path, capability: str) -> None:
    """**默认 deny** 的结构判据：换个求值器也改不了「三能力必须全部被裁决」这件事。

    这条防的是「把 `_CAPABILITIES` 删到只剩一个」这类无声放宽：三个能力逐个被判，
    缺一个就有一条参数化用例红。
    """
    from adapters.fakes import FakePolicyEvaluator
    from packages.domain.enums import PolicyDecision

    policy = FakePolicyEvaluator()
    policy.set_decision(capability, PolicyDecision.DENY)
    task = _task()
    _write_result(tmp_path, task)
    result = _seam(tmp_path, FakeExecutionBackend(), policy)(
        task, _contract(), _spec(), f"trace-{capability}"
    )
    assert result.outcome == "FAILED", result.message
    assert capability in result.message, result.message
