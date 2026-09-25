"""凭据生命周期的同源判据（GOAL-009 EC-05 / PLAN-20260920-125）。

`docs/integration/LIVE_MODEL_RUNBOOK.md` §8 把四件事写成固定标签表：**注入 / 轮换 / 撤销 /
可弃用额度**。本判据判**语义**与**同源**，不判文笔。

**最重要的两条（本判据存在的理由）**：

1. **「构造时快照」**：两个解析器都在构造时拷贝环境 ⇒ **已构造的实例**在来源被换掉或被撤销
   之后**仍按旧结论回答**；只有**新构造**的实例看到变化。「同一进程内改环境变量即生效」
   是**错的**——本判据把它钉成**成对断言**（旧实例不变 + 新实例变），只判一条都不算数。
2. **撤销的两条边界**：环境变量面撤销 ⇒ 门 **fail-closed** 关闭并点名凭据；
   但**注册表命中优先于环境变量** ⇒ 已 `register()` 的 ref **不会**因环境变量被清空而关门，
   必须 `unregister()`。少了第二条，读者会把「清空环境变量」当成万能撤销。

**不读真实凭据**：全部用**虚构值**驱动解析器与门；判据不读 `.env`、不打印任何值、不发起调用。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.contracts.fixtures import endpoint

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = REPO_ROOT / "docs/integration/LIVE_MODEL_RUNBOOK.md"

_CREDENTIAL_REF = "llm_main_key"
#: 环境变量面的**变量名**：必须与 `os.environ` 里的名字**逐字一致**。
#: Windows 上 `os.environ` 的查找是**大小写不敏感**的，但解析器把它拷贝成**普通 dict**，
#: 那里就是**大小写敏感**的 ⇒ 用小写名去查会得到 False（本判据第一版就这么红过）。
_ENV_VAR = "LLM_MAIN_KEY"
#: 虚构值（**不是**任何真实凭据，也不来自环境）：本判据只测布尔语义。
_FABRICATED = "fabricated-value-for-semantics-only"
_ROTATED = "fabricated-value-after-rotation"

#: §8 表格的**固定标签**（解析只认标签，不猜格式）。
_LABELS = ("注入", "轮换", "撤销", "可弃用额度")


def _runbook_text() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def _section_eight() -> str:
    """§8 的正文（到下一个二级标题为止）。解析失败就点名，不返回空串。"""
    text = _runbook_text()
    start = text.find("\n## 8.")
    assert start != -1, "the runbook no longer has a §8 credential-lifecycle section"
    rest = text[start + 1 :]
    end = rest.find("\n## ", 3)
    return rest if end == -1 else rest[:end]


def _row(label: str) -> str:
    prefix = f"| {label} |"
    for line in _section_eight().splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError(f"§8 no longer has a row labelled {label!r}")


def _gate(resolver: object) -> object:
    #: 本判据的靶子是**凭据生命周期**（快照 / 撤销）⇒ 另外两条开门条件（显式开关 /
    #: live runtime）**显式置为满足**，否则「撤销 ⇒ 关门」会被「开关没开」掩盖成恰好绿。
    return evaluate_live_run_gate(
        credentials=resolver,  # type: ignore[arg-type]
        endpoint=replace(endpoint(), credential_ref=_CREDENTIAL_REF),
        agent_runtime=OPENHANDS_RUNTIME,
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=True,
    )


class TestRotationIsASnapshotNotALiveRead:
    """**构造时快照**：生产路径的旧实例不变 + 新实例变——两条必须成对。

    精确到**构造方式**（实测 2026-09-21）：

    - 无参 `EnvCredentialResolver()`（生产路径）**拷贝** `os.environ` ⇒ 是快照；
    - 传 `environment=` 的 `EnvCredentialResolver` **按引用**持有那个映射 ⇒ 看得到改动；
    - `RegistryCredentialResolver` 两种都 `dict(...)` ⇒ 是快照。
    """

    def test_the_production_resolver_keeps_its_snapshot(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(_ENV_VAR, _FABRICATED)
        built_before = EnvCredentialResolver()  # 生产路径：无参 ⇒ 拷贝环境

        monkeypatch.delenv(_ENV_VAR)

        assert built_before.has(_ENV_VAR) is True, (
            "the production resolver copies the environment at construction; an already-built "
            "instance must keep answering from that snapshot"
        )

    def test_a_freshly_constructed_resolver_sees_the_revocation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(_ENV_VAR, _FABRICATED)
        monkeypatch.delenv(_ENV_VAR)

        assert EnvCredentialResolver().has(_ENV_VAR) is False, (
            "a newly constructed resolver must see the environment as it is now"
        )

    def test_an_injected_mapping_is_held_by_reference(self) -> None:
        """传 `environment=` 的形态**不是**快照——这条差异必须写明，否则会拿测试行为推生产。"""
        source = {_ENV_VAR: _FABRICATED}
        injected = EnvCredentialResolver(environment=source)

        source.clear()

        assert injected.has(_ENV_VAR) is False, (
            "the injected mapping is held by reference, so this shape does follow changes; "
            "§8 must not let readers infer production behaviour from it"
        )

    def test_the_registry_resolver_copies_its_mapping(self) -> None:
        source = {_ENV_VAR: _FABRICATED}
        resolver = RegistryCredentialResolver(environment=source)

        source.clear()

        assert resolver.has(_ENV_VAR) is True, (
            "RegistryCredentialResolver copies its mapping at construction"
        )

    def test_the_lookup_is_case_sensitive_on_the_copied_mapping(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`credential_ref` 必须与变量名**逐字一致**：拷贝出来的是普通 dict（大小写敏感）。"""
        monkeypatch.setenv(_ENV_VAR, _FABRICATED)

        assert EnvCredentialResolver().has(_ENV_VAR) is True
        assert EnvCredentialResolver().has(_ENV_VAR.lower()) is False, (
            "the copied mapping is a plain dict: looking up a differently-cased name must "
            "miss, even though os.environ itself would have matched it on Windows"
        )


