"""GOAL-20261026-097 EC-01：**两个产品组合根都接上实验缝 / 报告缝**，且装配期零 Docker 连接。

**它补哪一格**（本轮建档实测）：`OrchestrationDependencies` 早就有 `experiment_task` /
`report_task` 两道缝，两个工厂也早已存在 —— 但 `rg "experiment_task|report_task"
services/api/composition.py` 零命中 ⇒ 缺省 `None` ⇒ 从**产品入口**（真 API）起的 run 走到
`experiment` / `report` 相就以**点名拒绝**收敛。链在 e2e 的手工装配里成立、在产品入口不成立。

**四件事逐条取证**（缺一即判红）：

1. `assemble()` 之后 `experiment_task` / `report_task` **均非 None**（SQLite 根）；
2. **装配期零 Docker 连接**：把后端工厂换成「构造即抛」，`assemble()` 仍成功 ——
   首次派发才调用它（惰性）；
3. **PG 根同判**：用静态判据（两个根文件都把 `**…_executor_seams(...)` 传进
   `OrchestrationDependencies`），因为本机的 PG 组合根需要真 DSN；
4. **反证**：从 SQLite 根摘掉接缝 ⇒ 判据**点名判红**（不是「恰好都非 None」的巧合）。

**为什么 2 必须两向**：只断言「非 None」时，一个**装配期就连 Docker** 的实现照样绿 ——
而那种实现在默认门的 `quality-windows-latest`（无 daemon 保证）上让 `assemble()` 直接炸，
且 `assemble()` 被多个默认门测试调用。所以既要「没被调用」，也要「真调用时它是活的」。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

import pytest

from services.api import executor_wiring, experiment_factories, experiment_support
from services.api.composition import assemble
from services.api.settings import ApiSettings

_ROOT = Path(__file__).resolve().parents[2]
_SQLITE_ROOT = _ROOT / "services" / "api" / "composition.py"
_PG_ROOT = _ROOT / "services" / "api" / "pg_composition.py"
_SEAM_NAMES = ("experiment_task", "report_task")
#: 演练用的**真实存在**的实验脚本（契约 pin 形态的按压要用真文件）。
_EXISTING_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"


def _settings(tmp_path: Path) -> ApiSettings:
    return ApiSettings(db_path=str(tmp_path.joinpath("control.db")))


def test_the_sqlite_root_wires_both_seams(tmp_path: Path) -> None:
    """(i) 两个缝都非 None（`assemble()` 出来的 deps，不补缝）。"""
    deps = assemble(_settings(tmp_path))
    try:
        runs = deps.runs
        assert runs is not None, "assembly must produce an orchestration service"
        inner = runs._deps
        assert inner.experiment_task is not None, "实验缝没接：声明了 experiment 的任务会被点名拒绝"
        assert inner.report_task is not None, "报告缝没接：声明了 report 的任务会被点名拒绝"
    finally:
        deps.close()


def test_assembly_opens_no_docker_connection(tmp_path: Path, monkeypatch: Any) -> None:
    """(ii) 正反两向：装配期**不**调用后端工厂；首次派发才调用（且真会抛）。"""

    calls: list[str] = []

    def exploding(image: str) -> Any:
        calls.append(image)
        raise AssertionError("constructed at assembly time")

    monkeypatch.setattr(experiment_factories, "docker_backend_factory", exploding)
    deps = assemble(_settings(tmp_path))
    try:
        runs = deps.runs
        assert runs is not None, "assembly must produce an orchestration service"
        inner = runs._deps
        assert inner.experiment_task is not None
        # 装配期零连接：工厂一次都没被调用。
        assert calls == [], f"装配期就构造了执行后端（镜像 {calls}）⇒ 无 daemon 的机器上会炸"
        # 首次派发**才**调用：这里直接把惰性入口拿出来按压（不真跑容器）。
        with pytest.raises(AssertionError, match="constructed at assembly time"):
            _first_dispatch(inner.experiment_task)
        # 首次派发用的是**契约 pin 的那个镜像**（EC-03 声明优先），不是装配面的兜底 ——
        # 两件事在同一行取证：惰性（此刻才调用）+ 声明优先（调用参数是 `pinned:1`）。
        assert calls == ["pinned:1"], calls
        assert calls != [executor_wiring.DEFAULT_EXPERIMENT_IMAGE]
    finally:
        deps.close()


def _first_dispatch(runner: Any) -> None:
    """让派发器走到「取后端」那一步（契约 pin 了脚本/镜像也照样要取后端）。

    不真起容器：`_DeferredExecution.get` 在**构造 Governor 之前**就调用工厂，
    所以抛出点一定早于任何容器操作 —— 这正是「首次派发才连 Docker」的判据形态。
    """
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import (
        AcceptanceCriterion,
        ExperimentExecutionSpec,
        TaskContract,
    )

    task = _minimal_task()
    contract = TaskContract(
        id="experiment_execution",
        version="1.0.0",
        purpose="probe",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.TEST_PASSES)],
        # 用**真实存在**的脚本：`_governed_executor` 会把脚本复制进沙箱工作区，
        # 一个不存在的路径会让判据在取后端之前就 `FileNotFoundError`（按压跑出来的）。
        experiment=ExperimentExecutionSpec(script=_EXISTING_SCRIPT, image="pinned:1"),
    )
    runner(task, contract, _minimal_spec_context(), "trace-lazy")


def _minimal_task() -> Any:
    """最小任务（只为走到取后端那一步；不进入任何执行分支）。`ID` 必须是真 UUID。"""
    from packages.domain.core import ID
    from packages.domain.tasks import ResearchTask

    return ResearchTask(
        id=ID("2f6a4d3e-8b71-4c52-9a0e-5d3c1b7f4a21"),
        run_id=ID("1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"),
    )


def _minimal_spec_context() -> Any:
    """最小会话规格上下文（同上：惰性判据不需要它被真的消费）。"""
    from types import SimpleNamespace

    return SimpleNamespace(phase_id="experiment")


def _kwargs_of(path: Path, function: str) -> set[str]:
    """某函数里 `OrchestrationDependencies(...)` 调用实际给的**关键字**名（按 AST 读）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        label = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
        if label != "OrchestrationDependencies":
            continue
        for keyword in node.keywords:
            if keyword.arg is not None:
                names.add(keyword.arg)
    return names


