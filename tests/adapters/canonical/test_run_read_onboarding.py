"""GOAL-20261005-030 EC-02 判据：**B 组承接 —— `run.read`**（以核实为准，不得为凑数硬接）。

**B 组核实结论（建档勘察的实测，逐条见 GOAL「事实层结论」第 3 条）**：

- **`run.read`：可行 ⇒ 本轮承接。** `RunStore` **确在 Port 面**
  （`packages/application/ports/run_store.py`：`list_runs` / `get_run` / `save_run`），
  **两个组合根都持有实例**（`composition.py` 的 `_SqliteStoreParts.runs_store` /
  `pg_composition.py` 的 `c["runs_store"]`）。承接内容是**新增读实现**
  （`adapters/canonical/run_read.py`；与 HTTP 读面 `GET /runs/{id}` 同一个 `get_run`，
  不新造第二套查询口径）。
- **`citation.validate`：不可行 ⇒ 本轮不接（如实登记，不硬接）。** 取数面确实可复用
  （`NcbiEutilsProvider._elink` → `normalize_elink`），判定语义也确实可以写死；**但**
  把它声明进 `tool_providers.yaml` 的 `ncbi_eutils.capabilities` 会**打红两条既有判据**：
  `tests/contracts/test_ncbi_provider_contract.py::…::test_list_tools_schema`（钉住
  `names == {literature_search, literature_read, citation_inspect}`）与
  `tests/contracts/test_europe_pmc_pin_and_registration.py::…::test_existing_providers_are_untouched`
  （钉住 `ncbi.capabilities == [literature.search, literature.read, citation.inspect]`）。
  两条都在 `tests/contracts/**` —— 本 GOAL 的 `fix_policy` **明文禁止**修改该面，
  消红必须动既有判据。故按「**不得为凑数硬接**」登记为**受限面**（解除条件：
  该两处 pin 的同轮同步授权）。

**本文件证什么**（`run.read` 的承接，四件事）：

1. **承接 = 声明 + 实现**：`tool_providers.yaml` 声明了它（`m12_artifact`），
   `CanonicalReadProvider.list_tools` 在**该 provider 的声明面**下真的列出它，
   出厂绑定表有一条 `("run.read", "m12_artifact", "run_read")`。
2. **真读得到**：给一个真在 `RunStore` 里的 run ⇒ 返回状态 / 协议 / 两个 manifest
   digest，**逐字段**与 store 里的事实一致（不是空壳）。
3. **缺依赖点名**：装配里没有 `RunStore` ⇒ **点名拒绝**（不返回空壳冒充「没有这个 run」）；
   run id 未知 ⇒ 点名拒绝（由 `RunStore` 自己抛）。
4. **承接 ≠ 放行且可区分**：`run.read` 在 `policy.yaml` 里**没有 `allow`** ⇒ 用真实
   `NativePolicyEvaluator(policy.yaml)` 求值必得 `DENY` + `used default policy effect`。
   这条与上一条**合起来**才是完整的句子：「已承接但未放行」**可区分**，
   **不得**用承接冒充放行。

**与既有判据的分工**（承 MEM-159：不互相顶替）：`tests/architecture/python/
test_capability_coverage_is_implemented.py` 判**声明面 ↔ 实现面**的落差（本轮同轮更新
射程清单与下界）；本文件判 `run.read` 这一条**具体能力**的行为（读得到 / 点名 / 未放行可区分）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from adapters.canonical import CanonicalReadProvider
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID, Digest
from packages.domain.enums import EffectClass, PolicyDecision, ProviderType, TrustLevel
from packages.domain.run import ResearchRun
from packages.domain.tools import ToolProviderSpec
from services.api.session_tool_support import DEFAULT_SESSION_TOOL_BINDINGS

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_PROVIDER_ID = "m12_artifact"
_CAPABILITY = "run.read"
_TOOL_ID = "run_read"


class _FakeRunStore:
    """最小 `RunStore`（结构实现 Port 的三件套；只服务本判据）。"""

    def __init__(self, runs: dict[str, ResearchRun]) -> None:
        self._runs = runs

    def list_runs(self, project_id: str | None = None) -> list[ResearchRun]:
        return [
            run for run in self._runs.values() if project_id is None or run.project_id == project_id
        ]

    def get_run(self, run_id: str) -> ResearchRun:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise InvalidInputError(f"unknown run id: {run_id}") from exc

    def save_run(self, run: ResearchRun) -> None:
        self._runs[run.id.value] = run


def _run() -> ResearchRun:
    return ResearchRun(
        id=ID.generate(),
        project_id="example-project",
        protocol_id="capabilities_used_in_a_run_v1_0_0",
        state="SUCCEEDED",
        manifest_digest=Digest.of_bytes(b"manifest"),
        manifest_semantic_digest=Digest.of_bytes(b"semantic"),
    )


def _spec(*capabilities: str) -> ToolProviderSpec:
    return ToolProviderSpec(
        id=_PROVIDER_ID,
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.BUILT_IN,
        capabilities=list(capabilities),
        effect_class=EffectClass.READ_ONLY,
    )


def _provider(runs: Any) -> CanonicalReadProvider:
    return CanonicalReadProvider(
        FakeArtifactStore(), FakeEvidenceLedger(), run_store=runs, spill_threshold_bytes=1
    )


def _spilled(provider: CanonicalReadProvider, args: dict[str, object]) -> dict[str, Any]:
    """经**真实执行路径**读一次（参数制品 → digest 校验 → provider.execute → 结果落盘）。"""
    import json

    from packages.domain.core import Timestamp
    from packages.domain.enums import ToolCallStatus
    from packages.domain.tools import ToolCallRecord

    operation_key = _TOOL_ID
    content = json.dumps(args, ensure_ascii=False, sort_keys=True).encode("utf-8")
    from packages.domain.artifacts import Artifact

    store = provider._artifacts  # noqa: SLF001 - 判据侧：造参数制品要走真 store
    store.put(
        Artifact(
            id=f"tool-args:task-1:{operation_key}",
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="test",
            classification="tool-args",
        ),
        content,
    )
    record = ToolCallRecord(
        task_id="task-1",
        attempt=1,
        operation_key=operation_key,
        tool_id=_TOOL_ID,
        capability=_CAPABILITY,
        argument_digest=Digest.of_bytes(content),
        status=ToolCallStatus.REQUESTED,
        recorded_at=Timestamp.now(),
    )
    result = provider.execute(_spec("artifact.read", _CAPABILITY), record)
    from packages.application.tool_plane.results import fetch_spilled_result

    raw = fetch_spilled_result(store, result)
    assert raw is not None, "结果必须落盘（内容可取回）"
    parsed: dict[str, Any] = json.loads(raw.decode("utf-8"))
    return parsed


class TestTheCapabilityIsDeclaredImplementedAndBound:
    """① 承接 = 声明 + 实现 + 绑定，三者同轮在场。"""

    def test_the_catalog_declares_it_on_this_provider(self) -> None:
        """出厂目录（`tool_providers.yaml`）在 `m12_artifact` 上声明了 `run.read`。"""
        from services.api.catalog import load_catalog_snapshot

        spec = load_catalog_snapshot().tool_providers[_PROVIDER_ID]
        assert _CAPABILITY in spec.capabilities, spec.capabilities

    def test_the_provider_lists_it_when_declared(self) -> None:
        """实现面：声明了 ⇒ `list_tools` 真的把它列出来（并承载在专属 tool id 上）。"""
        provider = _provider(_FakeRunStore({}))
        tools = provider.list_tools(_spec("artifact.read", _CAPABILITY))
        carried = {tool.id for tool in tools if _CAPABILITY in tool.capabilities}
        assert carried == {_TOOL_ID}, (carried, [tool.id for tool in tools])

    def test_the_factory_binding_table_carries_it(self) -> None:
        """出厂绑定表有一条指向本 provider 与专属 tool id 的条目。"""
        bindings = {
            tool_name: (provider_id, tool_id)
            for tool_name, provider_id, tool_id in DEFAULT_SESSION_TOOL_BINDINGS
        }
        assert bindings.get(_CAPABILITY) == (_PROVIDER_ID, _TOOL_ID), sorted(bindings)

    def test_it_is_not_listed_when_the_provider_does_not_declare_it(self) -> None:
        """两向：provider **未声明** ⇒ 不进工具面（防「实现了就无条件暴露」）。"""
        provider = _provider(_FakeRunStore({}))
        tools = provider.list_tools(_spec("artifact.read"))
        assert all(_CAPABILITY not in tool.capabilities for tool in tools), [
            tool.id for tool in tools
        ]


class TestItActuallyReadsTheRun:
    """② 真读得到：逐字段与 `RunStore` 里的事实一致。"""

    def test_the_run_fields_round_trip(self) -> None:
        run = _run()
        provider = _provider(_FakeRunStore({run.id.value: run}))

        payload = _spilled(provider, {"run_id": run.id.value})

        assert payload["run_id"] == run.id.value, payload
        assert payload["project_id"] == run.project_id, payload
        assert payload["protocol_id"] == run.protocol_id, payload
        assert payload["state"] == str(run.state), payload
        assert payload["manifest_digest"] == str(run.manifest_digest), payload
        assert payload["manifest_semantic_digest"] == str(run.manifest_semantic_digest), payload

    def test_an_unfrozen_run_reports_null_not_a_substitute(self) -> None:
        """未冻结 ⇒ `null`（**不**回落成别的值冒充已冻结）。"""
        run = replace(_run(), manifest_digest=None, manifest_semantic_digest=None)
        provider = _provider(_FakeRunStore({run.id.value: run}))

        payload = _spilled(provider, {"run_id": run.id.value})

        assert payload["manifest_digest"] is None, payload
        assert payload["manifest_semantic_digest"] is None, payload


class TestMissingDependenciesAndUnknownIdsAreNamed:
    """③ 缺依赖 / 未知 id 一律**点名**（不静默、不返回空壳）。"""

    def test_without_a_run_store_the_tool_is_named_unavailable(self) -> None:
        provider = CanonicalReadProvider(FakeArtifactStore(), FakeEvidenceLedger())
        with pytest.raises(InvalidInputError) as excinfo:
            _spilled(provider, {"run_id": "any"})
        assert "RunStore" in str(excinfo.value), str(excinfo.value)

    def test_a_missing_run_id_is_refused(self) -> None:
        provider = _provider(_FakeRunStore({}))
        with pytest.raises(InvalidInputError) as excinfo:
            _spilled(provider, {})
        assert "run_id" in str(excinfo.value), str(excinfo.value)

    def test_an_unknown_run_id_is_named(self) -> None:
        provider = _provider(_FakeRunStore({}))
        with pytest.raises(InvalidInputError) as excinfo:
            _spilled(provider, {"run_id": "no-such-run"})
        assert "no-such-run" in str(excinfo.value), str(excinfo.value)


class TestOnboardedIsNotGrantedAndTheDifferenceIsVisible:
    """④ 承接 ≠ 放行，且二者在判据上**可区分**（本类的存在就是那条分界）。"""

    def test_the_catalog_declares_it_but_the_policy_does_not_allow_it(self) -> None:
        """**同一进程里同时断言两件事**：目录声明了它，而策略面拒绝它。

        只断言其一都会让「已承接」冒充「已跑通」。
        """
        from packages.application.policy.native import NativePolicyEvaluator
        from packages.application.ports.policy_evaluator import PolicyRequest
        from packages.application.preflight.policy_check import policy_scope_for
        from services.api.catalog import load_catalog_snapshot, load_policy_definition

        declared = load_catalog_snapshot().tool_providers[_PROVIDER_ID].capabilities
        assert _CAPABILITY in declared, (
            "本判据的前提是「已承接」——目录没有它说明承接被移除了",
            declared,
        )

        policy = load_policy_definition()
        assert policy is not None, "policy.yaml must be loadable"
        decision = NativePolicyEvaluator(policy).evaluate(
            PolicyRequest(
                actor="agent:goal030",
                capability=_CAPABILITY,
                action="execute",
                scope=policy_scope_for(_CAPABILITY),
                resource=_CAPABILITY,
            )
        )
        assert decision.decision is PolicyDecision.DENY, (
            "`run.read` 未被放行是**如实状态**：承接 ≠ 放行（放行需用户拍板）",
            decision.decision,
            decision.reason,
        )
        assert decision.reason == "used default policy effect", decision.reason
