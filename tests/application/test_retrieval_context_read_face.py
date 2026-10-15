"""GOAL-20261014-078 EC-03 判据：**「进了什么」在既有读面上可复核**。

**它补哪一格**：EC-01/EC-02 让上下文进了会话，但那是**进程内对象**知道的 ——
「哪些内容进了上下文、各自的 digest 与来源」在**读面**上还答不出来。本文件把
装配结果**落成制品**的判据钉死：写出的字节**就是** `retrieval_digest` 的源
（**同源** ⇒ 读面值与装配点的值不可能分叉），且制品 id 按 **task 前缀**命名
⇒ 它天然落在既有的 `GET /runs/{id}/artifacts` 上（**零新路由**）。

**边界**：本文件只判**制品面**（落盘 + 可读 + 同源 + 空集合带理由 + 命名约定）；
**HTTP 面**的端到端取证在 `tests/e2e/`（那里有真装配与真路由）。
"""

from __future__ import annotations

import json

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.run_orchestration.retrieval_context import (
    build_retrieval_context,
    context_artifact_id,
    persist_retrieval_context,
)
from packages.domain.core import Digest
from tests.application.test_retrieval_context_seam import (  # noqa: E402 - 复用既有夹具
    _RUN,
    _TASK,
    _retrieved_view,
)


class TestTheContextIsReadableAftheFact:
    """GOAL-20261014-078 EC-03：装配结果**落成制品**（既有读面可复核「进了什么」）。

    取证面锚定在**同源**上：写出的字节**就是** `retrieval_digest` 的源 ——
    因此「读面的值 == 装配点的值」不是靠比对两次计算结果，而是**不可能分叉**。
    """

    def test_the_written_artifact_is_the_digest_source(self) -> None:
        store, view = _retrieved_view()
        artifact_id = persist_retrieval_context(store, _TASK, view)
        raw = store.get(artifact_id)
        assert str(Digest.of_bytes(raw)) == view.snapshot.retrieval_digest, (
            "写盘字节必须**就是** `retrieval_digest` 的源（同源 ⇒ 读面值不可能与装配点分叉）",
        )
        assert str(store.meta(artifact_id).digest) == view.snapshot.retrieval_digest, store.meta(
            artifact_id
        )

    def test_the_artifact_id_is_task_prefixed_and_named(self) -> None:
        """制品 id 以 **task id** 为前缀 ⇒ 它天然落在 `GET /runs/{id}/artifacts` 上。

        这是**省掉一条新路由**的机制（既有路由按 `task:{id}` 约定收 run 作用域制品）
        —— 判据把这条命名约定钉住，免得将来改名把这件制品从读面上「弄丢」。
        """
        store, view = _retrieved_view()
        artifact_id = persist_retrieval_context(store, _TASK, view)
        assert artifact_id == context_artifact_id(_TASK), artifact_id
        assert artifact_id.split(":", 1)[0] == _TASK, (
            "前缀必须是 task id（既有读面按这个约定收集 run 作用域制品）",
            artifact_id,
        )
        assert artifact_id.endswith(":retrieval_context"), artifact_id

    def test_the_payload_carries_the_entries_for_a_reader(self) -> None:
        """载荷**自足**：读面的人不用回查任何东西就能看出「进了什么」。"""
        store, view = _retrieved_view()
        artifact_id = persist_retrieval_context(store, _TASK, view)
        payload = json.loads(store.get(artifact_id).decode("utf-8"))
        assert payload["run_id"] == _RUN, payload
        entries = payload["entries"]
        assert isinstance(entries, list) and len(entries) == len(view.entries), payload
        for entry in entries:
            for key in ("identifier", "evidence_id", "artifact_id", "shown"):
                assert entry.get(key), (key, entry)

    def test_an_empty_context_is_written_with_its_reason(self) -> None:
        """空集合也**要读得出来**：制品在、`entries == []`、理由**点名**。"""
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        view = build_retrieval_context(store, ledger, _RUN)
        artifact_id = persist_retrieval_context(store, _TASK, view)
        payload = json.loads(store.get(artifact_id).decode("utf-8"))
        assert payload["entries"] == [], payload
        assert payload.get("reason") and "no retrieved evidence" in payload["reason"], payload

    def test_a_non_default_creator_names_the_assembly_not_an_agent(self) -> None:
        """`created_by` 记的是**装配事实**（编排层写的），不是任何 agent 的产出。"""
        store, view = _retrieved_view()
        artifact_id = persist_retrieval_context(store, _TASK, view)
        assert store.meta(artifact_id).created_by == "system:retrieval-context", store.meta(
            artifact_id
        )
