"""运行链调用的**参数材料**（自 `phase_capabilities.py` 拆出：规模门 + GOAL-089 EC-01）。

拆法与全仓一致（`phase_call_arguments.py` / `phase_capability_triggers.py` 同一手法）：
「取哪几份材料、怎么合并」与「执行循环 / 证据登记」分列。**原先的行为逐字保留**。

**本轮新增的那一格**（GOAL-20261019-089 EC-01）：GOAL-081 让 `inputs: [A:research_question]`
成为**声明**并把上游产物登记成证据 —— 但那条通道只进**证据链**：参数材料只扫
`spec.declared_input_artifacts`（本地输入）⇒ 上游产出**读不到**，`arguments_from_input`
必点名失败。本模块把已解析的跨相输入按**产物名**挂进同一份材料，于是
`arguments_from_input=("research_question.query",)` 对两种来源一视同仁。

**四条边界**（逐条可判）：

1. **只读 canonical**：`ArtifactStore` —— 不建会话、不发请求；
2. **解析用既有身份**：产出方任务 id 走 `cross_phase_inputs.producer_task_id`
   （idempotency key 的稳定身份），本模块**不**另写一套解析；
3. **fail-closed**：取不到 / 非对象 / **同名不同内容** ⇒ 点名；不回落、不「取后者」；
4. **零回归**：`cross_phase=()`（缺省）⇒ 与拆出前的实现**逐字节**相同。

**两种产物形态都认**（`declared_object`）：真会话的交付物是**信封**
（`content` = 模型正文），受控夹具给的是**直形态**（顶层就是对象）—— 与
`experiments/design_from_plan.design_block_in` 的两种形态识别同一纪律。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.run_orchestration.cross_phase_inputs import producer_task_id
from packages.domain.enums import TrustLabel
from packages.domain.tasks import ResearchTask

if TYPE_CHECKING:  # 只为类型：避免与 phase_capabilities 形成导入环
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps
    from packages.application.run_orchestration.task_executor import SessionSpecContext

#: 会话交付物**信封**里承载模型正文的那个键（`real_research_deliverable_v1`）。
ENVELOPE_CONTENT_KEY = "content"
#: 信封的判别键：只有真交付物才带它（直形态的载荷不会有）。
ENVELOPE_MARK_KEY = "declared_artifact"


@dataclass(frozen=True, slots=True)
class CrossPhaseMaterial:
    """一条**可作参数材料**的跨相输入（产物名 + 真实制品 id + 编译期性质）。

    性质原样取自 `CompiledPhase.cross_phase_inputs` 的第三项（由**产出方**决定），
    本类**不**重新推导 —— 两处各推一次必然漂。
    """

    producer_phase_id: str
    artifact_name: str
    artifact_id: str
    trust_label: TrustLabel


def resolve_cross_phase_material(
    workflow: WorkflowEngine | None,
    artifacts: ArtifactStore,
    task: ResearchTask,
    declared: tuple[tuple[str, str, TrustLabel], ...],
) -> tuple[CrossPhaseMaterial, ...]:
    """本 phase 的跨相输入 → 参数材料项（未声明 ⇒ `()`，缺件 ⇒ 点名）。

    `declared` 就是 `CompiledPhase.cross_phase_inputs`（编译期已校验结构面与性质）。
    声明了却没有解析面（`workflow is None`）⇒ **点名**，不静默当成「没有跨相输入」：
    那会让「声明了输入」与「输入真的被读过」分叉（本 EC 要消灭的正是这个分叉）。
    """
    if not declared:
        return ()
    if workflow is None:
        raise InvalidInputError(
            f"phase of task {task.id.value} declares cross-phase inputs, but this assembly"
            " provides no workflow engine to resolve the producer task identity"
        )
    items: list[CrossPhaseMaterial] = []
    for producer_phase_id, artifact_name, trust_label in declared:
        producer_task = producer_task_id(workflow, task, producer_phase_id)
        artifact_id = f"{producer_task}:{artifact_name}"
        if artifacts.meta(artifact_id) is None:
            raise InvalidInputError(
                f"cross-phase input {producer_phase_id}:{artifact_name} is not in the artifact"
                f" store as {artifact_id} (the producer phase did not emit it)"
            )
        items.append(
            CrossPhaseMaterial(
                producer_phase_id=producer_phase_id,
                artifact_name=artifact_name,
                artifact_id=artifact_id,
                trust_label=trust_label,
            )
        )
    return tuple(items)


def input_material(
    deps: "CapabilityDeps",
    spec: "SessionSpecContext",
    *,
    cross_phase: tuple[CrossPhaseMaterial, ...] = (),
) -> dict[str, object]:
    """本 phase 声明输入的 JSON 顶层字段合并成一份参数材料（缺件 ⇒ fail closed）。

    `cross_phase` 的每一项按**产物名**成为材料的一个顶层键（与本地声明输入的合并口径
    相同）—— 于是 `arguments_from_input` 的点分路径对两种来源写法一致。
    """
    material: dict[str, object] = {}
    for artifact_id in spec.declared_input_artifacts:
        payload = _json_object(deps.artifacts, artifact_id, label="declared input")
        material.update(payload)
    for item in cross_phase:
        payload = _json_object(deps.artifacts, item.artifact_id, label="cross-phase input")
        previous = material.get(item.artifact_name)
        if previous is not None and previous != payload:
            # 同名不同内容 ⇒ 参数材料有两个可能的意思 ⇒ 点名（不取后写的那个）。
            raise InvalidInputError(
                f"cross-phase input {item.artifact_name!r} collides with a local declared"
                " input of the same name and different content; the run-chain arguments"
                " would be undecidable"
            )
        # 解出来的是 `{产物名: 它声明的对象}` ⇒ 取**内层**挂到同名键下（不双挂）。
        declared = declared_object(payload, key=item.artifact_name)
        inner = declared.get(item.artifact_name)
        material[item.artifact_name] = inner if isinstance(inner, Mapping) else declared
    return material


def declared_object(payload: Mapping[str, Any], *, key: str | None = None) -> Mapping[str, Any]:
    """产物载荷 → **模型声明的那份对象**（信封形态解开，直形态原样）。

    只在**两个条件同时成立**时解开信封：载荷带 `declared_artifact`（真交付物才有的判别键）
    且 `content` 是字符串。任一不满足 ⇒ 原样返回（不猜、不模糊匹配）。

    `key` = **期望的顶层键**（= 产物名）。给了它 ⇒ 只认**带这个键**的 JSON 对象：
    真实正文里常常先有一段**示例**块（合约给的形状）再是答案块，不按期望键筛选就会
    取到示例（本轮真实 run 实测）。不给 ⇒ 取第一个可解析的对象（既有口径）。
    """
    if ENVELOPE_MARK_KEY not in payload:
        return payload
    content = payload.get(ENVELOPE_CONTENT_KEY)
    if not isinstance(content, str):
        return payload
    parsed = _json_in_text(content, key=key)
    if parsed is None:
        # 给了期望键却解不出来 ⇒ **点名**（不静默返回信封：那会让下游看到
        # `content` 而不是模型声明的那份对象，而错误会出现在更远的地方、指错方向）。
        # 形状用**字面量**给（GOAL-20261020-091：原先写在一个 f-string 的嵌套花括号里，
        # 那道表达式会被当成格式说明符 ⇒ 这条 fail-closed 分支自己抛 `ValueError`，
        # 于是「解不出来」被报成一个无关的格式化错误）。
        shape = "{'" + str(key) + "': {...}}"
        raise InvalidInputError(
            f"the producer's reply carries no JSON object with the key {key!r}"
            f" (expected a block like {shape} in the reply text)"
        )
    return parsed


def _json_in_text(text: str, *, key: str | None = None) -> Mapping[str, Any] | None:
    """正文 → JSON 对象（**整段**、或**任一**围栏块、或围栏块里的那一段）。

    **为什么要扫全部围栏块**（真实 run 实测）：模型的回复是「一段说明 + 若干 ```json
    块」，而其中第一个块可能只是**示例**（合约里给的形状），真正的答案在后面的块里。
    只取第一个 ⇒ 参数材料里没有那个名字 ⇒ 运行链点名失败（这正是本轮实测到的形态）。
    三种候选按**从具体到宽泛**的顺序取：整段 → 每个围栏块 → 围栏块里裸 JSON 段。
    """
    stripped = text.strip()
    candidates: list[str] = [stripped]
    candidates.extend(_fenced_blocks(stripped))
    # 整段里的裸 JSON 段也要扫：模型常把答案**不套围栏**地写在说明文字之后
    # （「裸块在前、围栏块在后」这种形态下只扫围栏会漏掉前者）。
    candidates.extend(_braced_segments(stripped))
    found: list[Mapping[str, Any]] = []
    for candidate in candidates:
        try:
            parsed: Any = json.loads(candidate)
        except ValueError:
            continue
        if not isinstance(parsed, Mapping):
            continue
        if parsed in found:
            continue
        found.append(parsed)
    if key is None:
        return found[0] if found else None
    # 带期望键的对象**优先**：合约要的形状是 `{产物名: {...}}`，它把自己与示例块区分开。
    keyed = [item for item in found if key in item]
    if len(keyed) > 1:
        # **多块都带期望键** ⇒ 取哪一块都是猜（示例块与答案块常同时在场）。
        # 与全仓「不猜、不取最后一条」同一纪律：点名，由产出方把正文写成**一块**。
        raise InvalidInputError(
            f"the producer's text carries {len(keyed)} distinct JSON objects for"
            f" {key!r}; the run-chain argument would be undecidable"
        )
    if keyed:
        return keyed[0]
    # 没有一个带期望键 ⇒ 只接受**唯一**的那份对象（直形态：正文就是产物本身）。
    # 多于一份 ⇒ 分不清哪份是答案（示例块与答案块都无键）⇒ 点名。
    if len(found) > 1:
        raise InvalidInputError(
            f"the producer's text carries {len(found)} distinct JSON objects and none of"
            f" them has the key {key!r}; the run-chain argument would be undecidable"
        )
    return found[0] if found else None


def _fenced_blocks(text: str) -> list[str]:
    """**全部** ``` 围栏的内容（无围栏 ⇒ 空列表；容忍 ```json 之类的语言标记）。"""
    pieces = text.split("```")
    blocks: list[str] = []
    # 奇数下标是围栏内部（0 是块外文字）。
    for index in range(1, len(pieces), 2):
        body = pieces[index]
        newline = body.find("\n")
        blocks.append(body[newline + 1 :] if newline != -1 else body)
    return blocks


