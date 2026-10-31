"""GOAL-20261031-102 EC-02：改稿闭环的**产品路径**判据（v2 在结构上存在且可读）。

**它补哪一格**：`response_letter.md` 此前只渲染 `action_taken` 自报字符串 —— 作者可以
写「已修改」，但没有任何东西验证手稿真的变了。本文件在**报告任务的产品入口**
（`execute_report_task`，与 `test_manuscript_assembly.py` 同一缝）取证五件事：

1. **闭环成立**：带改稿正文的 run 装出 `manuscript_v2.md`，其 `supersedes` 解析到 v1，
   读面（`revision_closure_of_run`）零问题，应答信里每条 `action_taken` 引用 v2；
2. **反证 (iii)**：v2 在场却没带 `supersedes` ⇒ 读面**点名判红**（按存储状态读，
   不信任「装配路径一定写了指针」）；
3. **反证 (v)**：`supersedes` 成环 ⇒ 读面点名（域面反证在 `tests/domain/test_artifacts.py`）；
4. **反证 (iv)**：`action_taken` 引用本 run 不带着的制品 / 不引用任何制品 ⇒
   任务 FAILED 且点名；
5. **零回归**：旧形状（应答没有改稿块）⇒ 只产应答信，不产 v2。

夹具复用 `tests.application.test_manuscript_assembly` 的种面（同一条记录、同一份
工具结果字节），改稿正文从它的 `_SECTIONS` 派生 —— 改的只是 Related Work 与
Discussion 的**措辞**（回应编辑要求），硬规则（无数字 / 引用闭合）两臂同守。
"""

from __future__ import annotations

