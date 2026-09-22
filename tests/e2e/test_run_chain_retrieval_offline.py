"""GOAL-011 EC-01 / EC-02 的**离线**判据：运行链真的执行检索，且来源性质被判据要求。

与 `test_run_chain_retrieval_live.py` 的分工：那份要真实 LLM + 真实 NCBI（挂
`requires_live_llm`，默认门不跑）；本文件用本机 mock 端点 + `httpx.MockTransport`
（离线、默认门可跑），测的是**链与判据**：声明面 → 运行链执行两步 → 工具证据落
canonical → 读面可区分来源性质 → 验收门**按性质**裁决。

两条用例**成对**（EC-01 与 EC-02 的反证都在其中）：

- 接上能力步 ⇒ 工具观测存在、标识来自检索响应本身、来源性质为 `RETRIEVED`、run `SUCCEEDED`；
- **去掉**能力步 ⇒ 零工具观测 **且** `EVIDENCE_COVERAGE` 判拒 ⇒ run `FAILED`
  （判词点名缺的是「检索来源」这一维）。

装配与读面辅助取自 `test_ec03_real_runtime_offline_chain`（同一套 mock 端点与
`_read_chain` 读面快照），避免两处各写一份、慢漂移。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from tests.e2e.live_run_support import (
    MOCK_PMIDS as _MOCK_PMIDS,
)
from tests.e2e.live_run_support import (
    ncbi_run_chain_provider as _ncbi_run_chain_provider,
)
from tests.e2e.live_run_support import (
    offline_ncbi_http as _offline_ncbi_http,
)
from tests.e2e.live_run_support import (
    openhands_deps as _openhands_deps,
)
from tests.e2e.live_run_support import (
    start_run as _start,
)
from tests.e2e.live_run_support import (
    with_run_chain_capabilities as _with_run_chain,
)

# 读面快照与 mock 端点由 EC-03 那份 e2e 提供（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import (
    _RETRIEVAL_PROTOCOL,
    _read_chain,
    mock_relay,
)

__all__ = ["mock_relay"]


def _assert_retrieval_landed(reads: Any, http_calls: list[str]) -> None:
    """主干断言（EC-01 三句 + EC-02 两句），与 live 判据同口径、同顺序。"""
    assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
    assert http_calls == ["esearch.fcgi", "efetch.fcgi"], http_calls
    tool_evidence = [item for item in reads.evidence if item["tool_refs"]]
    by_tool = {tuple(item["tool_refs"]): item for item in tool_evidence}
    assert set(by_tool) == {
        ("ncbi_eutils", "literature_search"),
        ("ncbi_eutils", "literature_read"),
    }, (tool_evidence, reads.failures)
    read_step = by_tool[("ncbi_eutils", "literature_read")]
    # 来源命名沿用既有口径 `tool:{tool_id}:{task}:{operation_key}`（provider 记在 tool_refs）。
    assert read_step["source_origin"].startswith("tool:literature_read:"), read_step
    # 真实标识进证据链：读取步读的就是检索响应里返回的那个 PMID。
    assert _MOCK_PMIDS[0] in read_step["id"], read_step
    assert _MOCK_PMIDS[0] in read_step["source_ref"], read_step
    assert str(read_step["artifact_id"]).startswith("tool-result:"), read_step
    assert read_step["content_digest"], read_step
    # EC-02：**来源性质**在同一个读面上可区分（不是靠 id 前缀猜出来的）。
    assert {item["source_trust_label"] for item in tool_evidence} == {"RETRIEVED"}, tool_evidence
    labels = {item["source_trust_label"] for item in reads.evidence}
    assert "RETRIEVED" in labels and "USER_PROVIDED" in labels, reads.evidence
    declared = [item for item in reads.evidence if item["source_trust_label"] == "USER_PROVIDED"]
    assert declared and all(not item["tool_refs"] for item in declared), declared


def test_run_chain_retrieval_is_observed_and_traceable(mock_relay: str) -> None:
    """GOAL-011 EC-01 主干：`analysis` phase 真的执行了检索，且标识**来自检索响应本身**。

    与「谁来调工具」这条岔路相对：本判据测量的不是模型行为（概率性），而是**运行链**
    的确定性后果。真实协议 `real_retrieval_research_v1.yaml` 的 phase 声明
    `capability_execution: run_chain` + `literature.search/read`，运行链据声明执行两步
    （检索 → 读取，读取用的是检索响应里返回的 id），证据经 `register_tool_evidence`
    **同一个** claim 落 canonical。

    EC-01 的三句与 EC-02 的两句都在 `_assert_retrieval_landed` 里（同一读面、同一口径）：
    终态 `SUCCEEDED`、工具观测可读、真实 PMID 进证据链；性质可区分（`RETRIEVED` vs
    `USER_PROVIDED`）、覆盖**由检索来源满足**——最后这一句的证据就是 run 能过验收门
    （合约要求 `minimum_retrieved_sources: 1`，门判的是 `SourceRecord.trust_label`，
    不是证据条数）。成对的反证见下一条用例。
    """
    from services.api.app import create_app

    http_calls: list[str] = []
    deps = _openhands_deps(mock_relay, map_tools=False)
    _with_run_chain(
        deps, _ncbi_run_chain_provider(deps, http_client=_offline_ncbi_http(http_calls))
    )
    with TestClient(create_app(deps)) as client:
        reads = _read_chain(client, _start(client, _RETRIEVAL_PROTOCOL))

    _assert_retrieval_landed(reads, http_calls)


def test_run_chain_retrieval_absent_without_the_wiring(mock_relay: str) -> None:
    """EC-02 的反证（EC-01 反证的加强）：**不接**能力步 ⇒ 零工具观测 **且覆盖判拒**。

    为什么这条必须存在：主干判据若只看「有两条工具证据」，一个恒返回固定证据的实现
    也能骗过它；而若只看「run `SUCCEEDED`」，一个把覆盖降到"有几条证据就算几条"的实现
    同样能骗过它。这里把**因果**钉住：同一份协议、同一套装配，**只**去掉检索接线 ⇒
    ① 该 phase 零工具观测（EC-01 的反证面）；② 合约的性质维度（`minimum_retrieved_sources`）
    不再被满足 ⇒ 验收门判拒、run 收敛 **`FAILED`**（EC-02 的反证面）。

    这一条同时说明：去掉检索**不是**「少了个可选装饰」——检索来源是**被判据要求的**。
    """
    from services.api.app import create_app

    deps = _openhands_deps(mock_relay, map_tools=False)
    with TestClient(create_app(deps)) as client:
        reads = _read_chain(client, _start(client, _RETRIEVAL_PROTOCOL))

    assert [item for item in reads.evidence if item["tool_refs"]] == [], reads.evidence
    assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
    assert any("acceptance gate" in message for message in reads.failures), reads.failures
    # 判定来自**覆盖判据**（不是别的门）：判词点名缺的是「检索来源」这一维。
    assert any("retrieved sources" in message for message in reads.failures), reads.failures
