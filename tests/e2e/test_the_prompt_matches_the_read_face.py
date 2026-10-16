"""GOAL-20261016-081 EC-03：**提示词那段 == 读面制品**（逐条逐字）+ 反证。

**它与 `test_retrieval_context_reaches_the_session.py` 的分工**（不互相顶替）：078 判
「上下文制品在读面上**自足**」；本条判「**模型拿到的那段**与读面**逐条逐字**相同」——
即「模型看到了什么」能对着既有读面**重建**出来，且带**反证**（改一条 / 多一条 ⇒ 判红）。
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
from tests.e2e.test_ec03_real_runtime_offline_chain import mock_relay
from tests.e2e.test_retrieval_context_reaches_the_session import (
    _DOWNSTREAM_CONTRACT,
    _PROTOCOL,
    _assembled_deps,
)

__all__ = ["mock_relay"]

# **实测缺陷**（CI 的 `quality-windows-latest` 抓到）：本文件的用例与源文件**同一条路径**
# （同一个协议、同一段沙箱实验缝）⇒ 也需要容器 —— 漏了这个标记时，无 Docker 的环境里
# run 走不到实验格 ⇒ 检索从未发生 ⇒ 上下文为空 ⇒ 判据以「恰有一条非空上下文」失败。
# 判据**没有**放宽：那条断言是对的；缺的是**前置条件**的声明（与源文件同款）。
pytestmark = pytest.mark.requires_docker


class TestThePromptIsVerbatimTheReadFace:
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
