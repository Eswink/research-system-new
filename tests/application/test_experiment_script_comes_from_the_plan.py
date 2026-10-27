"""GOAL-20261027-098 EC-03：**实验脚本由方向派生**（白名单「选择级」，方案 (b)）。

**它补哪一格**（本轮建档实测）：`design_source="plan"` 到此只让**臂与参数**由计划派生 ——
「跑哪个脚本」仍是装配常量（`services/api/executor_wiring.py::DEFAULT_EXPERIMENT_SCRIPT`），
`declared_or_assembled` 只在**契约 pin** 时改它。⇒ 换方向换多少次，跑的都是
`exact_match_index_benchmark.py`：派生停在**参数级**。

**本轮走 (b)：计划在出厂脚本白名单里挑一个 + 给参数。**(a)「模型为新问题写脚本、沙箱里跑
模型给的代码」是**安全面变更**（`policy` / `classify_risk` / `EXECUTE` 类 HIGH 的既有门
**没有**覆盖「模型产出的任意 Python」这类产物）⇒ 登记为待拍板子项，本轮不碰。

**本文件判四件事**（缺一即判红）：

1. **选择真的生效**（行为面）：同一份装配、**两份计划**（一份点名脚本 A、一份点名 B）⇒
   两次派发真的把**不同的脚本**交给执行链（判 `assembly.script`，那是 `_governed_executor`
   复制进沙箱工作区的那个文件）；
2. **零回归**：计划没写 `script` ⇒ **逐字**回到装配面那一个（同一装配、同一份计划加不加
   这个键之外的差异都没有）；
3. **白名单是闭集**：名字不认识 / 绝对路径 / `..` / 盘符 / 非字符串 ⇒ **点名拒绝**
   （不静默回落 —— 静默回落会把「计划点名了一个跑不了的脚本」伪装成「计划没点名」）；
4. **来源面**：`design_source != "plan"` 时**不**读计划（检索来源与装配面来源的语义不动）。

**反证臂**：摘掉 `plan_selected_script` 那一行（真文件实测）⇒ 判据**点名判红**，并按
raw `sha256` 逐字节复原。没有这一臂，「脚本变了」可能只是「装配面刚好有两份」。

**不出容器、不出网**：执行体是受控替身（与 GOAL-079/080 的 e2e 同一手法）—— 本文件判的是
**派发面**（`assembly.script` 这一格换成了计划点名的那个）。**容器面**由
`tests/e2e/test_experiment_script_selection_docker.py` 判（`requires_docker`：真跑两个脚本、
按**容器产出的指标**区分跑的是哪一个），取证在
`evidence/GOAL-20261027-098-ec03-container-run.txt`。

**为什么两段都要**：`assembly.script` 是**输入**，容器读数才是**输出**。只判派发面时，
「复制脚本进工作区」那一步若出偏差，判据会照绿 —— 本轮就抓到过同类位置的真缺陷
（`with_novelty` 读了一个不存在的字段）。两段钉在一起才算「真跑用的是它」。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import services.api.experiment_support as experiment_support
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.experiments.design_from_plan import DESIGN_KEY, plan_artifact_id
from packages.application.experiments.design_script import (
    SHIPPED_EXPERIMENT_SCRIPTS,
    declared_script,
    plan_selected_script,
    script_override,
    script_whitelist,
)
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState
from packages.domain.evidence import (
    Claim,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
)
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import ExperimentRun, ExperimentRunResult
from packages.domain.tasks import ResearchTask
from services.api.experiment_support import (
    DESIGN_SOURCE_PLAN,
    SandboxExperimentAssembly,
    sandbox_experiment_runner,
)
from tests.application.subprocess_press_support import press_run
from tests.application.test_experiment_parameters import _contract, _spec_context

_ROOT = Path(__file__).resolve().parents[2]
_SUPPORT = "services/api/experiment_support.py"

RUN_ID = "7c1d2e3f-4a5b-4c6d-8e9f-0a1b2c3d4e5f"
#: `ID` 只接受合法 UUID4 布局（域不变量）⇒ 任务 id 也是 UUID 形态。
TASK_ID = "8d2e3f4a-5b6c-4d7e-9f0a-1b2c3d4e5f60"

#: 装配面的兜底脚本（组合根常量那一份）。
_ASSEMBLED = "examples/experiments/exact_match_index_benchmark.py"
#: 计划点名的两个**不同**出厂脚本。
_SCRIPT_A = "examples/experiments/sort_analysis_baseline.py"
_SCRIPT_B = "examples/experiments/m12_reference_classification.py"


# --- 夹具 --------------------------------------------------------------------


def _task(run_id: str = RUN_ID) -> ResearchTask:
    from packages.domain.core import ID

    return ResearchTask(id=ID(TASK_ID), run_id=ID(run_id))


def _assembly(**overrides: object) -> SandboxExperimentAssembly:
    base: dict[str, object] = {
        "execution": object(),
        "artifacts": FakeArtifactStore(),
        "policy": object(),
        "image": "research-os-sandbox:m9-test",
        "script": _ASSEMBLED,
    }
    base.update(overrides)
    return SandboxExperimentAssembly(**base)  # type: ignore[arg-type]


class _RecordingExecutor:
    """受控执行体：记录请求并返回一个带制品的科学终态（不出容器）。

    带制品是**必需**的：声明了 `design_source` ⇒ 读取器要走证据链 ⇒ 准入面要求终态运行
    带 spec/result 且至少一个制品（既有检查，本条判据一字未改）。
    """

    def __init__(self, artifacts: Any) -> None:
        self.requests: list[Any] = []
        self.artifacts = artifacts

    def execute(self, request: Any) -> ExperimentExecutionOutcome:
        from packages.domain.experiments import ExperimentRunSpec

        self.requests.append(request)
        artifact_id = f"{request.run_id.value}:metrics"
        content = json.dumps(
            {"experiment_run_id": request.run_id.value, "status": "SUCCEEDED", "metrics": {"n": 1}},
            sort_keys=True,
        ).encode("utf-8")
        self.artifacts.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/json",
                storage_uri=None,
                created_by="sandbox-experiment",
                source_refs=[f"experiment:{request.run_id.value}"],
                classification="experiment_result",
            ),
            content,
        )
        self.artifacts.mark(artifact_id, ArtifactState.VERIFIED)
        run = ExperimentRun(
            id=request.run_id,
            plan_id=request.plan.id,
            state=ExperimentRunState.State.SUCCEEDED,
            spec=ExperimentRunSpec(input_digest=Digest.of_bytes(b"script-selection")),
            result=ExperimentRunResult(
                execution_run_id=request.run_id.value, artifact_refs=(artifact_id,)
            ),
        )
        return ExperimentExecutionOutcome(run=run)


def _seed_plan(assembly: SandboxExperimentAssembly, payload: object) -> None:
    """把一份计划产物登记进本 run 的证据链（= 它对本 run「在场」）。"""
    ledger = assembly.ledger
    assert ledger is not None, "本夹具的装配面总是带 ledger"
    content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    artifact_id = plan_artifact_id(TASK_ID)
    assembly.artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            storage_uri=None,
            created_by="agent:research_director",
            source_refs=[f"task:{TASK_ID}"],
            classification="execution_result",
        ),
        content,
    )
    assembly.artifacts.mark(artifact_id, ArtifactState.VERIFIED)
    evidence = Evidence(
        id="evidence:plan:script-selection",
        source_ref=f"tool:{artifact_id}",
        content_digest="0" * 64,
        extracted_by="agent:research_director",
        artifact_id=artifact_id,
        run_id=RUN_ID,
    )
    claim = Claim(id="claim:plan:script-selection", statement=f"plan {artifact_id}")
    ledger.register_evidence(evidence)
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim.id,
            evidence_id=evidence.id,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def _plan_assembly(payload: object, *, script: str | None = None) -> SandboxExperimentAssembly:
    overrides: dict[str, object] = {
        "design_source": DESIGN_SOURCE_PLAN,
        "ledger": FakeEvidenceLedger(),
    }
    if script is not None:
        overrides["script"] = script
    assembly = _assembly(**overrides)
    _seed_plan(assembly, payload)
    return assembly


def _pinned_contract(script: str) -> Any:
    """一份**pin 了脚本**的契约（与出厂 `m12_experiment_execution` 同形）。"""
    from dataclasses import replace as _replace

    return _replace(_contract(), experiment=replace_spec(script))


def replace_spec(script: str) -> Any:
    from packages.domain.tasks import ExperimentExecutionSpec

    return ExperimentExecutionSpec(script=script)


def _dispatch(
    assembly: SandboxExperimentAssembly, monkeypatch: pytest.MonkeyPatch
) -> tuple[Any, Any, list[str | None]]:
    """跑**真**派发体，只换执行体那一步；返回派发时实际交给沙箱的脚本路径。

    `seen` 每**任务**一条（`_governed_executor` 在 `run()` 里只解析一次，各臂共用同一个
    执行体 —— 那是既有形态：脚本是本 run 的选择，不是某个臂的选择）。
    """
    seen: list[str | None] = []
    executor = _RecordingExecutor(assembly.artifacts)
    real = experiment_support._governed_executor

    def spy(resolved: Any) -> Any:
        seen.append(getattr(resolved, "script", None))
        return executor

    monkeypatch.setattr(experiment_support, "_governed_executor", spy)
    try:
        result = experiment_support.sandbox_experiment_runner(assembly)(
            _task(), _contract(), _spec_context(), "trace-ec03"
        )
    finally:
        monkeypatch.setattr(experiment_support, "_governed_executor", real)
    return result, executor, seen


# --- 1. 选择真的生效 ---------------------------------------------------------


class TestThePlanSelectsTheScript:
    """**换计划里的选择 ⇒ 换真跑的脚本**（这是「由方向派生」从参数级升到选择级的定义）。"""

    def test_the_plan_script_is_what_the_sandbox_runs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assembly = _plan_assembly({DESIGN_KEY: {"arms": {"only": {}}, "script": _SCRIPT_A}})
        _result, _executor, seen = _dispatch(assembly, monkeypatch)
        assert seen == [_SCRIPT_A], seen

    def test_two_plans_select_two_different_scripts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """**同一装配**、两份计划 ⇒ 两次派发跑的是**不同**的脚本。"""
        first = _plan_assembly({DESIGN_KEY: {"arms": {"only": {}}, "script": _SCRIPT_A}})
        _r1, _e1, first_seen = _dispatch(first, monkeypatch)
        second = _plan_assembly({DESIGN_KEY: {"arms": {"only": {}}, "script": _SCRIPT_B}})
        _r2, _e2, second_seen = _dispatch(second, monkeypatch)
        assert first_seen == [_SCRIPT_A], first_seen
        assert second_seen == [_SCRIPT_B], second_seen
        assert first_seen != second_seen

    def test_every_arm_of_a_multi_arm_design_uses_the_selected_script(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """选择是**本 run** 的，不是某个臂的：各臂共用同一个脚本（否则「臂」会偷换变量）。

        `seen` 因此是**一条**（`_governed_executor` 在 `run()` 里解析一次，各臂共用同一个
        执行体 —— 既有形态）。两个臂都真的跑了由 `len(executor.requests) == 2` 判。
        """
        assembly = _plan_assembly({
            DESIGN_KEY: {"arms": {"control": {}, "treatment": {"n_items": 40}}, "script": _SCRIPT_B}
        })
        _result, executor, seen = _dispatch(assembly, monkeypatch)
        assert len(executor.requests) == 2, [r.run_id.value for r in executor.requests]
        assert seen == [_SCRIPT_B], seen
        assert seen != [_ASSEMBLED]


# --- 2. 零回归 ---------------------------------------------------------------


class TestWithoutTheKeyNothingChanges:
    """计划没写 `script` ⇒ **逐字**回到装配面（既有行为一个字节不动）。"""

    def test_no_script_key_falls_back_to_the_assembled_script(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assembly = _plan_assembly({DESIGN_KEY: {"arms": {"only": {}}}})
        _result, _executor, seen = _dispatch(assembly, monkeypatch)
        assert seen == [_ASSEMBLED], seen

    def test_no_design_source_never_reads_the_plan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`design_source is None` ⇒ 计划里的 `script` **不被读**（来源面各管各的）。"""
        assembly = _assembly(ledger=FakeEvidenceLedger())
        _seed_plan(assembly, {DESIGN_KEY: {"arms": {"only": {}}, "script": _SCRIPT_A}})
        _result, _executor, seen = _dispatch(assembly, monkeypatch)
        assert seen == [_ASSEMBLED], seen

    def test_a_contract_pin_still_wins_over_the_plan_selection(self) -> None:
        """契约 pin（静态承诺）强于计划选择（本 run 的模型正文）—— 三档优先级。

        调用形态与派发体逐字一致：`declared_or_assembled` 先给出「契约优先」的那个值
        （这里就是 pin 的 `pinned`），再交给选择面 —— 计划点名的 `_SCRIPT_A` **不得**覆盖它。
        """
        pinned = "examples/experiments/m12_reference_classification.py"
        contract = _pinned_contract(pinned)
        assembly = _plan_assembly({DESIGN_KEY: {"arms": {"only": {}}, "script": _SCRIPT_A}})
        assert pinned != _SCRIPT_A
        chosen = plan_selected_script(assembly, _task(), contract=contract, assembled=pinned)
        assert chosen == pinned, chosen
        assert chosen != _SCRIPT_A


