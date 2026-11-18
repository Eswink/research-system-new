"""EC-03 ④：`UNDER REVIEW` 段在**真实拼装路径**上必须在场且非空。

**它补哪一格**（GOAL-20261119-115 建档实测）：`task_executor._run_session` 把
**已渲染好的 `str`** 放进 `AgentSessionSpec`，而 `SessionBuilder` 又把它交给
`compose_prompt` —— 只按**视图对象**渲染时，`render_review_material_prompt("<已渲染的 str>")`
找不到 `entries` ⇒ 返回空串 ⇒ **整段被静默丢弃**。实测读数：真实 run 的 reviewer
会话提示词长度 1082、内容只有合约文本；两位模型都如实报告「UNDER REVIEW 段不存在」。

修法是 `_section_of` 认 `str`（原样用）。**没有任何判据钉住它**：改回只认视图对象，
全仓不会红。

**判什么**：

1. 传**已渲染的 `str`** ⇒ 该段**原样出现**在最终提示词里（不是空串、不是 repr）；
2. 六段同时在场的**顺序**与 `compose_prompt` 文档描述一致（方向 → 前序 → 检索 →
   上一轮评审 → 评审点表 → 被评对象）；
3. 全缺时**逐字**返回 `purpose`（零回归口径）。

**反证臂**：让 `_section_of` 只认视图对象 ⇒ 第 1 条必须判红（复现真实缺陷）。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.application.run_orchestration.retrieval_prompt import (
    REVIEW_MATERIAL_SECTION_TITLE,
    compose_prompt,
)

_PURPOSE = "TASK — judge the artifact you were given."


class _View:
    """被评对象的**视图对象**形态（真实现有 `render_review_material_prompt` 消费它）。"""

    def __init__(self, body: str) -> None:
        self.body = body
        self.artifact_id = "task-1:research_plan"
        self.digest = "sha256:abc"


def _rendered_segment() -> str:
    """已渲染好的那一段（**这是真实路径的形态**：`session_prompts.*_prompt` 的返回值）。"""
    return f"{REVIEW_MATERIAL_SECTION_TITLE}\n\ncontent digest: sha256:abc\n\nBODY-MARKER-42"


class TestThePreRenderedStringSurvives:
    def test_a_rendered_string_is_used_verbatim(self) -> None:
        """受判面：传 `str` ⇒ 那一段**原样**出现（这是被修的那个缺陷）。"""
        prompt = compose_prompt(_PURPOSE, review_material=_rendered_segment())
        assert REVIEW_MATERIAL_SECTION_TITLE in prompt, prompt
        assert "BODY-MARKER-42" in prompt, "被评对象正文被静默丢弃了（缺陷复现）"
        assert "content digest: sha256:abc" in prompt, prompt

    def test_a_rendered_string_is_not_re_rendered_into_repr(self) -> None:
        """不得出现 `str(<str>)` 这类二次包装（会让正文变成引号包裹的转义串）。"""
        prompt = compose_prompt(_PURPOSE, review_material=_rendered_segment())
        assert "\n\n'" not in prompt, prompt
        assert "nBODY-MARKER" not in prompt, prompt

    def test_an_empty_rendered_string_does_not_add_the_section(self) -> None:
        """空段 ⇒ 逐字返回 purpose（空不是"有一段空的"）。"""
        assert compose_prompt(_PURPOSE, review_material="") == _PURPOSE


class TestTheSegmentOrderMatchesTheDocumentedContract:
    """顺序与 `compose_prompt` 的文档逐条对齐（六段全在场时判相对位置）。"""

    def test_the_six_sections_appear_in_the_documented_order(self) -> None:
        prompt = compose_prompt(
            _PURPOSE,
            direction="DIRECTION-MARKER",
            prior_knowledge="PRIOR-MARKER",
            retrieval="RETRIEVAL-MARKER",
            review_outcome="OUTCOME-MARKER",
            review_points="POINTS-MARKER",
            review_material="MATERIAL-MARKER",
        )
        order = [
            _PURPOSE,
            "DIRECTION-MARKER",
            "PRIOR-MARKER",
            "RETRIEVAL-MARKER",
            "OUTCOME-MARKER",
            "POINTS-MARKER",
            "MATERIAL-MARKER",
        ]
        positions = [prompt.index(marker) for marker in order]
        assert positions == sorted(positions), [
            (marker, pos) for marker, pos in zip(order, positions, strict=True)
        ]

    def test_the_review_material_is_last(self) -> None:
        """被评对象**紧贴**它要给出的判词读（文档口径）。"""
        prompt = compose_prompt(
            _PURPOSE,
            retrieval="RETRIEVAL-MARKER",
            review_material="MATERIAL-MARKER",
        )
        assert prompt.rindex("MATERIAL-MARKER") > prompt.rindex("RETRIEVAL-MARKER"), prompt


class TestTheCriterionBites:
    """**反证臂**：只认视图对象时，已渲染的 `str` 会被丢成空串（复现缺陷）。"""

    def test_render_only_mode_drops_the_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """按压：把 `_section_of` 换成"只认视图对象"，第 1 条必须红。"""
        import packages.application.run_orchestration.retrieval_prompt as module

        def view_only(value: Any, render: Any) -> str:
            if isinstance(value, str):
                return ""  # 旧行为：把已渲染的 str 当"不是视图" ⇒ 丢弃
            return str(render(value) or "")

        monkeypatch.setattr(module, "_section_of", view_only)
        prompt = module.compose_prompt(_PURPOSE, review_material=_rendered_segment())
        assert "BODY-MARKER-42" not in prompt, "按压后仍能看到正文 ⇒ 这条臂没咬合"
        assert prompt == _PURPOSE, prompt

    def test_the_real_module_still_uses_the_string(self) -> None:
        """正控制：不按压时同一条路径能看到正文（证明上面那条红是按压造成的）。"""
        prompt = compose_prompt(_PURPOSE, review_material=_rendered_segment())
        assert "BODY-MARKER-42" in prompt
