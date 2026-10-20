"""GOAL-20261020-091 EC-02：**被评对象进评审者的提示词**（且只对评审者、有界、同源）。

**它咬住的缺口（建档实测）**：`cross_phase_evidence` 把上游产物登记成**证据**，但会话的
唯一出站消息是 `compose_prompt(purpose, direction, prior_knowledge, retrieval)` ——
被评对象**不进提示词**。对一批评审者，这意味着两位看到的都只是**合约 purpose** ⇒
它们评的**不是同一件东西**（各自想象的被评对象不同）。「两个模型在同一产物上判出不同
结论」因此即便配置上模型不同，也不是同一道题的两个答案。

**五条读数（成对）**：

1. **有被评对象 ⇒ 那一段在提示词里**：标题在场、产物名在场、内容摘要在场；
2. **没有 ⇒ 没有那一段**：`compose_prompt(...) == purpose`（**逐字**，零回归）；
3. **只给评审者**：`review_panel_role` 不是 `REVIEWER` 的 role ⇒ 不挂（`with_review_material`
   原样返回 —— 那件产物对它是**输入**，不是**被评对象**）；
4. **有界 + 截断可见**：超长正文被截到上限并**标注**；摘要算的是**展示出去的字节**
   （截断后也一样），因此读面能把提示词与落库制品对上；
5. **信封解包同源**：真实交付物是信封（正文在 `content` 里）⇒ 那一段展示的是**模型声明的
   那份对象**，不是信封的元数据（`conversation_id` 之类不该出现在被评对象里）。

判据只读**装配结果 + 渲染文本**（纯函数），不起会话；会话创建点那一段由
`compose_prompt` 的同一条路径承担（`test_prior_knowledge_in_prompt.py` 同一手法）。
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.retrieval_prompt import (
    REVIEW_MATERIAL_SECTION_TITLE,
    TRUNCATED_MARK,
    compose_prompt,
    render_review_material_prompt,
)
from packages.application.run_orchestration.review_material import (
    DEFAULT_MAX_CHARS,
    ReviewMaterialView,
    build_review_material,
    with_review_material,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import ActivationPolicy, ModelBindingMode, ReviewPanelRole, RoleCategory
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask

_PURPOSE = "TASK — judge the research plan you were given."
_RUN_ID = "11111111-1111-4111-8111-111111111111"
_PHASE = "author"
_NAME = "research_plan"
#: `ID` 只收 UUID（判别 id 的既有约束）⇒ 任务 id 用真 UUID，制品 id 按
#: `{task_id}:{artifact_name}` 拼（与产品路径同一条形态）。
_TASK_ID = "aaaaaaaa-0000-4000-8000-000000000001"
_ARTIFACT_ID = f"{_TASK_ID}:{_NAME}"


class _Workflow:
    """最小 `WorkflowEngine` 面：只需 `task_identities`（跨相解析用）。

    它不是 `WorkflowEngine` 的实现 —— 判据只需要那一个方法。类型上的代价由
    `_workflow()` 一处 `cast` 承担（装配器签名保持真实 Port 类型，不放宽）。
    """

    def __init__(self, task_id: str = _TASK_ID) -> None:
        self._task_id = task_id

    def task_identities(self, run_id: str) -> tuple[Any, ...]:
        return (_Identity(self._task_id, f"{run_id}:{_PHASE}:author_a"),)


class _Identity:
    def __init__(self, task_id: str, key: str) -> None:
        self.task_id = task_id
        self.idempotency_key = key


class _Reader:
    """评审者（`review_panel_role = REVIEWER`）与检索者（`NONE`）各一份 role。"""

    def __init__(self, role: RoleDefinition) -> None:
        self.role = role


def _role(panel_role: ReviewPanelRole) -> RoleDefinition:
    return RoleDefinition(
        id="scientific_reviewer" if panel_role is ReviewPanelRole.REVIEWER else "domain_researcher",
        role_type="ScientificReviewer",
        category=RoleCategory.EVALUATION,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        review_panel_role=panel_role,
    )


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID(_TASK_ID),
        run_id=ID(_RUN_ID),
        contract_id="review_scored_deliverable",
        assigned_agent_id="reviewer_a",
        status="CREATED",
        idempotency_key=f"{_RUN_ID}:review:reviewer_a",
    )


def _bytes(payload: Any) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _store(payload: Any) -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = _bytes(payload)
    store.put(
        Artifact(
            id=_ARTIFACT_ID,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="agent:author_a",
        ),
        content,
    )
    return store


def _declared() -> tuple[tuple[str, str, Any], ...]:
    from packages.domain.enums import TrustLabel

    return ((_PHASE, _NAME, TrustLabel.GENERATED),)


def _workflow() -> Any:
    """`build_review_material` 的 workflow 参数（替身经此处一次 `cast`）。"""
    from typing import cast

    return cast(Any, _Workflow())


def _view(shown_object: dict[str, Any] | None = None, *, max_chars: int = DEFAULT_MAX_CHARS) -> Any:
    payload = shown_object or {"research_plan": {"question": "q", "hypothesis": "h"}}
    return build_review_material(
        _workflow(), _store(payload), _task(), _declared(), max_chars=max_chars
    )


def test_the_artifact_under_review_is_in_the_prompt() -> None:
    """① 有被评对象 ⇒ 那一段在提示词里（标题 / 产物名 / 内容摘要 / 正文）。"""
    view = _view()
    prompt = compose_prompt(_PURPOSE, review_material=view)
    assert REVIEW_MATERIAL_SECTION_TITLE in prompt, prompt
    assert _NAME in prompt, prompt
    assert view.entries[0].digest in prompt, prompt
    assert '"question": "q"' in prompt, prompt
    # 与既有三段**并列**：那三段缺席时提示词仍以 purpose 开头（不替换）。
    assert prompt.startswith(_PURPOSE), prompt


def test_without_the_artifact_the_prompt_is_byte_identical() -> None:
    """② 没有 ⇒ 没有那一段（**逐字**返回 purpose —— 零回归）。"""
    assert compose_prompt(_PURPOSE) == _PURPOSE
    assert compose_prompt(_PURPOSE, review_material=ReviewMaterialView(entries=())) == _PURPOSE
    assert render_review_material_prompt(ReviewMaterialView(entries=())) == ""


def test_the_envelope_is_unwrapped_and_its_metadata_stays_out() -> None:
    """⑤ 信封形态：展示**模型声明的那份对象**，不是信封的元数据。"""
    envelope = {
        _NAME: {
            "content": '```json\n{"research_plan": {"question": "q1", "hypothesis": "h1"}}\n```',
            "message_count": 1,
            "conversation_id": "conv-should-not-appear",
            "session_id": "sess-1",
            "fact_name": "session_message",
            "declared_artifact": _NAME,
            "contract_id": "research_report_plan",
        }
    }
    view = _view(envelope)
    prompt = compose_prompt(_PURPOSE, review_material=view)
    assert '"question": "q1"' in prompt, prompt
    assert "conv-should-not-appear" not in prompt, prompt


def test_the_excerpt_is_bounded_and_the_truncation_is_visible() -> None:
    """④ 有界 + 截断可见：超限被截并标注；摘要算的是**展示出去的字节**。"""
    big = {"research_plan": {"question": "q" * 400}}
    small = _view(big, max_chars=50)
    entry = small.entries[0]
    assert entry.truncated is True
    assert len(entry.shown) == 50
    assert entry.digest == str(Digest.of_bytes(entry.shown.encode("utf-8")))
    prompt = compose_prompt(_PURPOSE, review_material=small)
    assert TRUNCATED_MARK in prompt, prompt

    whole = _view(big)
    assert whole.entries[0].truncated is False
    assert whole.entries[0].digest != entry.digest, "截断前后是两个不同的内容事实"


def test_only_a_reviewer_gets_the_excerpt() -> None:
    """③ 只给评审者：非 `REVIEWER` 的 role ⇒ **同一个对象**返回（连替换都不发生）。"""
    spec = _identity_spec(_role(ReviewPanelRole.NONE))
    assert with_review_material(_Deps(), _task(), spec) is spec


def _identity_spec(role: RoleDefinition) -> Any:
    """真实的 `SessionSpecContext`（`replace()` 需要真 dataclass；替身做不到）。"""
    from packages.application.run_orchestration.task_executor import SessionSpecContext

    return SessionSpecContext(
        role=role,
        agent=AgentSpec(
            id="reviewer_a",
            role="scientific_reviewer",
            model_binding=AgentBinding(mode=ModelBindingMode.INHERIT),
        ),
        frozen_manifest_digest="digest",
        cross_phase_inputs=_declared(),
    )


class _Deps:
    """`review_material` 装配器（装配方身份；与生产组合根同一签名）。"""

    def review_material(self, task: ResearchTask, declared: Any) -> ReviewMaterialView:
        return build_review_material(
            _workflow(), _store({"research_plan": {"q": "x"}}), task, declared
        )


def test_with_review_material_replaces_the_slot_for_a_reviewer() -> None:
    """③（正向臂）评审者：槽位被填上；且**是**那个视图（不是空壳）。"""
    spec = _identity_spec(_role(ReviewPanelRole.REVIEWER))
    updated = with_review_material(_Deps(), _task(), spec)
    assert updated is not spec, "评审者必须拿到带被评对象的新 spec"
    assert updated.review_material is not None
    prompt = compose_prompt(_PURPOSE, review_material=updated.review_material)
    assert REVIEW_MATERIAL_SECTION_TITLE in prompt, prompt


def test_with_review_material_leaves_a_non_reviewer_untouched() -> None:
    """③（反证臂）非评审者 ⇒ **同一个对象**（内容相同也不行：调用点要能分辨「没挂」）。"""
    spec = _identity_spec(_role(ReviewPanelRole.NONE))
    assert with_review_material(_Deps(), _task(), spec) is spec


def test_a_missing_assembly_leaves_everything_untouched() -> None:
    """未接装配器 ⇒ 原样（既有装配语义逐字不变）。"""
    spec = _identity_spec(_role(ReviewPanelRole.REVIEWER))
    assert with_review_material(object(), _task(), spec) is spec


def test_an_unreadable_artifact_is_named_not_swallowed() -> None:
    """解不出 ⇒ **点名**（「读不到」不得被读成「没有可评的东西」）。"""
    with pytest.raises(InvalidInputError, match="did not emit it"):
        build_review_material(_workflow(), FakeArtifactStore(), _task(), _declared())
    store = FakeArtifactStore()
    raw = b"not json"
    store.put(
        Artifact(
            id=_ARTIFACT_ID,
            digest=Digest.of_bytes(raw),
            size_bytes=len(raw),
            media_type="application/json",
            created_by="agent:author_a",
        ),
        raw,
    )
    with pytest.raises(InvalidInputError, match="not valid JSON"):
        build_review_material(_workflow(), store, _task(), _declared())


def test_the_section_comes_after_the_three_existing_sections() -> None:
    """顺序纪律：被评对象在**最后**（紧贴它要给的判词），前三段相对顺序不变。"""
    prompt = compose_prompt(
        _PURPOSE,
        direction="study retrieval",
        review_material=_view(),
    )
    assert prompt.index("PROJECT DIRECTION") < prompt.index(REVIEW_MATERIAL_SECTION_TITLE)
    assert prompt.index(_PURPOSE) < prompt.index(REVIEW_MATERIAL_SECTION_TITLE)


def test_the_view_is_immutable_and_round_trips() -> None:
    """视图是可比较的冻结值（装配结果不该在传递途中被改）。"""
    first = _view()
    second = _view()
    assert first == second
    with pytest.raises(Exception):
        first.entries = ()
    replaced = replace(first, entries=())
    assert replaced.empty is True


def test_a_rendered_section_string_survives_the_composer() -> None:
    """**缝合线判据**（GOAL-091 实测到的既有缺陷）：`SessionBuilder` 提交的是**已渲染**的
    `str`，而 `compose_prompt` 若只按**视图对象**渲染，就会把那一段静默丢弃。

    实测读数（真实 run）：reviewer 会话收到的提示词里 `UNDER REVIEW` 段整个不见 ——
    两位模型都如实报告「段不存在」。同一条缝对**检索段 / 前序段一直存在**
    （`render_retrieval_prompt("<已渲染的 str>")` 去找 `entries` 属性、拿不到 ⇒ 空串）。

    本判据钉住「两种形态都认」：空串 / `None` 仍逐字不变，非空字符串**原样**拼在后面。
    """
    from packages.application.run_orchestration.retrieval_prompt import (
        PRIOR_SECTION_TITLE,
        PROMPT_SECTION_TITLE,
    )

    retrieval = f"{PROMPT_SECTION_TITLE}\n\n- 41408154: a title\n"
    prior = f"{PRIOR_SECTION_TITLE}\n\n- mem-1: learned earlier\n"
    review = (
        f"{REVIEW_MATERIAL_SECTION_TITLE}\n\n- research_plan (content digest: sha256:abc):\n{{}}\n"
    )

    text = compose_prompt(
        _PURPOSE, prior_knowledge=prior, retrieval=retrieval, review_material=review
    )
    for section in (PRIOR_SECTION_TITLE, PROMPT_SECTION_TITLE, REVIEW_MATERIAL_SECTION_TITLE):
        assert section in text, (section, text)
    # 三段都出现了，且**顺序**是「前序 → 检索 → 被评对象」。
    assert (
        text.index(PRIOR_SECTION_TITLE)
        < text.index(PROMPT_SECTION_TITLE)
        < text.index(REVIEW_MATERIAL_SECTION_TITLE)
    )
    # 空串 / None 一律**逐字**返回 purpose（零回归）。
    assert (
        compose_prompt(_PURPOSE, retrieval="", prior_knowledge="", review_material="") == _PURPOSE
    )
    assert compose_prompt(_PURPOSE, retrieval=None, review_material=None) == _PURPOSE
