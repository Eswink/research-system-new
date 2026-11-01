"""两个**域层早有、读面此前不披露**的字段（GOAL-20261101-103 EC-02）。

**它封住的失败形态**（两条同一种病：域里判得出，产品上拿不到）：

1. `Artifact.supersedes` 自 GOAL-20261031-102 EC-01 起就能表达「同一篇论文的下一版」，
   但 `ArtifactDto` 不披露它 ⇒ 改稿链在 API 上退化成**两个互不相干的制品**，前端只能
   看到两个长得很像的 id。
2. `ReviewFinding.reviewer_model` 自 GOAL-20261018-085 EC-01 起就能表达「这条判词是哪个
   模型判的」，但 `ReviewFindingDto` 不披露它 ⇒ 阶梯「复检」域的**判词可归因到模型**
   在产品读面上拿不到（只有直接读库才看得到）。

**判法（三处同轮，缺一处即漂移）**：Python DTO 有字段 + OpenAPI 快照有它 +
`types.ts` 有它。第三条由 `tests/contracts/test_openapi_snapshot.py` 与
`apps/web` 的 `tsc` 各自把关，本文件把前两条钉在一起。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.api.dto.artifacts import ArtifactDto
from services.api.dto.inspection import ReviewFindingDto

_ROOT = Path(__file__).resolve().parents[2]


def test_the_artifact_read_face_carries_the_supersedes_pointer() -> None:
    """`ArtifactDto` 有 `supersedes`，缺省 `None`（既有全部制品都是这一形态）。"""
    fields = ArtifactDto.model_fields
    assert "supersedes" in fields, "ArtifactDto 必须披露改稿链父指针（域层早就有）"
    assert fields["supersedes"].default is None, "缺省必须是 None（既有构造点零回归）"


def test_the_review_finding_read_face_carries_the_reviewer_model() -> None:
    """`ReviewFindingDto` 有 `reviewer_model`，缺省 `None`（= 未声明该面）。"""
    fields = ReviewFindingDto.model_fields
    assert "reviewer_model" in fields, "ReviewFindingDto 必须披露判词跑在哪个模型上"
    assert fields["reviewer_model"].default is None


def test_the_artifact_router_projects_the_pointer_from_the_domain_object() -> None:
    """**投影真的接了**：router 的 `_artifact_dto` 从域对象读 `supersedes`。

    只断言 DTO 有字段是不够的 —— 一个字段可以在 DTO 里、而投影从不填它（那就是
    `verified` 那种"列表面恒 None"的形态）。这里按 AST/源码读**赋值**那一行。
    """
    source = _ROOT.joinpath("services/api/routers/artifacts.py").read_bytes().decode("utf-8")
    assert 'supersedes=getattr(artifact, "supersedes", None)' in source, (
        "`_artifact_dto` 必须把域对象的 supersedes 投影进 DTO"
    )


def test_the_review_router_projects_the_reviewer_model() -> None:
    """**投影真的接了**：`run_reviews` 从 finding 读 `reviewer_model`。"""
    source = _ROOT.joinpath("services/api/routers/inspection.py").read_bytes().decode("utf-8")
    assert 'reviewer_model=getattr(item.finding, "reviewer_model", None)' in source, (
        "`run_reviews` 必须把 reviewer_model 投影进 DTO"
    )


def _artifact(**overrides: Any) -> Any:
    """最小制品替身（只带投影用到的字段；本判据不判域不变量）。"""

    class _Policy:
        def to_str(self) -> str:
            return "KEEP_FOREVER"

    base = {
        "id": "task-1:manuscript_v2.md",
        "digest": "sha256:abc",
        "size_bytes": 12,
        "media_type": "text/markdown",
        "state": type("S", (), {"value": "STAGED"})(),
        "created_by": "model:main/glm-5.3",
        "source_refs": [],
        "classification": None,
        "retention_policy": _Policy(),
        "created_at": None,
        "supersedes": "task-1:manuscript.md",
    }
    base.update(overrides)
    return type("Artifact", (), base)()


def test_the_projection_really_returns_the_pointer_for_a_revised_artifact() -> None:
    """端到端投影：给一个带父指针的制品 ⇒ DTO 的 `supersedes` 就是那个 id。"""
    from services.api.routers.artifacts import _artifact_dto

    dto = _artifact_dto(_artifact())

    assert dto.supersedes == "task-1:manuscript.md"


def test_an_artifact_without_the_field_reads_as_none_not_crash() -> None:
    """早期 / Fake store 的制品对象可能**没有**这一格 ⇒ 如实给 `None`（不 AttributeError）。"""

    class _Bare:
        id = "task-1:tool-result"
        digest = "sha256:def"
        size_bytes = 1
        media_type = "application/json"
        state = "STAGED"
        created_by = None
        source_refs: list[str] = []
        classification = None
        retention_policy = None
        created_at = None

    from services.api.routers.artifacts import _artifact_dto

    assert _artifact_dto(_Bare()).supersedes is None


def test_the_openapi_snapshot_declares_both_fields() -> None:
    """OpenAPI 快照同轮重生成（缺它 ⇒ `test_openapi_snapshot` 会判红，但那是另一个文件）。"""
    import json

    schema = json.loads(_ROOT.joinpath("docs/api/openapi.m13.json").read_text(encoding="utf-8"))
    schemas = schema["components"]["schemas"]
    assert "supersedes" in schemas["ArtifactDto"]["properties"]
    assert "reviewer_model" in schemas["ReviewFindingDto"]["properties"]
    assert "phases" in schemas["RunDetailDto"]["properties"]


def test_the_typescript_types_declare_both_fields() -> None:
    """`types.ts` 同轮同步（前端只消费本文件类型；漏它 ⇒ 页面拿不到值）。"""
    text = _ROOT.joinpath("apps/web/src/api/types.ts").read_bytes().decode("utf-8")
    assert "supersedes: string | null;" in text
    assert "reviewer_model: string | null;" in text
    assert "export interface PhaseProgressDto" in text
    assert "export interface EditorialDecisionDto" in text