class TestRevocationClosesTheGateFailClosed:
    """撤销 ⇒ 门关（fail-closed）并点名凭据；与「来源在 ⇒ 门开」成对。"""

    def test_a_present_source_opens_the_gate(self) -> None:
        gate = _gate(EnvCredentialResolver(environment={_CREDENTIAL_REF: _FABRICATED}))
        assert gate.open is True, getattr(gate, "reason", "")  # type: ignore[attr-defined]

    def test_a_revoked_source_closes_the_gate_and_names_the_credential(self) -> None:
        gate = _gate(EnvCredentialResolver(environment={}))
        assert gate.open is False, "revoking the source must close the gate (fail-closed)"  # type: ignore[attr-defined]
        assert _CREDENTIAL_REF in gate.reason, (  # type: ignore[attr-defined]
            "a closed gate must name the credential it could not resolve"
        )

    def test_an_emptied_source_also_closes_the_gate(self) -> None:
        """空串 == 不可解析（与 §8 的「清空或删除」一致）。"""
        gate = _gate(EnvCredentialResolver(environment={_CREDENTIAL_REF: ""}))
        assert gate.open is False  # type: ignore[attr-defined]


class TestTheRegistryFaceNeedsItsOwnRevocation:
    """注册表命中**优先于**环境快照 ⇒ 清空环境变量**不**关这个面的门。"""

    def test_a_registered_ref_survives_an_environment_revocation(self) -> None:
        resolver = RegistryCredentialResolver(environment={})
        resolver.register(_CREDENTIAL_REF, _FABRICATED)

        assert resolver.has(_CREDENTIAL_REF) is True, (
            "a registered ref is answered from the in-process registry; clearing the "
            "environment variable must not look like a revocation for this face"
        )

    def test_unregistering_closes_it(self) -> None:
        resolver = RegistryCredentialResolver(environment={})
        resolver.register(_CREDENTIAL_REF, _FABRICATED)
        resolver.unregister(_CREDENTIAL_REF)

        assert resolver.has(_CREDENTIAL_REF) is False, (
            "the registry face is revoked with unregister(), not by clearing the environment"
        )

    def test_the_environment_is_still_a_fallback_for_unregistered_refs(self) -> None:
        """注册表只对那些**注册过**的 ref 优先；未注册的仍按环境快照回答。"""
        resolver = RegistryCredentialResolver(environment={_CREDENTIAL_REF: _FABRICATED})
        assert resolver.has(_CREDENTIAL_REF) is True


class TestTheFourItemsAreWrittenDown:
    """四件事必须有明文（只判在场与指向，不判文笔）。"""

    def test_every_item_has_a_row(self) -> None:
        for label in _LABELS:
            assert _row(label), label

    def test_the_injection_row_points_at_the_resolver(self) -> None:
        assert "adapters/relay/credential_resolver.py" in _row("注入")

    def test_the_rotation_row_points_at_the_resolver(self) -> None:
        assert "adapters/relay/credential_resolver.py" in _row("轮换")

    def test_the_revocation_row_points_at_the_gate(self) -> None:
        assert "packages/application/model_relay/live_run_gate.py" in _row("撤销")

    def test_the_rotation_and_revocation_rows_carry_the_snapshot_semantics(self) -> None:
        """**行内**必须带「新构造」——只判「整节里出现过『快照』」会让改坏一行溜过去。

        这是本条判据的**第一次压测**发现的：把撤销行改写成「每次调用都读一次环境」，
        整节断言仍然绿（§8 别处还有「快照」字样）⇒ 断言必须落到**行**上。
        """
        for label in ("轮换", "撤销"):
            assert "新构造" in _row(label), (
                f"§8 的 {label!r} 行必须写明生效边界是「新构造」，"
                "否则「改环境变量即生效」这种错说法会重新溜进来"
            )

    def test_the_posix_injection_form_is_present(self) -> None:
        assert "set -a; . ./.env; set +a" in _section_eight(), (
            "the runbook must give the portable export form verbatim"
        )

    def test_the_snapshot_boundary_is_stated(self) -> None:
        section = _section_eight()
        assert "构造时" in section and "快照" in section, (
            "§8 must state that both resolvers snapshot at construction"
        )

    def test_the_registry_revocation_boundary_is_stated(self) -> None:
        assert "unregister()" in _section_eight(), (
            "§8 must say that the registry face needs unregister() — otherwise 'clear the "
            "env var' reads as a universal revocation"
        )

    def test_the_disposable_quota_and_the_discipline_are_both_stated(self) -> None:
        section = _section_eight()
        assert "免费可弃用额度" in section, "§8 must say the key is a disposable free quota"
        assert "不放松纪律" in section, (
            "§8 must say that the disposable quota does NOT relax credential discipline"
        )
