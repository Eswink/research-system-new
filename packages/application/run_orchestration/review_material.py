"""**被评对象** → 评审者提示词的一段（GOAL-20261020-091 EC-02）。

**它补哪一格**：`cross_phase_evidence` 把上游产物登记成**证据**（落 canonical、进覆盖门），
但**不进提示词** —— 会话的唯一出站消息是
`compose_prompt(purpose, direction, prior_knowledge, retrieval)`。对一批评审者，这意味着
每一位看到的都只是**合约 purpose**，而「要评的那件东西」只在证据链里 ⇒ 两位评审模型
**评的不是同一件东西**（它们各自想象的被评对象不同）。「两个模型在同一产物上判出不同
结论」因此即便配置上模型不同，也不是同一道题的两个答案。

**四条边界**（逐条可判）：

1. **只收声明过的跨相输入**：材料来自 `SessionSpecContext.cross_phase_inputs`
   （编译期已校验「产出方是自己的上游 / 该产物在它的 `outputs` 里」）—— 不扫全库、
   不按名字猜「哪一件像被评对象」；
2. **只给评审者**：`RoleDefinition.review_panel_role is REVIEWER` 才挂这一段。
   非评审 phase（例如读上游问题的检索格）提示词**逐字节**不变 —— 那件产物对它是
   **输入**，不是**被评对象**，两种语义混在一段里会让「它在评什么」不可读；
3. **有界 + 截断可见**（§10）：正文按字符上限截断并**逐条标注**；不把完整正文塞进会话；
4. **同源**：`shown` 是**展示出去的字节**，`digest` 是**这些字节**的内容摘要 ——
   读面据此能把「模型看到的」与「落库的那份制品」对上（不重读第二遍原文）。

**信封形态**（与运行链参数材料同一口径）：真实会话交付物是
`{declared_artifact: {content: "…"}}`，模型声明的那份对象在**正文**里 ⇒ 用既有
`declared_object` 解包（**不**在这里写第二份解析）。解不出来 ⇒ **点名**（不静默给空段：
「读不到」与「没有」必须分得开）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.run_orchestration.cross_phase_inputs import producer_task_id
from packages.application.run_orchestration.phase_input_material import declared_object
from packages.domain.core import Digest
from packages.domain.enums import ReviewPanelRole

if TYPE_CHECKING:  # 只为类型：避免与 task_executor 形成导入环
    from packages.application.run_orchestration.task_executor import SessionSpecContext

#: 逐条正文的**字符**上限（§10 的有界口径：内容进提示词但不进完整正文）。
DEFAULT_MAX_CHARS = 2000


@dataclass(frozen=True, slots=True)
class ReviewMaterialEntry:
    """一件**被评对象**（有界摘录 + 它是谁的哪件产物）。"""

    producer_phase_id: str
    artifact_name: str
    artifact_id: str
    #: 展示给模型的那段文本（**已截断**；超限见 `truncated`）。
    shown: str
    truncated: bool
    #: `shown` 这些字节的内容摘要（读面据此与落库制品对齐）。
    digest: str


@dataclass(frozen=True, slots=True)
class ReviewMaterialView:
    """一次装配的结果（逐条）。空元组 = 没有可评的对象（该 phase 不声明跨相输入）。"""

    entries: tuple[ReviewMaterialEntry, ...]

    @property
    def empty(self) -> bool:
        return not self.entries


def is_reviewer(spec_context: "SessionSpecContext") -> bool:
    """本 phase 的 role 是否是**评审者**（`review_panel_role` 是域里的既有概念）。"""
    return spec_context.role.review_panel_role is ReviewPanelRole.REVIEWER


def build_review_material(
    workflow: WorkflowEngine | None,
    artifacts: ArtifactStore,
    task: Any,
    declared: tuple[tuple[str, str, Any], ...],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> ReviewMaterialView:
    """本 phase 声明的跨相输入 → 被评对象的**有界摘录**（只读 canonical；零出网）。"""
    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    if not declared:
        return ReviewMaterialView(entries=())
    if workflow is None:
        raise InvalidInputError(
            f"phase of task {task.id.value} declares cross-phase inputs, but this assembly"
            " provides no workflow engine to resolve the producer task identity"
        )
    entries: list[ReviewMaterialEntry] = []
    for producer_phase_id, artifact_name, _trust_label in declared:
        producer_task = producer_task_id(workflow, task, producer_phase_id)
        artifact_id = f"{producer_task}:{artifact_name}"
        payload = _object_of(artifacts, artifact_id, artifact_name)
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        shown, truncated = _clip(text, max_chars)
        entries.append(
            ReviewMaterialEntry(
                producer_phase_id=producer_phase_id,
                artifact_name=artifact_name,
                artifact_id=artifact_id,
                shown=shown,
                truncated=truncated,
                digest=str(Digest.of_bytes(shown.encode("utf-8"))),
            )
        )
    return ReviewMaterialView(entries=tuple(entries))


def _object_of(artifacts: ArtifactStore, artifact_id: str, artifact_name: str) -> Any:
    """制品 → **模型声明的那份对象**（缺件 / 不是 JSON / 解不出 ⇒ 点名）。"""
    if artifacts.meta(artifact_id) is None:
        raise InvalidInputError(
            f"the artifact under review ({artifact_name}) is not in the artifact store as"
            f" {artifact_id} (the producer phase did not emit it)"
        )
    try:
        parsed = json.loads(artifacts.get(artifact_id).decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise InvalidInputError(
            f"the artifact under review {artifact_id} is not valid JSON: {error}"
        ) from error
    if not isinstance(parsed, dict):
        raise InvalidInputError(f"the artifact under review {artifact_id} is not a JSON object")
    # 落库制品的形状是 `{产物名: <载荷>}`（`result_handler._artifact_for_output` 按结构化
    # 输出的那个键命名）⇒ 先取下那一层；信封的判别键在**载荷**上，不在产物名那一层。
    payload = parsed.get(artifact_name)
    value = payload if isinstance(payload, Mapping) else parsed
    declared = declared_object(value, key=artifact_name)
    # 与 `phase_input_material.input_material` 同一取法：正文里的形状是
    # `{产物名: {...}}` ⇒ 取**内层**（不双挂）；直形态原样。
    inner = declared.get(artifact_name)
    return inner if isinstance(inner, Mapping) else declared


def _clip(text: str, limit: int) -> tuple[str, bool]:
    """按**字符**截断（超限 ⇒ `truncated=True`，不静默变短）。"""
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def with_review_material(deps: Any, task: Any, spec_context: "SessionSpecContext") -> Any:
    """把**被评对象**装进本任务的 spec（求值点与检索上下文同一处）。

    未接装配器（`deps.review_material is None`）⇒ **原样返回**（既有语义逐字节不变）；
    非评审 role ⇒ 原样返回（不声明即不挂）；装配器抛错 ⇒ 让异常冒到执行循环
    （那里的失败路径会点名 —— 不静默给一个空段）。
    """
    build = getattr(deps, "review_material", None)
    if build is None or not is_reviewer(spec_context):
        return spec_context
    from dataclasses import replace

    view = build(task, spec_context.cross_phase_inputs)
    return replace(spec_context, review_material=view)


__all__ = [
    "DEFAULT_MAX_CHARS",
    "ReviewMaterialEntry",
    "ReviewMaterialView",
    "build_review_material",
    "is_reviewer",
    "with_review_material",
]
