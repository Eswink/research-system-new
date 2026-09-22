"""GOAL-011 EC-01 的 **live** 判据：一次真实 run 的 analysis phase 真的调用了检索。

与离线判据的分工（两个文件都在，互不替代）：

- `test_ec03_real_runtime_offline_chain.py` 用 `httpx.MockTransport` 测**链**（离线、
  默认门可跑，判据是"标识来自检索响应本身"）；
- 本文件测**真的是不是检索得到东西**：真 LLM + 真 NCBI E-utilities，判据是
  canonical 证据链里出现**真实 PMID**，且该 PMID 就是这次检索返回的
  （从检索结果 artifact 的字节里复算，不另存一份期望值）。

出网面：整个用例挂 `requires_live_llm`（`tests/egress_guard.py` 的唯一放行面）；
不带该 marker 的默认门里它**不会**跑，也不会出网。真实检索**最小必要次数**：一次
esearch + 一次 efetch（`literature_read` 的 ids 来自检索结果本身），本判据把请求数
钉成 2 —— 多一次就红。

操作者口令（值只在环境变量里，永不落盘/回显）：

```bash
set -a; . ./.env; set +a
RESEARCHOS_AGENT_RUNTIME=openhands pytest tests/e2e/test_run_chain_retrieval_live.py -q -rs
```
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.e2e.live_run_support import (
    LIVE_CREDENTIAL_REF,
)
from tests.e2e.live_run_support import (
    MOCK_PMIDS as _FIXTURE_PMIDS,
)
from tests.e2e.live_run_support import (
    ncbi_run_chain_provider as _ncbi_run_chain_provider,
)
from tests.e2e.live_run_support import (
    openhands_deps as _openhands_deps,
)
from tests.e2e.live_run_support import (
    run_chain_store_ledger as _store_and_ledger,
)
from tests.e2e.live_run_support import (
    run_failures as _failures,
)
from tests.e2e.live_run_support import (
    start_run as _start,
)
from tests.e2e.live_run_support import (
    with_run_chain_capabilities as _with_run_chain,
)

#: GOAL-011 EC-01 的真实协议（`analysis` phase 声明 run_chain 检索能力）。
RETRIEVAL_PROTOCOL = "real_retrieval_research_v1.yaml"
#: 目录/协议声明的检索端点域（不新造第二份白名单）。
DECLARED_DOMAIN = "eutils.ncbi.nlm.nih.gov"
#: 一次最小必要检索 = esearch + efetch。
EXPECTED_REQUESTS = 2
_PMID = re.compile(r"\d{6,9}")


def _live_credentials() -> tuple[str, str] | None:
    """Live 运行的口令：端点取**目录声明**（不是测试里另写一个 base_url），凭据取环境变量。

    凭据引用就是目录里 endpoint 声明的 `credential_ref`（本仓库 `LLM_MAIN_KEY`）：
    值只在环境变量里，**不落盘、不回显、不进断言**；取不到即如实 skip（skip 不是 PASS）。
    `RESEARCHOS_LIVE_E2E_ENDPOINT` 仅供换端点复跑用，缺省即目录声明值。
    """
    from services.api.catalog import load_catalog_snapshot

    catalog = load_catalog_snapshot()
    endpoint = next(
        (
            item
            for item in catalog.endpoints.values()
            if item.credential_ref == LIVE_CREDENTIAL_REF
            and item.protocol == "OPENAI_COMPATIBLE"
            and item.enabled
        ),
        None,
    )
    if endpoint is None:
        return None
    api_key = os.environ.get(LIVE_CREDENTIAL_REF)
    if not api_key:
        return None
    base_url = os.environ.get("RESEARCHOS_LIVE_E2E_ENDPOINT") or endpoint.base_url
    return base_url.rstrip("/"), api_key


def _by_tool(evidence: list[dict[str, Any]]) -> dict[tuple[str, ...], dict[str, Any]]:
    """工具观测按 tool_refs 索引（非工具来源不进这张表）。"""
    return {tuple(item["tool_refs"]): item for item in evidence if item["tool_refs"]}


def _read_step_ids(read_step: dict[str, Any]) -> list[str]:
    """读取步**实际读的**标识：取自 operation_key（source_ref 的最后一段）。

    为什么不用正则扫整个 source_ref：`source_ref` 里还有 task id（UUID）——UUID 的
    十六进制段会被 `\\d{6,9}` 扫出来（实测：多出一个 `908144` 的假标识），判据因此
    在真实运行里**假红**。只解 operation_key 这一段，标识就是逐字的那串。
    """
    key = str(read_step["source_ref"]).rsplit(":", 1)[-1]
    return [item for item in key.split("+") if item]


def _register_live_http(calls: list[str]) -> Any:
    """**不拦截**的 httpx client：只记录真实出站 URL，好让判据数得清请求次数。"""
    return httpx.Client(
        event_hooks={"request": [lambda request: calls.append(str(request.url))]},
        timeout=60.0,
    )


@pytest.mark.requires_live_llm
def test_live_run_chain_retrieval_lands_a_real_identifier() -> None:
    """真实 run 真的检索：run 到终态；工具观测可读；**真实 PMID** 进证据链。"""
    credentials = _live_credentials()
    if credentials is None:
        pytest.skip(
            "live retrieval needs RESEARCHOS_LIVE_E2E_ENDPOINT+KEY (or DEV_LLM_BASE_URL+API_KEY)"
        )
    base_url, api_key = credentials
    calls: list[str] = []
    deps = _openhands_deps(
        base_url,
        map_tools=False,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=api_key,
    )
    http_client = _register_live_http(calls)
    _with_run_chain(deps, _ncbi_run_chain_provider(deps, http_client=http_client))
    try:
        from services.api.app import create_app

        with TestClient(create_app(deps)) as client:
            run = _start(client, RETRIEVAL_PROTOCOL)
            failures = _failures(client, run["id"])
            evidence = client.get(f"/runs/{run['id']}/evidence").json()
    finally:
        http_client.close()

    assert run["state"] == "SUCCEEDED", (run, failures)
    assert len(calls) == EXPECTED_REQUESTS, calls
    assert all(url.startswith(f"https://{DECLARED_DOMAIN}/") for url in calls), calls

    store, _ledger = _store_and_ledger(deps)
    steps = _by_tool(evidence)
    search_step = steps[("ncbi_eutils", "literature_search")]
    read_step = steps[("ncbi_eutils", "literature_read")]
    payload = json.loads(store.get(str(search_step["artifact_id"])).decode("utf-8"))
    returned = [str(item) for item in payload["ids"]]
    assert returned, payload
    # 非空转锚点：拿到的不能是离线夹具的标识（否则传输层被换成了 mock）。
    assert not (set(returned) & set(_FIXTURE_PMIDS)), ("live 判据拿到了夹具标识", returned)
    brief = json.loads(store.get("input-brief:real_research_v1").decode("utf-8"))
    assert payload["query"] == brief["retrieval"]["query"], payload

    read_ids = _read_step_ids(read_step)
    assert read_ids, read_step
    # 读取步读的必须是**这次检索返回的**标识（从检索结果字节里复算，不用期望值）。
    assert set(read_ids) <= set(returned), (read_ids, returned)
    assert read_ids[0] in str(read_step["id"]), read_step
    assert read_step["content_digest"], read_step
