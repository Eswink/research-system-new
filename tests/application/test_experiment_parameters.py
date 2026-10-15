"""GOAL-20261015-079 EC-01 判据：**实验参数由声明给出**（不是脚本里的模块常量）。

**被测对象**：`experiments/plan_parameters.py` 的白名单传递面 + 装配面（`SandboxExperimentAssembly`
的 `parameters` → `ExperimentExecutionRequest.environment`）+ 沙箱脚本的参数读取
（`examples/experiments/exact_match_index_benchmark.py` 的 `_declared_int`）。

**五件事逐条取证**：

1. **白名单生效**（§9）：白名单内的键**逐键**变成带前缀的环境变量；白名单外的键
   **点名拒绝**（不静默丢弃、不原样转发任意环境变量）；
2. **声明即传递**（逐键）：装配声明的量原样出现在执行请求的环境里（键名逐字、值逐字）；
3. **缺省零回归**：没有任何声明时，请求里的 `environment` 与**今天逐字相同**
   （只有 `EXPERIMENT_RUN_ID` 与装配方显式给的那几件）；
4. **脚本读得到**：参数经环境进容器后，脚本产出**声明值下的指标**（不是常量下的）；
5. **脚本侧 fail-closed**：声明的值**非法**时脚本点名失败（**不静默回落**到缺省 ——
   那会把「声明被吞掉」伪装成「跑成功了」）。

**离线纪律**：本文件不跑容器（那是 e2e 的活），只判**参数面**的传递与拒绝语义；
`_declared_int` 的判据直接以子进程跑脚本的**纯函数部分**（生成语料 / 求指标），
不经 HTTP、不出网。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from packages.application.experiments.plan_parameters import (
    ALLOWED_PARAMETERS,
    PARAMETER_PREFIX,
    UndeclaredExperimentParameterError,
    declared_parameters,
    parameter_environment,
)

_SCRIPT = Path("examples/experiments/exact_match_index_benchmark.py")


class TestTheWhitelistIsEnforced:
    """① 白名单：声明的键逐键传递；未声明的键**点名拒绝**。"""

    def test_declared_keys_become_prefixed_environment_entries(self) -> None:
        environment = parameter_environment({"seed": 11, "n_items": 100})
        assert environment == {
            f"{PARAMETER_PREFIX}SEED": "11",
            f"{PARAMETER_PREFIX}N_ITEMS": "100",
        }, environment
        # 逐键：每个允许的键都能单独传递（不是「某些键恰好能过」）。
        for key in sorted(ALLOWED_PARAMETERS):
            single = parameter_environment({key: 3})
            assert single == {f"{PARAMETER_PREFIX}{key.upper()}": "3"}, (key, single)

    def test_an_undeclared_key_is_refused_by_name(self) -> None:
        with pytest.raises(UndeclaredExperimentParameterError, match="PATH"):
            parameter_environment({"PATH": "/usr/bin"})
        with pytest.raises(UndeclaredExperimentParameterError, match="secret"):
            parameter_environment({"secret": "x"})

    def test_a_null_value_is_refused_rather_than_dropped(self) -> None:
        """**空值与缺省是两件事**：`None` 多半是上游写错 ⇒ 点名，不静默当没声明。"""
        with pytest.raises(UndeclaredExperimentParameterError, match="n_items"):
            parameter_environment({"n_items": None})

    def test_no_declaration_yields_an_empty_mapping(self) -> None:
        assert parameter_environment(None) == {}
        assert parameter_environment({}) == {}

    def test_the_prefix_namespace_does_not_collide_with_the_executor_key(self) -> None:
        """参数前缀与执行器自己的键**不相交**（`EXPERIMENT_RUN_ID` 不被参数面覆盖）。"""
        assert not "EXPERIMENT_RUN_ID".startswith(PARAMETER_PREFIX)
        environment = parameter_environment({"seed": 1})
        assert "EXPERIMENT_RUN_ID" not in environment, environment

    def test_the_round_trip_reads_the_parameters_back(self) -> None:
        environment = parameter_environment({"seed": 5, "duplicate_pairs": 2})
        assert declared_parameters(environment) == {"seed": "5", "duplicate_pairs": "2"}
        assert declared_parameters({"EXPERIMENT_RUN_ID": "run-1"}) == {}


class TestTheDeclarationReachesTheRequest:
    """② 声明即传递（装配面 → 执行请求）。"""

    def _request_environment(self, parameters: dict[str, object]) -> dict[str, str]:
        """用**真装配件**构造一次执行请求（不经容器：只读它要交给容器的环境）。"""
        from adapters.fakes.artifact_store import FakeArtifactStore
        from packages.application.experiments.types import ExperimentExecutionRequest
        from services.api.experiment_support import (
            SandboxExperimentAssembly,
            _request_builder,
        )

        assembly = SandboxExperimentAssembly(
            execution=object(),
            artifacts=FakeArtifactStore(),
            policy=object(),
            image="research-os-sandbox:m9-test",
            script=str(_SCRIPT),
            parameters=dict(parameters),
        )
        build = _request_builder(assembly)
        request: ExperimentExecutionRequest = build(_task(), _contract(), _spec_context())
        return dict(request.environment)

    def test_the_declared_values_appear_verbatim_in_the_request(self) -> None:
        environment = self._request_environment({"seed": 11, "n_items": 100})
        assert environment[f"{PARAMETER_PREFIX}SEED"] == "11", environment
        assert environment[f"{PARAMETER_PREFIX}N_ITEMS"] == "100", environment
        # 执行器自己的键仍在（本 GOAL 不碰它 —— 既有语义）。
        assert environment.get("EXPERIMENT_RUN_ID"), environment

    def test_no_declaration_keeps_the_request_environment_unchanged(self) -> None:
        """③ 缺省零回归：未声明 ⇒ 环境里**只有**执行器的键（与今天逐字相同）。"""
        environment = self._request_environment({})
        assert set(environment) == {"EXPERIMENT_RUN_ID"}, environment


def _task() -> Any:
    from uuid import uuid4

    from packages.domain.core import ID
    from packages.domain.tasks import ResearchTask

    # `ID` 要求合法 UUID4（域不变量）；本判据只关心**环境里传了什么** ⇒ 标识任取。
    return ResearchTask(id=ID(str(uuid4())), run_id=ID(str(uuid4())))


def _contract() -> Any:
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import (
        AcceptanceCriterion,
        ExperimentExecutionSpec,
        TaskContract,
    )

    return TaskContract(
        id="experiment_execution",
        version="1.0.0",
        purpose="parameter surface judgment",
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="metrics")
        ],
        experiment=ExperimentExecutionSpec(),
    )


def _spec_context() -> Any:
    """会话装配上下文（复用既有共享夹具的 role/agent，不手搓域对象）。"""
    from packages.application.run_orchestration.task_executor import SessionSpecContext
    from tests.contracts.fixtures import agent_spec, role_definition

    return SessionSpecContext(
        role=role_definition(),
        agent=agent_spec(),
        frozen_manifest_digest="sha256:" + "0" * 64,
    )


class TestTheScriptReadsTheDeclaration:
    """④ 脚本读得到；⑤ 非法值点名失败（不静默回落）。"""

    def _run_script(self, extra: dict[str, str]) -> dict[str, object]:
        """在临时目录里真跑一次脚本（纯标准库；不经容器、不出网）。"""
        script = str(_SCRIPT.resolve())
        environment = {**os.environ, "EXPERIMENT_RUN_ID": "run-param-1", **extra}
        with tempfile.TemporaryDirectory() as workspace:
            completed = subprocess.run(  # noqa: S603 - 受控命令（固定 argv、无 shell）
                [sys.executable, "-B", script],
                cwd=workspace,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            assert completed.returncode == 0, (completed.returncode, completed.stderr[-400:])
            payload = json.loads(Path(workspace, "metrics").read_text(encoding="utf-8"))
        return dict(payload)

    def test_the_default_run_matches_the_module_constants(self) -> None:
        metrics = self._run_script({})
        assert metrics["seed"] == 7, metrics
        assert metrics["n_items"] == 800, metrics
        assert metrics["duplicates_expected"] == 40, metrics

    def test_the_declared_parameters_are_honoured(self) -> None:
        metrics = self._run_script({
            f"{PARAMETER_PREFIX}SEED": "11",
            f"{PARAMETER_PREFIX}N_ITEMS": "120",
            f"{PARAMETER_PREFIX}DUPLICATE_PAIRS": "6",
        })
        assert metrics["seed"] == 11, metrics
        assert metrics["n_items"] == 120, metrics
        assert metrics["duplicates_expected"] == 6, metrics
        assert metrics["duplicates_found"] == 6, metrics
        assert metrics["agreement"] is True, metrics

    def test_a_malformed_declared_value_fails_by_name(self) -> None:
        """**不静默回落**：值非法 ⇒ 脚本点名失败（回落会把「声明被吞掉」伪装成成功）。"""
        script = str(_SCRIPT.resolve())
        with tempfile.TemporaryDirectory() as workspace:
            completed = subprocess.run(  # noqa: S603 - 受控命令（固定 argv、无 shell）
                [sys.executable, "-B", script],
                cwd=workspace,
                env={
                    **os.environ,
                    "EXPERIMENT_RUN_ID": "run-param-2",
                    f"{PARAMETER_PREFIX}SEED": "not-a-number",
                },
                capture_output=True,
                text=True,
                check=False,
            )
        assert completed.returncode != 0, completed.stdout
        assert f"{PARAMETER_PREFIX}SEED" in completed.stderr, completed.stderr[-400:]
        assert "must be an integer" in completed.stderr, completed.stderr[-400:]
