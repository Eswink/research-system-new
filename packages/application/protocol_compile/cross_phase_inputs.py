"""**跨相输入**的编译期解析（GOAL-20261016-081 EC-04）。

**它补哪一格**：`ProtocolPhase.inputs` 今天只认**组合根种入**的制品 id（`input-brief:…`），
而 run 内制品的真 id 是 `{task_id}:{artifact_name}` —— 任务 id 在**编排期**才生成 ⇒
协议里写不死「读上游 phase 的产物」。实测（`evidence/GOAL-20261016-081-ec04-evidence.txt`）：
在 `plan` 的 `inputs` 里写 `scouting_report` ⇒ 运行期
`declared input artifact scouting_report is not in the artifact store`。

**形态**（本模块是编译期的唯一解释点）：`inputs` 里出现 `{phase_id}:{artifact_name}` ⇒
它是**跨相引用**，指向该上游 phase 声明的产物名。编译期把它拆成 `(phase_id, artifact_name)`；
**运行期**再按 canonical 的任务身份解析成真实的 `{task_id}:{artifact_name}`
（任务 id 只有那时才知道；见 `orchestration/cross_phase_inputs.py`）。

**编译期必须点名**（不留到运行期 —— 运行期才发现等于让协议带着一个必死的 run 过 preflight）：

1. 两段都非空（`:` 恰好一个且两侧非空）；
2. 产出方 phase 存在，且**不是自己**；
3. 产出方是**自己的上游**（沿 `depends_on` 可达）—— 否则执行顺序保证不了产物在场；
4. 该产物名在产出方的 `outputs` 里 —— 否则读的是「产出方从不承诺的东西」；
5. 产出方**唯一**（多个 phase 声明同名产物 ⇒ 引用歧义）；
6. 读取方的执行体**真的消费声明输入** —— 报告汇编器今天不读 `declared_input_artifacts`，
   为它放行一条跨相输入会让「声明了输入」与「输入真的被读过」分叉，而覆盖门数的是来源
   ⇒ 缺口会被掩蔽。这一点用**契约声明**判（`report` / `experiment` 两个执行体声明位），
   不写死合约 id。

**与既有 `inputs` 的口径关系**：不含冒号的项**原样**留在 `CompiledPhase.inputs`
（组合根种入那一类，`test_declared_input_sources.py` 的四条判据逐字不变）。
两类可以并存 —— 它们指向的来源类别不同（外部供应 vs 本 run 上游产物）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports import CatalogSnapshot
from packages.domain.enums import TrustLabel
from packages.domain.protocols import (
    CapabilityExecution,
    CompileFindingCode,
    FindingSeverity,
    PreflightFinding,
    ProtocolDefinition,
    ProtocolPhase,
)

#: 跨相引用的分隔符（`{phase_id}:{artifact_name}`）。
SEPARATOR = ":"

#: 组合根**种入**的输入前缀（`services/api/demo.DECLARED_INPUTS` 是这些 id 的登记面）。
#: 只有这两个命名空间里的冒号项算本地输入；其余 `a:b` 一律按**跨相引用**解析并点名。
LOCAL_INPUT_PREFIXES: tuple[str, ...] = ("input-brief", "input-corpus")


@dataclass(frozen=True, slots=True)
class CrossPhaseInput:
    """一条**已解析**的跨相输入：谁产出、产出什么、它是什么**性质**。"""

    producer_phase_id: str
    artifact_name: str
    #: 来源性质，**由产出方决定**（本 EC 的硬要求 b）。见 `_producer_trust_label`。
    trust_label: TrustLabel


@dataclass(frozen=True, slots=True)
class CrossPhaseResolution:
    """一次编译的跨相输入解析结果（phase id → 它引用的上游产物，按声明顺序）。"""

    by_phase: dict[str, tuple[CrossPhaseInput, ...]]
    findings: tuple[PreflightFinding, ...] = ()

    def for_phase(self, phase_id: str) -> tuple[CrossPhaseInput, ...]:
        return self.by_phase.get(phase_id, ())


def is_cross_phase_reference(protocol: ProtocolDefinition, reference: str) -> bool:
    """该 `inputs` 项是不是**跨相引用**（判定依赖协议本身，不只看形态）。

    判定规则（两条，且必须**区分得开**组合根供给的 `input-brief:real_research_v1`）：

    1. **左段是协议里某个 phase 的 id** ⇒ 它是跨相引用（拼错也不行 —— 见下一条）；
    2. 否则**右段是某个 phase 声明的产物名**（`outputs`）⇒ **同样是**跨相引用，
       且左段必须是一个真实 phase ——「产物名对上了、产出方写错」是最容易犯的错，
       把它当成本地输入会静默放行一个**读不到**的声明。

    两条都不命中 ⇒ 本地输入（组合根种入那一类；形如 `input-brief:*` 的命名
    永远不可能是 phase id，因此第 1 条不会误伤）。
    """
    if reference.count(SEPARATOR) != 1:
        return False
    left, _, right = reference.partition(SEPARATOR)
    if not left or not right:
        return False
    if left in {phase.id for phase in protocol.phases}:
        return True
    if any(right in phase.outputs for phase in protocol.phases):
        return True
    # GOAL-20261019-089 EC-01（第 3 条）：**两段都是名字但两段都不是本协议的相位/产物**
    # ⇒ 同样是跨相引用（悬空），由 `_structural_failure` **点名**。
    #
    # 为什么必须这样（否则「摘掉上游」会被静默降级）：`inputs` 的本地那一类**只有**
    # `input-brief:` / `input-corpus:` 两个命名空间（组合根种入，`services/api/demo.py`
    # 的 `DECLARED_INPUTS` 是唯一登记面）。把 `question:research_question` 当本地输入
    # ⇒ 编译期不报，运行期在 **A 不在场**时点名 —— 那就成了「运行期才发现」，
    # 而且若恰好有同名本地输入，它会**静默取到别的东西**（正是本 EC 要消灭的分支）。
    return not is_local_input_namespace(left)


def is_local_input_namespace(prefix: str) -> bool:
    """组合根种入的那一类前缀（唯一登记面 = `services/api/demo.DECLARED_INPUTS`）。"""
    return prefix in LOCAL_INPUT_PREFIXES


def _error(message: str, subject: str) -> PreflightFinding:
    return PreflightFinding(
        CompileFindingCode.CROSS_PHASE_INPUT_INVALID.value,
        FindingSeverity.ERROR,
        message,
        subject,
    )


def _ancestors(protocol: ProtocolDefinition, phase_id: str) -> set[str]:
    """该 phase 的**全部上游** phase id（沿 `depends_on` 传递闭包）。"""
    by_id = {phase.id: phase for phase in protocol.phases}
    seen: set[str] = set()
    stack = list(by_id[phase_id].depends_on) if phase_id in by_id else []
    while stack:
        current = stack.pop()
        if current in seen or current not in by_id:
            continue
        seen.add(current)
        stack.extend(by_id[current].depends_on)
    return seen


def _producers_of(protocol: ProtocolDefinition, artifact_name: str) -> tuple[str, ...]:
    """声明产出该产物名的 phase（按协议声明顺序）。"""
    return tuple(phase.id for phase in protocol.phases if artifact_name in phase.outputs)


def _executor_consumes_declared_inputs(phase: ProtocolPhase, catalog: CatalogSnapshot) -> bool:
    """该 phase 的执行体**真的**消费声明输入（今天：报告汇编器不消费）。

    判据来自**契约声明位**（不是合约 id 的字面量）：
    - `report` 非空 ⇒ 执行体是报告汇编器 ⇒ 它的准入面只读 canonical 的 run / 证据 /
      指标 / 判词，**不读** `declared_input_artifacts`；
    - `experiment` 非空 ⇒ 沙箱实验 ⇒ 同样不读（实验参数由 `experiment` 声明与计划派生的
      设计块给出）；
    - 两者都缺 ⇒ 会话执行体，它**会**把声明输入登记成来源（`register_session_result`）。
    """
    for contract_id in phase.task_contracts:
        contract = catalog.task_contracts.get(contract_id)
        if contract is None:
            continue
        if contract.report is not None or contract.experiment is not None:
            return False
    return True


def _structural_failure(
    protocol: ProtocolDefinition, phase: ProtocolPhase, producer_phase_id: str, artifact_name: str
) -> PreflightFinding | None:
    """引用**结构面**的校验（自己 / 未知 / 非上游 / 未声明产物 / 歧义）。"""
    subject = f"phase:{phase.id}"
    phase_ids = {item.id for item in protocol.phases}
    if producer_phase_id == phase.id:
        return _error(
            f"phase {phase.id} declares its own output {artifact_name!r} as an input",
            subject,
        )
    if producer_phase_id not in phase_ids:
        return _error(
            f"phase {phase.id} declares input from unknown phase {producer_phase_id!r}"
            f" (expected {artifact_name!r} produced by a declared phase)",
            subject,
        )
    if producer_phase_id not in _ancestors(protocol, phase.id):
        return _error(
            f"phase {phase.id} declares input from {producer_phase_id}, which is not upstream"
            " of it (execution order cannot guarantee the artifact exists)",
            subject,
        )
    producers = _producers_of(protocol, artifact_name)
    if producer_phase_id not in producers:
        return _error(
            f"phase {producer_phase_id} does not declare output {artifact_name!r}"
            f" (it declares {list(_declared_outputs(protocol, producer_phase_id))})",
            subject,
        )
    if len(producers) > 1:
        return _error(
            f"input {artifact_name!r} of phase {phase.id} is ambiguous:"
            f" declared as output by {list(producers)}",
            subject,
        )
    return None


def producer_trust_label(
    protocol: ProtocolDefinition,
    producer_phase_id: str,
    catalog: CatalogSnapshot,
) -> TrustLabel:
    """**产出方 phase 的来源性质**（本 EC 的硬要求 b：性质不由读取方自报）。

    判据 = 产出方**真的会打到系统之外**，两个条件同时成立（与
    `phase_capabilities._trust_label_for` 同一口径，只是提前到编译期算）：

    1. 它声明 `capability_execution: run_chain`（能力由**运行链**执行，不是交给模型）；
    2. 它需要的某个 provider 在目录里声明了 `network_domains`（`execute_tool_call` 的
       URL 策略正是按这份声明在触网前判的）。

    ⇒ `RETRIEVED`；否则 `GENERATED`（**不**自称「系统取得」：一个只会写字的 phase
    产出的报告不能被下游当成检索来源）。
    """
    phase = next((item for item in protocol.phases if item.id == producer_phase_id), None)
    if phase is None or phase.capability_execution is not CapabilityExecution.RUN_CHAIN:
        return TrustLabel.GENERATED
    for capability in sorted(phase.required_capabilities):
        for provider in catalog.tool_providers.values():
            if capability in provider.capabilities and provider.network_domains:
                return TrustLabel.RETRIEVED
    return TrustLabel.GENERATED


def _resolve_one(
    protocol: ProtocolDefinition,
    phase: ProtocolPhase,
    reference: str,
    catalog: CatalogSnapshot,
) -> tuple[CrossPhaseInput | None, PreflightFinding | None]:
    """单条引用的校验（返回 `(解析结果, 失败 finding)`，二者恰有一个非空）。"""
    producer_phase_id, _, artifact_name = reference.partition(SEPARATOR)
    failure = _structural_failure(protocol, phase, producer_phase_id, artifact_name)
    if failure is not None:
        return None, failure
    if not _executor_consumes_declared_inputs(phase, catalog):
        return None, _error(
            f"phase {phase.id} declares cross-phase input {reference!r}, but its executor"
            " does not consume declared inputs (report/experiment executors read canonical"
            " facts only) -- the declaration would be a source the gate counts and nobody reads",
            f"phase:{phase.id}",
        )
    return (
        CrossPhaseInput(
            producer_phase_id=producer_phase_id,
            artifact_name=artifact_name,
            trust_label=producer_trust_label(protocol, producer_phase_id, catalog),
        ),
        None,
    )


def _declared_outputs(protocol: ProtocolDefinition, phase_id: str) -> tuple[str, ...]:
    phase = next((item for item in protocol.phases if item.id == phase_id), None)
    return tuple(phase.outputs) if phase is not None else ()


def resolve_cross_phase_inputs(
    protocol: ProtocolDefinition,
    catalog: CatalogSnapshot,
) -> CrossPhaseResolution:
    """`inputs` 的跨相引用 → `(产出方, 产物名)` + **编译期点名的** findings。"""
    by_phase: dict[str, tuple[CrossPhaseInput, ...]] = {}
    findings: list[PreflightFinding] = []
    for phase in protocol.phases:
        resolved: list[CrossPhaseInput] = []
        for reference in phase.inputs:
            if not is_cross_phase_reference(protocol, reference):
                continue
            item, failure = _resolve_one(protocol, phase, reference, catalog)
            if failure is not None:
                findings.append(failure)
                continue
            assert item is not None
            resolved.append(item)
        if resolved:
            by_phase[phase.id] = tuple(resolved)
    return CrossPhaseResolution(by_phase=by_phase, findings=tuple(findings))


def local_inputs(protocol: ProtocolDefinition, phase: ProtocolPhase) -> tuple[str, ...]:
    """该 phase `inputs` 里的**组合根种入**那一类（不含跨相引用）。"""
    return tuple(item for item in phase.inputs if not is_cross_phase_reference(protocol, item))


__all__ = [
    "SEPARATOR",
    "CrossPhaseInput",
    "CrossPhaseResolution",
    "is_cross_phase_reference",
    "local_inputs",
    "producer_trust_label",
    "resolve_cross_phase_inputs",
]