# --- 3. 白名单是闭集 ---------------------------------------------------------


class TestTheWhitelistIsClosed:
    """白名单外的名字 / 越界路径 / 坏形态 ⇒ **点名拒绝**（不静默回落）。"""

    def test_the_whitelist_names_real_shipped_scripts(self) -> None:
        allowed = script_whitelist()
        assert allowed == frozenset(SHIPPED_EXPERIMENT_SCRIPTS)
        for relative in allowed:
            assert (_ROOT / relative).is_file(), relative

    @pytest.mark.parametrize(
        "raw",
        [
            "examples/experiments/not_a_shipped_script.py",
            "/etc/passwd",
            "../../etc/passwd",
            "C:/Windows/system32/calc.exe",
            "examples/experiments/./sort_analysis_baseline.py",
        ],
    )
    def test_a_name_outside_the_whitelist_is_named_red(self, raw: str) -> None:
        from packages.application.experiments.design_from_plan import (
            ExperimentDesignUnreadableError,
        )

        with pytest.raises(ExperimentDesignUnreadableError, match="script"):
            declared_script({DESIGN_KEY: {}, "script": raw}, where="the-plan")

    def test_a_non_string_script_is_named_red(self) -> None:
        from packages.application.experiments.design_from_plan import (
            ExperimentDesignUnreadableError,
        )

        with pytest.raises(ExperimentDesignUnreadableError, match="non-empty"):
            declared_script({"script": 7}, where="the-plan")

    def test_an_unreadable_design_is_not_silently_ignored(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """计划**没有**设计块 ⇒ 点名拒绝（不是「没选脚本」—— 两者必须分得开）。"""
        from packages.application.experiments.design_from_plan import (
            ExperimentDesignUnreadableError,
        )

        assembly = _plan_assembly({"plan": "no design block here"})
        with pytest.raises(ExperimentDesignUnreadableError, match="experiment_design"):
            sandbox_experiment_runner(assembly)(_task(), _contract(), _spec_context(), "trace-ec03")

    def test_the_whitelist_override_is_the_only_path(self) -> None:
        """`script_override` 只有两条出口：计划点的那个 / 装配面那个（没有第三条）。

        入参是**设计块本身**（`design_block_in` 读出来的那个对象），不是外层载荷 ——
        这一点与本文件其它用例的夹具不同，故单独断言（写错会让「计划没点名」看起来像
        「点名了但没生效」）。
        """
        design = {"arms": {"only": {}}, "script": _SCRIPT_A}
        assert script_override(design, where="p", assembled=_ASSEMBLED) == _SCRIPT_A
        unchanged: dict[str, object] = {"arms": {"only": {}}}
        assert script_override(unchanged, where="p", assembled=_ASSEMBLED) == _ASSEMBLED


# --- 4. 反证臂：摘掉选择机制 ⇒ 判红 -----------------------------------------

#: 按压锚点：派发体里那一行调用（改成「删掉实现」这个**真形态**）。
_NEEDLE = (
    "        script = plan_selected_script(assembly, task, contract=contract, assembled=script)\n"
)
#: 按压时要跑的那条**行为**用例（它在类里 ⇒ 目标名必须带类名，否则 pytest exit 4）。
_PRESS_TARGET = (
    "tests/application/test_experiment_script_comes_from_the_plan.py"
    "::TestThePlanSelectsTheScript::test_the_plan_script_is_what_the_sandbox_runs"
)


def test_removing_the_selection_mechanism_makes_the_judge_red() -> None:
    """**按压在真文件上**：删掉 `experiment_support` 里那一行调用 ⇒ 行为判据**真的判红**。

    按压是**行为级**的：删掉那一行之后，在**子进程**里跑本文件那条行为用例
    （`test_the_plan_script_is_what_the_sandbox_runs`）—— 它必须**失败**；按 raw `sha256`
    逐字节复原之后，同一条用例必须**再次通过**。

    为什么用子进程：`importlib.reload` 会把新的类对象塞进共享模块，污染本会话里其它
    已经 `from ... import` 过这些名字的测试文件。子进程读到的是**磁盘上的真字节**，
    本进程的状态一个字节都不动 —— 而「按压对象是受判实现本身」这条要求照样成立。

    这类「按压工具自己的 bug」只能靠**按压后确认判据真的红了**才发现：本轮第一次写这
    条时用的是 `monkeypatch`（对已加载的模块毫无影响）⇒ 按压假绿；第二次是子进程的
    `pytest` 目标名少了类名 ⇒ exit 4（usage error）被读成「按压失败」。两次都被这条
    纪律抓住，形态收在 `subprocess_press_support`（本文件卡在 450 行硬上限上）。
    """
    result = press_run(_SUPPORT, _NEEDLE, _PRESS_TARGET)
    assert result.restored_digest_matches, "press restore failed（复原不是同一个字节）"
    assert result.pressed_code != 0, (
        "removing the plan-selection call did not turn the behavioural case red — "
        "the judge cannot see the mechanism it exists to test"
    )
    assert result.restored_code == 0, "the restored tree did not go green again"


def test_the_mechanism_is_back_after_the_press(monkeypatch: pytest.MonkeyPatch) -> None:
    """按压复原之后，选择**确实**又生效（复原不是「刚好也绿」）。"""
    assembly = _plan_assembly({DESIGN_KEY: {"arms": {"only": {}}, "script": _SCRIPT_A}})
    _result, _executor, seen = _dispatch(assembly, monkeypatch)
    assert seen == [_SCRIPT_A], seen