import json
from typing import Any

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.deliverable.manuscript import MANUSCRIPT_ARTIFACT_NAME
from packages.application.run_orchestration.report_task import (
    ReportTaskDeps,
    execute_report_task,
)
from packages.application.run_orchestration.revision_assembly import (
    MANUSCRIPT_V2_NAME,
    parse_revised_manuscript,
    revision_closure_of_run,
    validate_action_references,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import ID
from packages.domain.tasks import ResearchTask
from tests.application.test_manuscript_assembly import (
    _SECTIONS,
    _assets,
    _context,
    _link,
    _put,
    _report_contract,
    _Reviews,
    _seed_narrative,
)


def _revised_sections() -> dict[str, str]:
    """改稿正文：Related Work 点名那个被变化的「计划选择」（编辑要求的那件事）。"""
    revised = dict(_SECTIONS)
    revised["related_work"] = (
        "The closest retrieved work builds reproducibility tooling for computational "
        "research and leaves the planning choice open [1]; this study names that choice — "
        "the item count the two arms set — and varies it under a fixed procedure."
    )
    revised["discussion"] = (
        "The measured difference is a workload effect and nothing more: the run varies the "
        "item count alone, one script cannot speak for another, and the reproducibility "
        "record base is a single retrieved work."
    )
    return revised


def _reply(*, action_cite: str = MANUSCRIPT_V2_NAME, with_revised: bool = True) -> str:
    """应答会话的受控回复：`author_responses` 块（+ 可选的 `revised_manuscript` 块）。"""
    action = f"revised the section named in P1; see {action_cite}"
    first = json.dumps(
        {
            "author_responses": [
                {"point_id": "P1", "response": "We accept P1.", "action_taken": action}
            ]
        },
        ensure_ascii=False,
    )
    blocks = [f"```json\n{first}\n```"]
    if with_revised:
        blocks.append(
            "```json\n"
            + json.dumps({"revised_manuscript": _revised_sections()}, ensure_ascii=False)
            + "\n```"
        )
    return "Point by point, then the revised body.\n\n" + "\n\n".join(blocks) + "\n"


def _state(run_id: str, *, reply: str) -> tuple[FakeArtifactStore, FakeEvidenceLedger]:
    """种入完整夹具：手稿正文 / 记录 / 评审决定 / 应答会话产物（各自都登记成证据）。"""
    store, ledger = _assets(run_id)
    _seed_narrative(store, ledger, run_id)
    decision = _put(
        store,
        f"{run_id}:review:task-r:review_decision",
        {
            "review_decision": {
                "verdict": "REJECT",
                "weakest_link": "the related work does not name the planning choice that "
                "differs between the arms",
            }
        },
        "execution_result",
        run_id,
    )
    _link(ledger, decision, tool=False, run_id=run_id)
    answer = _put(
        store,
        f"{run_id}:revision:task-a:author_responses",
        {"content": reply, "declared_artifact": "author_responses"},
        "execution_result",
        run_id,
    )
    _link(ledger, answer, tool=False, run_id=run_id)
    return store, ledger


def _run_revision(*, reply: str) -> tuple[Any, FakeArtifactStore, str]:
    """在给定 run 上跑一次报告任务（改稿闭环随 `manuscript=True` 附加装配）。"""
    run_id = ID.generate()
    store, ledger = _state(run_id.value, reply=reply)
    deps = ReportTaskDeps(artifacts=store, ledger=ledger, reviews=_Reviews(), manuscript=True)
    result = execute_report_task(
        deps,
        ResearchTask(id=ID.generate(), run_id=run_id),
        _report_contract(),
        _context(run_id),
        "trace-1",
    )
    return result, store, run_id.value


def test_a_revised_body_supersedes_the_manuscript_it_replaces() -> None:
    """闭环成立：v2 在场、`supersedes` → v1、读面零问题、信里逐条引用 v2。"""
    result, store, run_id = _run_revision(reply=_reply())
    assert result.outcome == "SUCCEEDED", result.message
    v1_id = f"{run_id}:{MANUSCRIPT_ARTIFACT_NAME}"
    v2_id = f"{run_id}:{MANUSCRIPT_V2_NAME}"
    v2 = store.meta(v2_id)
    assert v2 is not None, "带改稿正文的 run 必须装出 manuscript_v2.md"
    assert v2.supersedes == v1_id, (v2.supersedes, v1_id)
    assert store.meta(v1_id) is not None, "v2 指向的 v1 不在场"
    closure = revision_closure_of_run(store, run_id)
    assert closure is not None and closure["problems"] == (), closure
    letter = store.get(f"{run_id}:response_letter.md").decode("utf-8")
    assert MANUSCRIPT_V2_NAME in letter, letter[:600]


def test_the_read_face_refuses_a_pointerless_v2() -> None:
    """反证 (iii)：v2 在场却没带 `supersedes` ⇒ 读面点名（不信任装配路径）。"""
    result, store, run_id = _run_revision(reply=_reply())
    assert result.outcome == "SUCCEEDED", result.message
    v2_id = f"{run_id}:{MANUSCRIPT_V2_NAME}"
    meta = store.meta(v2_id)
    assert meta is not None
    store.put(
        Artifact(
            id=v2_id,
            digest=meta.digest,
            size_bytes=meta.size_bytes,
            media_type=meta.media_type,
            supersedes=None,
        ),
        store.get(v2_id),
    )
    closure = revision_closure_of_run(store, run_id)
    assert closure is not None
    assert any("no supersedes pointer" in item for item in closure["problems"]), closure


def test_the_read_face_refuses_a_cycle() -> None:
    """反证 (v)：v2 ⊳ B 且 B ⊳ v2 ⇒ 读面点名成环（链游走抓到，不是只判一跳）。"""
    result, store, run_id = _run_revision(reply=_reply())
    assert result.outcome == "SUCCEEDED", result.message
    v2_id = f"{run_id}:{MANUSCRIPT_V2_NAME}"
    meta = store.meta(v2_id)
    assert meta is not None
    content = store.get(v2_id)
    other = f"{run_id}:revision:task-b:revised_manuscript"
    store.put(
        Artifact(
            id=other,
            digest=meta.digest,
            size_bytes=meta.size_bytes,
            media_type=meta.media_type,
            supersedes=v2_id,
        ),
        content,
    )
    store.put(
        Artifact(
            id=v2_id,
            digest=meta.digest,
            size_bytes=meta.size_bytes,
            media_type=meta.media_type,
            supersedes=other,
        ),
        content,
    )
    closure = revision_closure_of_run(store, run_id)
    assert closure is not None
    assert any("supersedes cycle" in item for item in closure["problems"]), closure


def test_a_fabricated_reference_fails_the_task_by_name() -> None:
    """反证 (iv)a：`action_taken` 引用本 run 不带着的制品 ⇒ FAILED 且点名那个名字。"""
    result, _store, _run_id = _run_revision(
        reply=_reply(action_cite=f"{MANUSCRIPT_V2_NAME} and manuscript_v9.md")
    )
    assert result.outcome == "FAILED", result.message
    assert "manuscript_v9.md" in result.message, result.message


def test_an_action_that_names_no_artifact_fails_the_task_by_name() -> None:
    """反证 (iv)b：`action_taken` 不引用 `manuscript_v2.md` ⇒ FAILED（不许空谈）。"""
    result, _store, _run_id = _run_revision(reply=_reply(action_cite="the related work"))
    assert result.outcome == "FAILED", result.message
    assert MANUSCRIPT_V2_NAME in result.message, result.message


def test_an_old_shape_response_still_yields_only_the_letter() -> None:
    """零回归：旧形状（应答没有改稿块）⇒ 只产应答信，不产 v2（GOAL-100 的产物不变）。"""
    result, store, run_id = _run_revision(reply=_reply(with_revised=False))
    assert result.outcome == "SUCCEEDED", result.message
    assert store.meta(f"{run_id}:{MANUSCRIPT_V2_NAME}") is None
    letter = store.get(f"{run_id}:response_letter.md").decode("utf-8")
    assert "### P1" in letter, letter[:400]


def test_the_revised_body_survives_the_same_hard_rules() -> None:
    """改稿正文不降门槛：正文里写数字 ⇒ 任务 FAILED 且点名（与 v1 同一条判法）。"""
    bad = dict(_revised_sections())
    bad["results"] = "the count rose by 42 percent"
    reply = _reply().replace(
        json.dumps({"revised_manuscript": _revised_sections()}, ensure_ascii=False),
        json.dumps({"revised_manuscript": bad}, ensure_ascii=False),
    )
    result, store, run_id = _run_revision(reply=reply)
    assert result.outcome == "FAILED", result.message
    assert "42" in result.message or "'4'" in result.message, result.message
    assert store.meta(f"{run_id}:{MANUSCRIPT_V2_NAME}") is None


def test_validate_action_references_judges_names_against_the_run() -> None:
    """引用判据的直臂：在场名字集合里的引用通过；编造的点名（单元面）。"""
    from packages.application.deliverable.author_response import AuthorResponse, ResponseError

    answer = AuthorResponse(point_id="P1", response="ok", action_taken=f"see {MANUSCRIPT_V2_NAME}")
    validate_action_references((answer,), known_names=frozenset({MANUSCRIPT_V2_NAME, "a.md"}))
    fabricated = AuthorResponse(
        point_id="P1", response="ok", action_taken=f"see {MANUSCRIPT_V2_NAME} and ghost.md"
    )
    try:
        validate_action_references((fabricated,), known_names=frozenset({MANUSCRIPT_V2_NAME}))
    except ResponseError as error:
        assert "ghost.md" in str(error), error
    else:
        raise AssertionError("编造的引用没有被判红")


def test_parse_revised_manuscript_returns_none_when_the_block_is_absent() -> None:
    """旧形状的应答（无改稿块）⇒ `None`（不是错误）—— 两种「空」分得开。"""
    assert parse_revised_manuscript(json.dumps({"content": "no blocks here"})) is None
