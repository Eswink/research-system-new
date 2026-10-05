"""GOAL-20261006-031 EC-02 判据：`citation.validate` 的**三态判定 + 单一取数面**。

**它把什么变成机械事实**：`citation.validate`（`citation.inspect` 的**判定层**）此前只有
声明（`roles.yaml` / `skills.yaml` / 能力词表），**没有实现**。本文件钉住四件事：

1. **三态规则显式**（EC-02(a)）—— 三个判词是**模块级常量**（`SUPPORTED` / `UNSUPPORTED` /
   `UNDETERMINED`），不是布尔收窄：
   * **成立**：来源解析出 linkset 且 ≥1 条 PMC 链接；
   * **不成立**：来源解析出 linkset 但**零链接**（引用不被来源支持）；
   * **无法判定**：来源**没有** linkset ⇒ **不得**当成「成立」，也**不得**读成「不成立」。
   **本判据逐条断言三种输入给出三种互不相同的判词** —— 二值实现（只看 `pmc_links == []`）
   会把后两种输入给出同一个判词，本判据立刻红。
2. **取数只有一个来源**（EC-02(b)）—— `citation.inspect` 与 `citation.validate` 经**同一
   端点、同一参数**取数：判据用**同一个 mock 响应**喂给两条工具，断言两者的 `pmc_links`
   **逐字相等**，且各自恰好触发**一次** elink 请求。
3. **点名失败**（EC-02(c) 的护栏）—— 无 `id` ⇒ `citation_validate requires an id`（点名）。
4. **反证两向**（EC-02(e)）—— ① 不被支持的引用 ⇒ `UNSUPPORTED` + 判词点名「零链接」；
   ② 来源缺失 ⇒ `UNDETERMINED` + 判词点名「没有 linkset」；且**两者不得相等**。

**不 import 产品常量当预言机**：三个判词的字面量**独立书写**在本文件里，产品常量是被测对象。
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from adapters.fakes import FakeArtifactStore
from adapters.research_tools.ncbi import (
    NcbiCitationValidationProvider,
    NcbiEutilsConfig,
    NcbiEutilsProvider,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.tool_plane.results import fetch_spilled_result
from packages.domain.core import Digest
from packages.domain.enums import EffectClass, ProviderType, TrustLevel
from packages.domain.tools import ToolCallRecord, ToolProviderSpec

#: 判词字面量（与产品常量同值但**独立书写** —— 判据的预言机必须自带）。
SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
UNDETERMINED = "UNDETERMINED"

PROVIDER = ToolProviderSpec(
    id="ncbi_citation",
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["citation.validate"],
    effect_class=EffectClass.READ_ONLY,
    network_domains=["eutils.ncbi.nlm.nih.gov"],
)

INSPECT_PROVIDER = ToolProviderSpec(
    id="ncbi_eutils",
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["citation.inspect"],
    effect_class=EffectClass.READ_ONLY,
    network_domains=["eutils.ncbi.nlm.nih.gov"],
)

#: 三种来源形态（**逐条对应三态**；判据的受判输入面就是这三份）。
LINKSET_WITH_LINKS: dict[str, Any] = {
    "linksets": [{"linksetdbs": [{"dbto": "pmc", "links": ["PMC8000001", "PMC8000002"]}]}]
}
LINKSET_WITHOUT_LINKS: dict[str, Any] = {
    "linksets": [{"linksetdbs": [{"dbto": "pmc", "links": []}]}]
}
NO_LINKSET: dict[str, Any] = {}

ELINK_REQUESTS: list[httpx.Request] = []


def _provider(payload: dict[str, Any]) -> NcbiEutilsProvider:
    """把 `payload` 当作 elink 的响应（其余端点不在本判据射程内）。"""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("elink.fcgi"):
            ELINK_REQUESTS.append(request)
            return httpx.Response(200, json=payload)
        return httpx.Response(404, text="not found")

    ELINK_REQUESTS.clear()
    return NcbiEutilsProvider(
        FakeArtifactStore(),
        config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        # 消费者要求：判定 payload 很小，默认 32 KiB 阈值会让它**不落盘** ⇒ 读不回。
        spill_threshold_bytes=1,
    )


def _call(tool_id: str, args: dict[str, Any]) -> ToolCallRecord:
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    return ToolCallRecord(
        task_id="task-1",
        attempt=1,
        operation_key="op-1",
        tool_id=tool_id,
        capability="citation.validate",
        argument_digest=Digest.of_bytes(raw),
    )


def _put_args(store: ArtifactStore, call: ToolCallRecord, args: dict[str, Any]) -> None:
    from packages.domain.artifacts import Artifact

    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    store.put(
        Artifact(
            id=f"tool-args:{call.task_id}:{call.operation_key}",
            digest=Digest.of_bytes(raw),
            size_bytes=len(raw),
            media_type="application/json",
        ),
        raw,
    )


def _run(
    provider: NcbiEutilsProvider,
    spec: ToolProviderSpec,
    *,
    tool_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """跑一次工具并取回落盘的 payload（**真 provider**，只 mock HTTP 面）。"""
    call = _call(tool_id, args)
    _put_args(provider._store, call, args)  # noqa: SLF001 - 夹具按契约写入该 artifact
    result = provider.execute(spec, call)
    content = fetch_spilled_result(provider._store, result)  # noqa: SLF001
    assert content is not None, "结果必须落盘（否则本判据读不到判定）"
    payload = json.loads(content.decode("utf-8"))
    assert isinstance(payload, dict), payload
    return payload


def _validate(payload: dict[str, Any], *, pmid: str = "38000001") -> dict[str, Any]:
    """跑一次 `citation_validate`（真实 `NcbiCitationValidationProvider`）。"""
    provider = NcbiCitationValidationProvider(
        FakeArtifactStore(),
        config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
        http_client=httpx.Client(transport=httpx.MockTransport(_handler_for(payload))),
        spill_threshold_bytes=1,
    )
    return _run(provider, PROVIDER, tool_id="citation_validate", args={"id": pmid})


def _handler_for(payload: dict[str, Any]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("elink.fcgi"):
            ELINK_REQUESTS.append(request)
            return httpx.Response(200, json=payload)
        return httpx.Response(404, text="not found")

    ELINK_REQUESTS.clear()
    return handler


class TestTheThreeStatesAreThreeDistinctVerdicts:
    """① 三态规则：三种输入 ⇒ 三种**互不相同**的判词（二值实现必红）。"""

    def test_a_linkset_with_links_is_supported(self) -> None:
        payload = _validate(LINKSET_WITH_LINKS)
        assert payload["verdict"] == SUPPORTED, payload
        assert payload["pmc_links"] == ["PMC8000001", "PMC8000002"], payload

    def test_a_linkset_without_links_is_unsupported(self) -> None:
        """EC-02(e)①：来源在场但零链接 ⇒ **不成立**（不是「无法判定」）。"""
        payload = _validate(LINKSET_WITHOUT_LINKS)
        assert payload["verdict"] == UNSUPPORTED, payload
        assert payload["pmc_links"] == [], payload
        assert "zero PMC links" in payload["reason"], payload

    def test_a_missing_linkset_is_undetermined(self) -> None:
        """EC-02(e)②：来源缺失 ⇒ **无法判定**（不得当成成立、也不得不成立）。"""
        payload = _validate(NO_LINKSET)
        assert payload["verdict"] == UNDETERMINED, payload
        assert "no linkset" in payload["reason"], payload

    def test_the_three_verdicts_are_pairwise_distinct(self) -> None:
        """**三态不是二值**：三种判词两两不等（二值实现会在这里红）。"""
        verdicts = {
            _validate(LINKSET_WITH_LINKS)["verdict"],
            _validate(LINKSET_WITHOUT_LINKS)["verdict"],
            _validate(NO_LINKSET)["verdict"],
        }
        assert verdicts == {SUPPORTED, UNSUPPORTED, UNDETERMINED}, verdicts
        assert len(verdicts) == 3, verdicts

    def test_undetermined_is_not_supported(self) -> None:
        """「无法判定」**不得**被算成「成立」（本 GOAL 的明文要求，单独成句断言）。"""
        undetermined = _validate(NO_LINKSET)
        supported = _validate(LINKSET_WITH_LINKS)
        assert undetermined["verdict"] != supported["verdict"], (undetermined, supported)


class TestTheFetchFaceIsSingleSource:
    """② 取数只有一套：两条能力经同一端点取到**同一读数**，且各只请求一次。"""

    def test_both_capabilities_read_the_same_links_from_the_same_endpoint(self) -> None:
        payload = LINKSET_WITH_LINKS

        inspect_provider = NcbiEutilsProvider(
            FakeArtifactStore(),
            config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
            http_client=httpx.Client(transport=httpx.MockTransport(_handler_for(payload))),
            spill_threshold_bytes=1,
        )
        inspect_payload = _run(
            inspect_provider, INSPECT_PROVIDER, tool_id="citation_inspect", args={"id": "38000001"}
        )
        inspect_requests = len(ELINK_REQUESTS)

        validate_payload = _validate(payload)
        validate_requests = len(ELINK_REQUESTS)

        assert inspect_payload["pmc_links"] == validate_payload["pmc_links"], (
            "两条能力必须读到同一份 links（同一取数面 ⇒ 同一读数）",
            inspect_payload,
            validate_payload,
        )
        assert inspect_payload["pmid"] == validate_payload["pmid"], (
            inspect_payload,
            validate_payload,
        )
        assert inspect_requests == 1, ("inspect 必须恰好请求一次 elink", inspect_requests)
        assert validate_requests == 1, ("validate 必须恰好请求一次 elink", validate_requests)

    def test_the_validate_tool_uses_the_elink_endpoint_with_the_same_parameters(self) -> None:
        _validate(LINKSET_WITH_LINKS)
        assert ELINK_REQUESTS, "validate 必须真的走 elink（否则取数面是假的）"
        request = ELINK_REQUESTS[-1]
        assert request.url.path.endswith("elink.fcgi"), request.url
        params = dict(request.url.params)
        assert params.get("dbfrom") == "pubmed", params
        assert params.get("db") == "pmc", params
        assert params.get("id") == "38000001", params
        assert params.get("retmode") == "json", params

    def test_the_two_capabilities_share_one_fetch_implementation_point(self) -> None:
        """结构判据：elink **取数点**在实现上只有一个（两条能力都调它）。

        行为判据（上面两条）证「读到同一份」；本条证「没有第二个 HTTP 请求点」——
        若有人给 `citation_validate` 另写一条 `self._get("elink.fcgi", …)`，本判据红。
        """
        import ast
        from pathlib import Path

        source = Path("adapters/research_tools/ncbi.py").read_text(encoding="utf-8")
        tree = ast.parse(source, filename="ncbi.py")
        call_sites: list[int] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr != "_get":
                continue
            if not node.args:
                continue
            endpoint = node.args[0]
            if isinstance(endpoint, ast.Constant) and endpoint.value == "elink.fcgi":
                call_sites.append(node.lineno)
        assert len(call_sites) == 1, (
            "elink 取数点必须恰好一个（第二个请求点 = 第二套取数）",
            call_sites,
        )

    def test_a_different_normalization_would_be_caught(self) -> None:
        """反证对照：取数**换成另一种归一化**会给出不同读数 ⇒ 「同一读数」断言不是恒真。"""
        same = _validate(LINKSET_WITH_LINKS)["pmc_links"]
        # 若有人只取第一条 linksetdb 的第一条链接（另一种归一化），读数会变成这样：
        different = ["PMC8000001"]
        assert same != different, "对照臂必须与真实读数不同，否则本反证在空转"


class TestAMissingIdIsNamed:
    """③ 点名失败：无 `id` ⇒ 逐字点名（不得静默返回一个判词）。"""

    def test_a_missing_id_is_refused_with_a_named_message(self) -> None:
        provider = NcbiCitationValidationProvider(
            FakeArtifactStore(),
            config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
            http_client=httpx.Client(
                transport=httpx.MockTransport(_handler_for(LINKSET_WITH_LINKS))
            ),
            spill_threshold_bytes=1,
        )
        call = _call("citation_validate", {})
        _put_args(provider._store, call, {})  # noqa: SLF001
        with pytest.raises(InvalidInputError) as excinfo:
            provider.execute(PROVIDER, call)
        assert "citation_validate requires an id" in str(excinfo.value), str(excinfo.value)


class TestTheJudgeItselfBites:
    """④ 判据自检：受判面非空 + 判词集合是声明集本身。"""

    def test_the_verdict_vocabulary_is_exactly_three(self) -> None:
        from adapters.research_tools.parsing import CITATION_VERDICTS

        assert set(CITATION_VERDICTS) == {SUPPORTED, UNSUPPORTED, UNDETERMINED}, CITATION_VERDICTS
        assert len(CITATION_VERDICTS) == 3, CITATION_VERDICTS

    def test_the_three_inputs_are_pairwise_different(self) -> None:
        """受判输入面非空且互不相同（否则三态判据可能在同一份输入上空转）。"""
        shapes = {
            json.dumps(LINKSET_WITH_LINKS, sort_keys=True),
            json.dumps(LINKSET_WITHOUT_LINKS, sort_keys=True),
            json.dumps(NO_LINKSET, sort_keys=True),
        }
        assert len(shapes) == 3, shapes