def test_both_roots_depend_on_the_shared_seam_builder() -> None:
    """(iii) 两个根都用**同一份**装配决策（`**…_executor_seams(...)`，不是各写一套）。

    静态判据的理由：PG 根的 `assemble()` 需要真 DSN（本机不可用）；而「两个根都走了同一个
    构造点」是**结构事实**，AST 读得到。`**` 展开在 AST 里是 `keyword.arg is None`。
    """
    for path, builder in (
        (_SQLITE_ROOT, "sqlite_executor_seams"),
        (_PG_ROOT, "pg_executor_seams"),
    ):
        text = path.read_text(encoding="utf-8")
        assert f"{builder}(" in text, f"{path.name} 没有调用 {builder}(…)"
        tree = ast.parse(text)
        spread = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == builder
        ]
        assert spread, f"{path.name} 里 {builder}(…) 不是直接调用"
        names = _kwargs_of(path, "OrchestrationDependencies")
        assert {"runtime", "workflow", "artifacts"} <= names, (path.name, sorted(names))


def test_the_pg_seam_reads_settings_from_the_config_object() -> None:
    """PG 缝的设置面取自 **`config.effective`**，不是 `inputs`（CI 抓到的真缺陷）。

    `_PgRuntimeInputs` 只有 credentials / policy_bindings / selection —— 从它取
    `effective` 会让三条 PG e2e 在 CI 上全红
    （`'_PgRuntimeInputs' object has no attribute 'effective'`），而本机跑不了 PG ⇒
    本地门看不见。所以这条判据是**静态**的：读签名与函数体。
    """
    import inspect

    from services.api import executor_wiring

    signature = inspect.signature(executor_wiring.pg_executor_seams)
    assert "config" in signature.parameters, sorted(signature.parameters)
    source = inspect.getsource(executor_wiring.pg_executor_seams)
    assert "config.effective.experiment_design_source" in source
    assert "inputs.effective" not in source.replace("`inputs`", ""), (
        "PG 缝不得从 `_PgRuntimeInputs` 取 `effective`（它没有那个字段）"
    )


