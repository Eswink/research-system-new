"""GOAL-20261117-114 EC-05：**消融台协议**在文档里成立，且与它的来源相逐字同源。

**为什么要单列一条协议**：配对消融的读数只需 `plan` 相的那一件产物；在十一相链上跑
6 次真实 run 的代价是 6 × 24–29 分钟（GOAL-113 实测 `8ba73c2a` = 28m46s），且任一相
失败就丢一对样本。`ablation_plan_probe_v1.yaml` 把一次 run 压到「检索 + 一次会话」，
并把失败面收窄到那一格。

**判什么**（缺一即判红）：

1. **文档形态**：单相、phase id 逐字 `plan`、`capability_execution: run_chain`、
   合约逐字 `research_report_plan`、输入/产物逐字；
2. **与来源相逐字同源**：能力集必须等于 `research_report_chain_v1.yaml` 的 `plan` 相
   （集合相等，不靠散文）—— 两处漂移会让「消融台上的读数」不再是那条链的读数；
3. **能编译**：`compile_protocol(...)` 给出 `plan`（不是 `None`）——协议作者写错能力名
   或角色名时，这一条先红，**在真实 run 之前**；
4. **不声明会话工具绑定**：`run_chain` 把本相能力连同 provider 一起排除 ⇒ 会话工具面为空
   ⇒ 不写绑定是唯一正确形态（越界绑定会被点名拒绝）。

**射程边界（如实登记）**：本判据判**声明面与编译面**，不判「真实 run 能跑通」——
后者要付费流量，在 live 判据里（EC-07），且 CI 上 `skip`（`skip` 不是 `PASS`）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from adapters.contracts.protocol_loaders import load_protocol
from packages.application.protocol_compile import compile_protocol
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[2]
_PROTOCOL = "ablation_plan_probe_v1.yaml"
_SOURCE = "research_report_chain_v1.yaml"
_PROTOCOL_ID = "ablation_plan_probe_v1_0_0"
_CONTRACT = "research_report_plan"
#: 本相**必须**用出厂检索面瞄准的那个 id（见 `test_the_phase_id_is_the_one_...`）。
RETRIEVAL_PHASE = "retrieval"


def _raw(name: str = _PROTOCOL) -> dict[str, Any]:
    path = _ROOT / "examples" / "protocols" / name
    loaded: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], loaded)


def _phases(name: str = _PROTOCOL) -> dict[str, dict[str, Any]]:
    return {phase["id"]: phase for phase in _raw(name)["phases"]}


def test_the_probe_declares_exactly_one_phase_in_the_required_shape() -> None:
    """**文档自己**写了单相与它的声明形态（不靠产品代码转述）。

    相 id 是 `retrieval`（不是 `plan`）：出厂检索面把两步链钉在 `RETRIEVAL_PHASE` 上，
    而 `planned_in_this_phase` 对不匹配的相**静默跳过** ⇒ 取名成别的，产品组合根在本协议上
    **不会执行任何检索**，失败随后落在合约的 `minimum_retrieved_sources` 上（归因错位）。
    """
    document = _raw()
    assert document["id"] == _PROTOCOL_ID, document["id"]
    phases = _phases()
    assert set(phases) == {RETRIEVAL_PHASE}, sorted(phases)

    plan = phases[RETRIEVAL_PHASE]
    assert plan.get("capability_execution") == "run_chain"
    assert plan.get("task_contract") == _CONTRACT
    assert plan.get("inputs") == ["input-brief:real_research_v1"]
    assert plan.get("outputs") == ["research_plan"]
    assert not plan.get("depends_on"), plan.get("depends_on")
    assert plan.get("required_roles") == [
        {"role": "research_director", "min_instances": 1, "max_instances": 1}
    ]


def test_the_phase_id_is_the_one_the_shipped_retrieval_face_targets() -> None:
    """相 id 必须**等于**出厂检索面瞄准的那个相（否则检索静默不跑）。"""
    from services.api.retrieval_wiring import RETRIEVAL_PHASE as SHIPPED

    assert RETRIEVAL_PHASE == SHIPPED, (
        "探针的相 id 与 `services/api/retrieval_wiring.RETRIEVAL_PHASE` 不同 ⇒ "
        "产品组合根在本协议上不会执行检索",
        RETRIEVAL_PHASE,
        SHIPPED,
    )


def test_the_probe_capabilities_are_the_source_phase_capabilities() -> None:
    """能力集必须与 `research_report_chain_v1.yaml` 的 `plan` 相**集合相等**。

    两处漂移的后果不是「协议不一样」，而是「消融台上的读数**不是**那条链的读数」——
    一份读数若来自另一份装配，它提供的分布位移不能拿去评判那条链的 `下一级`。
    """
    probe = set(_phases()[RETRIEVAL_PHASE]["required_capabilities"])
    source = set(_phases(_SOURCE)["plan"]["required_capabilities"])
    assert probe == source, {
        "only_in_probe": sorted(probe - source),
        "missing": sorted(source - probe),
    }


def test_the_probe_does_not_declare_session_tool_bindings() -> None:
    """`run_chain` ⇒ 会话工具面为空 ⇒ 不写绑定（写了会被点名拒绝）。"""
    assert "session_tool_bindings" not in _phases()[RETRIEVAL_PHASE]


def test_the_probe_compiles_and_the_source_phase_still_does() -> None:
    """两条协议都给出 `plan`（新协议写错、或改坏了来源相 ⇒ 这一条先红）。"""
    for name, phase_id in ((_PROTOCOL, RETRIEVAL_PHASE), (_SOURCE, "plan")):
        protocol = load_protocol(f"examples/protocols/{name}")
        result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
        assert result.plan is not None, (name, result.findings)
        phase_ids = [phase.id for phase in result.plan.phases]
        assert phase_id in phase_ids, (name, phase_ids)


def test_the_probe_is_the_only_phase_so_the_run_is_short() -> None:
    """单相是**成本事实**（不是风格）：相数 == 1 ⇒ 一次 run 只建一个会话。"""
    assert len(_phases()) == 1
