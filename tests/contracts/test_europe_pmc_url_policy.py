"""URL 策略在**触网之前**判 host（GOAL-20260929-027 EC-01 ④ 的净增量）。

本文件是**新增**判据，既有判据一字未改。被测命题有两条，缺一不可：

**命题一（反证，两向）**：目标 host / scheme 不合法 ⇒ **零请求**。反证必须断言
`transport` 收到的请求数 **== 0** —— 「请求后被拒」不算通过。三类被拒形态各自独立：

1. **仅 http/https**：（`ftp://` / `file://`）非 http(s) scheme；
2. **保留类地址**：环回 / localhost / 私有 / 链路本地 / 多播 / CGNAT / 文档保留段 ——
   判据**只有** `packages/application/model_relay/endpoint_policy.py::endpoint_url_refusal`
   一处（不新造第二个 host 谓词）；
3. **声明式白名单**：host 必须落在**声明的** `network_domains` 内 —— 声明外的公网域名
   同样零请求被拒；声明为空 ⇒ 一律拒（fail closed）。

**命题二（正控制）**：合法 host ⇒ 请求**真的发出**（计数 > 0）且被真解析。
没有这一条，命题一会被一个「怎么都不发请求」的空转实现骗过。

**反向控制**（证明拒绝的理由是**声明**而不是硬编码）：把同一 host 写进
`network_domains` ⇒ 同一请求被放行。

口径边界（如实）：本 provider 只对**自己的**出站请求做这层判定；仓内没有全局出口
网关，其它 provider 的 `network_domains` 仍无人执法（本 EC 只补新 provider 这一条，
不声称「全仓出站已受控」）。默认门仍离线，`tests/egress_guard.py` 未放宽。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeArtifactStore
from adapters.research_tools.europe_pmc import EUROPE_PMC_BASE_URL
from packages.application.ports.errors import PermanentPortError
from packages.domain.enums import EffectClass, ProviderType, ToolResultStatus, TrustLevel
from packages.domain.tools import ToolProviderSpec
from tests.contracts.europe_pmc_support import (
    PROVIDER,
    REAL_PMID,
    SEARCH_TOOL,
    Transport,
    call_port,
    make_call,
    make_provider,
    put_args,
    real_record,
    refuse_before_network,
    run_tool,
    search_args,
    search_payload,
)

#: 声明外但**完全合法**的第三方域名（用于证明白名单是必要条件）。
UNDECLARED_PUBLIC_HOST = "https://eutils.ncbi.nlm.nih.gov/x"


def spec_with_domains(*domains: str) -> ToolProviderSpec:
    return ToolProviderSpec(
        id="europe_pmc",
        kind=ProviderType.REST,
        trust_level=TrustLevel.VERIFIED,
        capabilities=["literature.search", "literature.read"],
        effect_class=EffectClass.READ_ONLY,
        transport="rest",
        network_domains=list(domains),
    )


class TestRefusedBeforeAnyRequest:
    """反证：全部在**触网之前**判 ⇒ transport 请求计数必须为 0。"""

    @pytest.mark.parametrize(
        ("base_url", "shape"),
        [
            ("https://evil.example.com/europepmc/webservices/rest", "非声明域名"),
            ("http://www.ebi.ac.uk.evil.example.com/europepmc/webservices/rest", "后缀伪装域名"),
            ("ftp://www.ebi.ac.uk/europepmc/webservices/rest", "非 http(s) scheme"),
            ("file:///etc/passwd", "非网络 scheme"),
            ("https://127.0.0.1/europepmc/webservices/rest", "环回地址"),
            ("https://localhost/europepmc/webservices/rest", "localhost"),
            ("https://10.0.0.5/europepmc/webservices/rest", "私有地址"),
            ("https://169.254.169.254/latest/meta-data", "链路本地 / 云元数据"),
            ("https://224.0.0.1/europepmc/webservices/rest", "多播 / 保留段"),
            ("https://100.64.0.1/europepmc/webservices/rest", "CGNAT 共享地址"),
            ("https://203.0.113.10/europepmc/webservices/rest", "文档用保留段"),
            ("https://[::1]/europepmc/webservices/rest", "IPv6 环回"),
            ("https://[fe80::1]/europepmc/webservices/rest", "IPv6 链路本地"),
        ],
    )
    def test_host_or_scheme_refused_before_transport(self, base_url: str, shape: str) -> None:
        transport = refuse_before_network(base_url)
        assert transport.requests == [], f"{shape} 不得产生任何请求"
        assert transport.count == 0

    def test_declared_domain_whitelist_is_required_not_just_reserved_classes(self) -> None:
        """仅「非保留类」不够：**声明外**的公网域名同样零请求被拒。"""
        store = FakeArtifactStore()
        transport = Transport()
        provider = make_provider(transport, base_url=UNDECLARED_PUBLIC_HOST, store=store)
        args = search_args()
        call = make_call(SEARCH_TOOL, args)
        put_args(store, call, args)

        with pytest.raises(PermanentPortError) as exc_info:
            call_port(provider, PROVIDER, call)

        assert transport.count == 0, "声明外域名必须在触网前被拒"
        assert "network_domains" in str(exc_info.value), "拒绝理由必须点名声明面"

    def test_undeclared_host_is_rejected_even_when_public_and_https(self) -> None:
        """同上但换一个域名，证明拒绝不是针对某一个具体 host。"""
        refuse_before_network("https://example.org/europepmc/webservices/rest")

    def test_empty_declaration_refuses_everything(self) -> None:
        """未声明任何域名 ⇒ 一律零请求（fail closed，不放行「无声明」态）。"""
        refuse_before_network(EUROPE_PMC_BASE_URL, spec_with_domains())

    def test_declaring_a_different_host_does_not_admit_the_default_one(self) -> None:
        """声明了别的域名 ⇒ 默认域名也不放行（白名单判定的是实际 host，不是「有没有声明」）。"""
        refuse_before_network(EUROPE_PMC_BASE_URL, spec_with_domains("example.org"))


class TestPositiveControls:
    """正控制：证明上一条不是「怎么都不发请求」的空转。"""

    def test_positive_control_issues_exactly_the_expected_requests(self) -> None:
        store = FakeArtifactStore()
        transport = Transport({"EXT_ID": search_payload(real_record())})
        result, payload = run_tool(
            make_provider(transport, store=store), store, SEARCH_TOOL, search_args()
        )

        assert transport.count == 1, "合法 host ⇒ 恰好一次请求"
        assert getattr(result, "output_digest") is not None
        assert payload["ids"] == [REAL_PMID]
        assert transport.requests[0].url.host == "www.ebi.ac.uk"
        assert transport.requests[0].url.params.get("format") == "json"
        assert getattr(result, "status") is ToolResultStatus.SUCCEEDED

    def test_declaring_the_host_is_what_admits_it(self) -> None:
        """反向控制：把同一 host **声明进** `network_domains` ⇒ 同一请求被放行。

        证明拒绝的理由是**声明式白名单**，不是把某个 host 硬编码进了代码。
        """
        spec = spec_with_domains("eutils.ncbi.nlm.nih.gov")
        store = FakeArtifactStore()
        transport = Transport()
        provider = make_provider(transport, base_url=UNDECLARED_PUBLIC_HOST, store=store)
        args = search_args()
        call = make_call(SEARCH_TOOL, args)
        put_args(store, call, args)

        result = call_port(provider, spec, call)

        assert transport.count == 1, "声明内 host ⇒ 请求发出（且只发一次）"
        assert getattr(result, "status") is ToolResultStatus.SUCCEEDED

    def test_refusal_does_not_consume_the_throttle_state(self) -> None:
        """被拒的调用**不推进**节流时钟：同一 transport 上先被拒、再成功，仍恰好一次请求。

        判据要点：若被拒路径把 `_last_request_at` 前移（或先发请求再判策略），
        本条会看到 `count != 1`；节流间隔为 0 使断言与耗时无关。
        """
        store = FakeArtifactStore()
        transport = Transport({"EXT_ID": search_payload(real_record())})
        provider = make_provider(transport, store=store)
        rejecting = make_provider(
            transport,
            base_url="https://evil.example.com/europepmc/webservices/rest",
            store=store,
        )
        rejected = make_call(SEARCH_TOOL, search_args(), operation_key="op-reject")
        put_args(store, rejected, search_args())

        with pytest.raises(PermanentPortError):
            call_port(rejecting, PROVIDER, rejected)

        assert transport.count == 0, "被拒路径不得发请求"

        result, _payload = run_tool(provider, store, SEARCH_TOOL, search_args())
        assert transport.count == 1, "被拒调用不得干扰后续合法调用的请求计数"
        assert getattr(result, "status") is ToolResultStatus.SUCCEEDED

    def test_a_refused_provider_never_yields_a_result_record(self) -> None:
        """被拒 ⇒ 不产生产物（fail closed：没有 digest 可被下游当成功证据）。"""
        store = FakeArtifactStore()
        rejecting = make_provider(
            transport=Transport(),
            base_url="https://127.0.0.1/europepmc/webservices/rest",
            store=store,
        )
        call = make_call(SEARCH_TOOL, search_args())
        put_args(store, call, search_args())

        with pytest.raises(PermanentPortError):
            call_port(rejecting, PROVIDER, call)

        assert store.meta(f"tool-result:task-goal027:op-1:{SEARCH_TOOL}") is None, (
            "被拒的调用不得留下任何产物"
        )
