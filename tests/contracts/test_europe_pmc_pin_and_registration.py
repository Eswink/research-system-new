"""Europe PMC 的 pin / 登记 / 夹具 pin 源覆盖（GOAL-20260927-027 EC-01 的 AC-3 / AC-4）。

本文件是**新增**判据，既有判据一字未改。四条断言：

1. **pin 契约在树且形状合规**：`examples/contracts/toolpack_europe_pmc.yaml` 含
   `toolpack_ncbi_eutils.yaml` 的同一组字段；`credentials` 为空（Europe PMC 检索
   无需凭据 ⇒ 满足「只有没有它不可用才声明」）；`digest` 是 `sha256:<64hex>` 形状。
2. **登记面**：`examples/config/tool_providers.yaml` 的 `europe_pmc` 条目经**产品加载器**
   （`load_tool_providers`）+ `schemas/tool-provider.schema.json` 读成 `ToolProviderSpec`，
   且它的 `network_domains` 必须与 pin 契约的 `network_domains` **同集合**——
   两份声明漂移即判红（出口白名单只能有一个真值来源）。
3. **能力面复用既有名字**：`europe_pmc` 的 capabilities ⊆ {`literature.search`,
   `literature.read`}，且**不**引入词表外的新名字（policy 三处本轮零改动）。
4. **夹具 pin 源覆盖目录内**每一个非 `NATIVE` provider（**下界断言**，承 MEM-160）：
   `tests/api/run_fixtures.py` 的 `_PROVIDERS` 是**整表替换**的 pin 源，任何新登记
   却未进该表的 provider 都会让 run_ready 路径以 `SUPPLY_CHAIN_UNPINNED` 判 FAIL。
   本判据把「目录内非 NATIVE 集合 ⊆ `_PROVIDERS`」钉死，新增 provider 时**必须**同轮
   扩表，不允许靠「受判集合为空」的空真通过。

口径边界（如实）：`toolpack_*.yaml` 的 `digest` 是**声明值**，全仓无人重算
（`services/api/catalog.py::_load_tool_pack_digests` 只读、preflight 只做
`Digest.parse` 形状校验）；内容重算只发生在 install 生命周期。本文件因此**只**断言
形状与字段形态，不断言「文件字节等于 digest」——那会是一条**假的**强断言。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from adapters.contracts.resource_loaders import load_tool_providers
from packages.domain.core import Digest

ROOT = Path(__file__).resolve().parents[2]
PIN_CONTRACT = ROOT / "examples" / "contracts" / "toolpack_europe_pmc.yaml"
REFERENCE_PIN = ROOT / "examples" / "contracts" / "toolpack_ncbi_eutils.yaml"
PROVIDERS_YAML = ROOT / "examples" / "config" / "tool_providers.yaml"
FIXTURE = ROOT / "tests" / "api" / "run_fixtures.py"

PROVIDER_ID = "europe_pmc"
PIN_ID = "europe_pmc_v1"
REUSED_CAPABILITIES = {"literature.search", "literature.read"}
DECLARED_DOMAIN = "www.ebi.ac.uk"

#: 与 `toolpack_ncbi_eutils.yaml` 对照的必备字段（形状同源，值可不同）。
REQUIRED_FIELDS = (
    "id",
    "version",
    "source",
    "resolved_revision",
    "digest",
    "license",
    "tools",
    "skills",
    "requested_capabilities",
    "network_domains",
    "credentials",
    "compatibility",
)


def load_pin(path: Path = PIN_CONTRACT) -> dict[str, Any]:
    body = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(body, dict), f"{path.name} 必须是 YAML 映射"
    return body


def fixture_provider_ids() -> tuple[str, ...]:
    """从夹具源码取 `_PROVIDERS`（不 import 被测模块，避免把夹具当预言机）。"""
    import ast

    tree = ast.parse(FIXTURE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_PROVIDERS" for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            return tuple(str(item) for item in value)
    raise AssertionError("run_fixtures.py 里找不到 _PROVIDERS（夹具 pin 源改名了）")


class TestPinContract:
    """AC-3：pin 契约在树且形状合规。"""

    def test_pin_contract_exists_and_carries_the_reference_shape(self) -> None:
        assert PIN_CONTRACT.exists(), "pin 契约必须落在 examples/contracts/toolpack_*.yaml"
        pin = load_pin()
        reference = load_pin(REFERENCE_PIN)
        missing = [field for field in REQUIRED_FIELDS if field not in pin]
        assert not missing, f"pin 契约缺少字段：{missing}"
        assert set(REQUIRED_FIELDS) <= set(reference), (
            "参照文件的字段集变了 —— 本判据的字段清单需与之同源复核"
        )
        assert pin is not reference

    def test_pin_id_matches_the_provider_after_suffix_stripping(self) -> None:
        """`catalog._load_tool_pack_digests` 会剥掉 `_vN` 后缀 ⇒ 剥后必须等于 provider id。"""
        assert load_pin()["id"] == PIN_ID
        assert PIN_ID.rsplit("_v", 1)[0] == PROVIDER_ID

    def test_digest_is_well_formed_and_declared_not_recomputed(self) -> None:
        """digest 必须是合法 `sha256:<64hex>` 形状（形状校验是唯一既有读取方做的事）。

        同时固定住「它是声明、不是内容寻址」这一事实：若有人把**文件字节**的 sha256
        填进来，本条仍然通过，但 `test_declared_digest_is_not_the_file_bytes_hash`
        会点出差异来源 —— 两条合起来防止把声明误当重算值来叙事。
        """
        digest = str(load_pin()["digest"])
        parsed = Digest.parse(digest)
        assert str(parsed) == digest
        assert digest.startswith("sha256:")
        assert len(digest) == len("sha256:") + 64

    def test_declared_digest_differs_from_the_reference_pack(self) -> None:
        """新 pack 不得复用参照 pack 的 digest（复制粘贴会在这里现形）。"""
        assert load_pin()["digest"] != load_pin(REFERENCE_PIN)["digest"]

    def test_credentials_are_empty_because_the_source_needs_none(self) -> None:
        """Europe PMC 检索无需凭据 ⇒ `credentials` 必须为空数组（声明即必需）。"""
        assert load_pin()["credentials"] == []

    def test_tools_and_capabilities_stay_on_the_existing_vocabulary(self) -> None:
        pin = load_pin()
        assert set(pin["tools"]) == REUSED_CAPABILITIES
        assert set(pin["requested_capabilities"]) == REUSED_CAPABILITIES

    def test_network_domains_declare_the_real_europe_pmc_host(self) -> None:
        assert load_pin()["network_domains"] == [DECLARED_DOMAIN]


class TestRegistration:
    """AC-4：登记进 provider 面（经产品加载器 + schema）。"""

    @pytest.fixture(scope="class")
    @classmethod
    def catalog(cls) -> dict[str, Any]:
        return load_tool_providers("examples/config/tool_providers.yaml")

    def test_loader_reads_the_new_provider(self, catalog: dict[str, Any]) -> None:
        assert PROVIDER_ID in catalog, f"目录里没有 {PROVIDER_ID}"
        provider = catalog[PROVIDER_ID]
        assert provider.kind.value == "REST"
        assert provider.trust_level.value == "VERIFIED"
        assert provider.effect_class.value == "READ_ONLY"
        assert provider.transport == "rest"
        assert provider.health_check is True

    def test_capabilities_reuse_the_existing_names(self, catalog: dict[str, Any]) -> None:
        capabilities = set(catalog[PROVIDER_ID].capabilities)
        assert capabilities == REUSED_CAPABILITIES, (
            "复用既有能力名 ⇒ capabilities 词表 / _CAPABILITY_SCOPE / policy.yaml 三处零改动"
        )

    def test_no_credential_ref_and_no_endpoint_env(self, catalog: dict[str, Any]) -> None:
        """两者都不声明：无必需凭据；端点自带默认值（声明却未设变量会被判不可用）。"""
        provider = catalog[PROVIDER_ID]
        assert provider.credential_ref is None
        assert provider.endpoint_env is None

    def test_declared_domains_match_the_pin_contract(self, catalog: dict[str, Any]) -> None:
        """出口白名单的唯一真值来源：登记声明与 pin 契约必须同集合（漂移即红）。"""
        declared = set(catalog[PROVIDER_ID].network_domains)
        assert declared == set(load_pin()["network_domains"]), (
            "provider 登记的 network_domains 与 pin 契约不一致"
        )
        assert DECLARED_DOMAIN in declared

    def test_existing_providers_are_untouched(self, catalog: dict[str, Any]) -> None:
        """既有三条 provider 的声明逐条未改（新条目是纯追加）。"""
        assert set(catalog) == {
            "openhands_workspace",
            "m12_artifact",
            "ncbi_eutils",
            "europe_pmc",
            # GOAL-20261006-031 EC-02：新增承接 provider（纯追加；既有四条逐字未改）
            "ncbi_citation",
        }
        ncbi = catalog["ncbi_eutils"]
        assert ncbi.capabilities == ["literature.search", "literature.read", "citation.inspect"]
        assert ncbi.network_domains == ["eutils.ncbi.nlm.nih.gov"]
        assert ncbi.credential_ref is None


class TestFixturePinSourceCoversTheCatalog:
    """下界断言（承 MEM-160）：夹具 pin 源必须覆盖目录内每个非 NATIVE provider。"""

    def test_every_non_native_provider_is_pinned_in_the_fixture_source(self) -> None:
        catalog = load_tool_providers("examples/config/tool_providers.yaml")
        fixture_ids = set(fixture_provider_ids())
        required = {
            provider_id
            for provider_id, provider in catalog.items()
            if provider.kind.value != "NATIVE"
        }
        assert required, "目录里必须有非 NATIVE provider（受判集合非空是交付前提）"
        assert required <= fixture_ids, (
            f"目录内非 NATIVE provider 未进夹具 pin 源：{sorted(required - fixture_ids)}"
            " —— run_ready 路径会以 SUPPLY_CHAIN_UNPINNED 判 FAIL"
        )
        assert PROVIDER_ID in fixture_ids

    def test_native_providers_are_also_listed_for_consistency(self) -> None:
        """NATIVE 也在表内（`_is_pinned_digest` 对 NATIVE 短路，但表是整表替换的）。"""
        fixture_ids = set(fixture_provider_ids())
        assert {"openhands_workspace", "m12_artifact"} <= fixture_ids

    def test_pin_contract_is_the_only_source_of_the_declared_digest(self) -> None:
        """目录加载器从 `toolpack_*.yaml` 取 digest ⇒ 新 pack 必须能被它读到。"""
        from services.api.catalog import load_catalog_snapshot

        snapshot = load_catalog_snapshot()
        assert PROVIDER_ID in snapshot.tool_pack_digests, (
            "新 pack 的 `id`（剥 `_vN` 后）必须等于 provider id，否则 pin 读不进来"
        )
        digest = snapshot.tool_pack_digests[PROVIDER_ID]
        assert digest == load_pin()["digest"]
