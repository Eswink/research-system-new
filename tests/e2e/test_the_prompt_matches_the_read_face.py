"""GOAL-20261014-078 EC-03 + GOAL-20261016-081 EC-03：**「进了什么」在既有读面上可复核**。

**为什么单列**：`test_retrieval_context_reaches_the_session.py` 贴着 450 行硬上限
（规模门），而本组用例（读面载荷 + 提示词那段的逐条逐字比对）是**独立可读**的一段 ——
按全仓既有的「按面拆文件」手法单列（与本目录其它 e2e 同款）。

**两个 GOAL 的分工**：078 判「上下文制品在读面上**自足**」；081 判「**提示词那段**与读面
**逐条逐字**相同」（模型看到的 == 读面能重建的）—— 后者带**反证**（改一条 / 多一条 ⇒ 判红）。
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.literature_chain_support import OfflineEuropePmc
from tests.e2e.live_run_support import start_run
from tests.e2e.retrieval_context_support import (
    assert_the_prompt_matches_the_read_face,
    context_payloads,
)
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay
from tests.e2e.test_retrieval_context_reaches_the_session import (
    _DOWNSTREAM_CONTRACT,
    _PROTOCOL,
    _assembled_deps,
)

__all__ = ["mock_relay"]


class TestWhatEnteredTheContextIsReadableAftheFact:
    """GOAL-20261014-078 EC-03：**「进了什么」在既有读面上可复核**（HTTP 面端到端）。

    取证面是**既有路由** `GET /runs/{id}/artifacts` —— 上下文制品按 **task 前缀**命名，
    因此它天然落在 run 作用域里（**零新路由、零新 DTO、零快照改动**）。
    读到的载荷必须**自足**：run 标识、逐条标识 / 证据 id / 制品 id / 摘录都在里面。
    """

    def _context_payloads(self, client: TestClient, run_id: str) -> dict[str, Any]:
        """读面上该 run 的上下文制品 → `{artifact_id: payload}`（只经既有路由）。"""
        artifacts = client.get(f"/runs/{run_id}/artifacts").json()
        ids = [
            str(item["id"]) for item in artifacts if str(item["id"]).endswith(":retrieval_context")
        ]
        return {
            artifact_id: json.loads(
                client.get(f"/artifacts/{artifact_id}/content").content.decode("utf-8")
            )
            for artifact_id in ids
        }

    def test_the_context_is_on_the_read_face_and_matches_the_session(self, mock_relay: str) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            payloads = self._context_payloads(client, str(run["id"]))

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        # 两个会话 phase 各一件（实验/报告格不建会话 ⇒ 不写 —— 见实现里的分派）。
        assert len(payloads) == 2, sorted(payloads)
        # 下游非空、上游空且带理由（与 EC-02 的两向一致 —— 读面**印证**会话 spec）。
        non_empty = [p for p in payloads.values() if p["entries"]]
        empty = [p for p in payloads.values() if not p["entries"]]
        assert len(non_empty) == 1 and len(empty) == 1, payloads
        assert empty[0].get("reason"), ("空集合必须在读面上带理由", empty[0])
        # 载荷自足：run 标识 + 逐条四列在场。
        for payload in payloads.values():
            assert payload["run_id"] == str(run["id"]), payload
            for entry in payload["entries"]:
                for key in ("identifier", "evidence_id", "artifact_id", "shown"):
                    assert entry.get(key), (key, entry)

    def _prompt_and_read_face(self, mock_relay: str) -> tuple[str, dict[str, Any]]:
        """跑一次真实 run ⇒ `(提示词那段, 下游的读面载荷)`（三个 EC-03 用例共用）。"""
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            payloads = context_payloads(client, str(run["id"]))

        non_empty = [payload for payload in payloads.values() if payload["entries"]]
        assert len(non_empty) == 1, ("本协议下恰有一条非空上下文（下游）", payloads)
        prompt = recorder.retrieval_prompt_of(_DOWNSTREAM_CONTRACT)
        assert prompt, "**先决条件**：提示词里必须有那段（否则本组用例测不到东西）"
        return prompt, non_empty[0]

    def test_the_prompt_is_verbatim_the_read_face(self, mock_relay: str) -> None:
        """**EC-03 正向**：提示词那段与读面制品**逐条逐字**相同（行级、含顺序）。

        这是「模型拿到了什么」可复核的机械含义：读者拿**既有读面**就能核对 ——
        不靠回忆、不靠日志。
        """
        prompt, payload = self._prompt_and_read_face(mock_relay)
        assert_the_prompt_matches_the_read_face(prompt, payload)

    def test_a_change_or_a_dropped_entry_makes_the_comparison_red(self, mock_relay: str) -> None:
        """**EC-03 反证**（两个形态）：改一条 / 多一条 ⇒ 同一比较**判红**。

        为什么必须做：只报「两边都在场」的比较可能**没有分辨力**。两个形态各打一类假绿：
        ① **改一条**（首条 `shown` 换掉）⇒ 打「只比条数」的写法；
        ② **多一条**（读面多一条 ⇒ 等价于渲染器少排一条）⇒ 打「用 `in` 判包含」的写法。
        """
        prompt, payload = self._prompt_and_read_face(mock_relay)

        changed = json.loads(json.dumps(payload))
        changed["entries"][0]["shown"] = "TAMPERED — this is not what the model saw"
        with pytest.raises(AssertionError, match="逐条逐字"):
            assert_the_prompt_matches_the_read_face(prompt, changed)

        extra = json.loads(json.dumps(payload))
        extra["entries"].append({"identifier": "extra-99999", "shown": "an entry nobody rendered"})
        with pytest.raises(AssertionError, match="逐条逐字"):
            assert_the_prompt_matches_the_read_face(prompt, extra)

    def test_the_read_face_value_is_the_assembly_value(self, mock_relay: str) -> None:
        """**同源**：读面制品的 digest == 该 run 那次会话的 `retrieval_digest`。

        这条把「读面读到的」与「会话拿到的」钉成同一份事实 —— 不是分别算两次再比，
        而是**同一份字节**：写盘字节就是 `retrieval_digest` 的源（见实现）。
        """
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            artifacts = client.get(f"/runs/{run['id']}/artifacts").json()

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        context = recorder.context_of(_DOWNSTREAM_CONTRACT)
        assert context is not None and context.selected_refs, context
        listed = [
            str(item["digest"])
            for item in artifacts
            if str(item["id"]).endswith(":retrieval_context")
        ]
        assert str(context.retrieval_digest) in listed, (
            "会话拿到的 `retrieval_digest` 必须**在场于**读面制品的 digest 里（同源）",
            context.retrieval_digest,
            listed,
        )