def _braced_segments(body: str) -> list[str]:
    """围栏块里**以 `{` 开头、以 `}` 结尾**的最大片段（块里还夹着说明文字时用）。

    只做**括号配对**的粗切（不解析语法、不猜键名）：从每个 `{` 起找到配平的 `}`；
    字符串里的括号不算（`_string_state` 吃掉引号内的一切，含转义）。
    """
    segments: list[str] = []
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for index, char in enumerate(body):
        in_string, escaped, consumed = _string_state(char, in_string, escaped)
        if consumed:
            continue
        if char == "{":
            start = index if depth == 0 else start
            depth += 1
        elif char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                segments.append(body[start : index + 1])
    return segments


def _string_state(char: str, in_string: bool, escaped: bool) -> tuple[bool, bool, bool]:
    """(在串内, 待转义, 本字符已被引号面吃掉)；纯状态推进，不碰括号计数。"""
    if in_string:
        if escaped:
            return True, False, True
        if char == "\\":
            return True, True, True
        if char == '"':
            return False, False, True
        return True, False, True
    if char == '"':
        return True, False, True
    return False, False, False


def _json_object(artifacts: ArtifactStore, artifact_id: str, *, label: str) -> dict[str, object]:
    """制品字节 → JSON 对象（缺件 / 非对象 ⇒ 点名：不拿空材料去检索）。"""
    parsed = json.loads(artifacts.get(artifact_id).decode("utf-8"))
    if not isinstance(parsed, dict):
        raise InvalidInputError(f"{label} {artifact_id} is not a JSON object")
    return parsed


__all__ = [
    "CrossPhaseMaterial",
    "declared_object",
    "input_material",
    "resolve_cross_phase_material",
]