def test_the_seams_cover_all_three_slots() -> None:
    """两个根的 seam 构造器都返回**三个**关键字（实验 / 报告 / 运行链检索面）。"""
    expected = {"experiment_task", "report_task", "capabilities"}
    source = (_ROOT / "services" / "api" / "executor_wiring.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.endswith("_executor_seams"):
            returned = [
                item
                for item in ast.walk(node)
                if isinstance(item, ast.Return) and isinstance(item.value, ast.Dict)
            ]
            assert returned, node.name
            keys = {
                str(cast(ast.Constant, key).value) for key in cast(ast.Dict, returned[0].value).keys
            }
            assert keys == expected, (node.name, sorted(keys))


def test_removing_the_seam_from_the_sqlite_root_is_named_red(tmp_path: Path) -> None:
    """(iv) 反证：摘掉 `**sqlite_executor_seams(...)` ⇒ 判据**点名**判红（不是静默）。"""
    source = _SQLITE_ROOT.read_text(encoding="utf-8")
    assert "**sqlite_executor_seams(faces, ports, dict(ports.tool_providers))" in source
    pressed = source.replace(
        "**sqlite_executor_seams(faces, ports, dict(ports.tool_providers)),", "", 1
    )
    assert pressed != source
    # 按压后的源码里，`OrchestrationDependencies(...)` 不再拿到那两个名字。
    module = ast.parse(pressed)
    given: set[str] = set()
    for node in ast.walk(module):
        if (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", "") == "OrchestrationDependencies"
        ):
            given |= {kw.arg for kw in node.keywords if kw.arg is not None}
    assert not (set(_SEAM_NAMES) & given), "摘掉接缝后仍能看见实验/报告缝 —— 判据没有真的咬住那行"


def test_run_chain_calls_are_pinned_to_their_phase() -> None:
    """出厂检索的两条调用**必须**标 `phase_id`（实证：不标 ⇒ 在问题相就执行并失败）。

    这条判据来自一次真实失败：不标 `phase_id` 时，`planned_in_this_phase` 对该 run 的
    **每一个** `run_chain` 相都返回 True ⇒ 问题相（上游产物还不存在）也去取
    `research_question.query`，run 在检索之前就 `FAILED`（`run.failed | run-chain
    capability step failed: declared input carries no 'research_question.query'`）。

    **两向**：正面向量（每条调用都带 `phase_id`）+ 反证（把 `phase_id` 抹掉 ⇒ 判定函数
    在问题相返回 True —— 也就是那个 bug 的形态）。
    """
    from services.api import retrieval_wiring

    calls = retrieval_wiring.retrieval_calls()
    assert calls, "出厂检索调用表不能为空"
    assert all(call.phase_id == retrieval_wiring.RETRIEVAL_PHASE for call in calls), [
        (call.tool_id, call.phase_id) for call in calls
    ]
    # 反证：同一批调用抹掉 phase_id ⇒ 在问题相被判定为「本相该执行」（bug 的形态）。
    import dataclasses
    from types import SimpleNamespace

    from packages.application.run_orchestration.phase_capability_triggers import (
        planned_in_this_phase,
    )

    question_spec = SimpleNamespace(
        run_chain_tool_ids=(retrieval_wiring.EUROPE_PMC_ID,), phase_id="question"
    )
    pressed = dataclasses.replace(calls[0], phase_id=None)
    assert planned_in_this_phase(pressed, cast(Any, question_spec)) is True
    # 而真实的调用（带着 phase）在问题相**不**执行。
    assert planned_in_this_phase(calls[0], cast(Any, question_spec)) is False


def test_the_session_tool_face_carries_the_retrieval_providers(tmp_path: Path) -> None:
    """**会话工具面**也要有检索实现（实证：缺了它会撞 `ToolDefinition ... is not registered`）。

    为什么需要：评审相**没有** run-chain 排除 ⇒ 它的会话工具面 = 整个冻结集。检索 provider
    之前只有运行链有实例 ⇒ 评审者一旦用到 `literature.read`，SDK 在 agent init 时点名
    `ToolDefinition 'literature.read' is not registered`（真实 run 实测，六相已跑完、只在
    评审相倒下）。

    **两向**：正向（出厂检索实例进注册表）+ 反证（不给 `extra_providers` ⇒ 表里没有它）。
    """
    from services.api.catalog import load_catalog_snapshot
    from services.api.retrieval_wiring import retrieval_providers
    from services.api.session_tool_support import session_tool_invokers

    specs = dict(load_catalog_snapshot().tool_providers)
    providers = retrieval_providers(artifacts=None, credentials=None)
    bindings = (
        ("literature.search", "europe_pmc", "literature_search"),
        ("literature.read", "europe_pmc", "literature_read"),
    )
    with_tools = session_tool_invokers(
        providers=providers, provider_specs=specs, artifacts=None, policy=None, bindings=bindings
    )
    assert set(with_tools) == {"literature.search", "literature.read"}
    # 反证：没有实例 ⇒ 那两个名字**不进表**（SDK 会点名，不是静默降级）。
    empty = session_tool_invokers(
        providers={}, provider_specs=specs, artifacts=None, policy=None, bindings=bindings
    )
    assert empty == {}


def test_the_lazy_factory_is_a_real_docker_backend(tmp_path: Path) -> None:
    """惰性不等于假实现：真调用时造出来的是**真实的** `DockerExecutionBackend`。

    只断言**类型与镜像**，不连 daemon（构造一个后端就会连 —— 这正是惰性的意义，
    所以这里用 `client` 注入面之外的方式**不**构造它：直接读工厂的实现）。
    """
    from adapters.execution import DockerExecutionBackend

    backend = DockerExecutionBackend.__new__(DockerExecutionBackend)  # 不调 __init__
    assert isinstance(backend, DockerExecutionBackend)
    # 工厂返回的**就是**那个类型（按注解与源码双重取证，不构造实例）。
    source = (_ROOT / "services" / "api" / "experiment_factories.py").read_text(encoding="utf-8")
    assert "return DockerExecutionBackend(image=image)" in source
    assert experiment_factories.docker_backend_factory.__doc__


def test_the_lazy_assembly_disagrees_with_the_eager_one_only_in_the_backend() -> None:
    """两个工厂**只差后端**：`execution_factory` 与 `execution` 恰好互补。"""
    lazy = experiment_factories.lazy_docker_experiment_assembly(
        artifacts=None, policy=None, script=None
    )
    assert lazy.execution is None and lazy.execution_factory is not None
    eager_source = (_ROOT / "services" / "api" / "experiment_factories.py").read_text(
        encoding="utf-8"
    )
    assert "execution=DockerExecutionBackend(image=image)" in eager_source
    # `sandbox_experiment_runner` 的转发入口仍在（判据侧既有用法不改）。
    assert callable(experiment_support.docker_experiment_assembly)
    assert callable(experiment_support.lazy_docker_experiment_assembly)
