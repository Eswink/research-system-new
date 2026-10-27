"""GOAL-20261027-098 EC-01：**创新点的作者与评审者在结构上不是同一个东西**。

**它补哪一格**（本轮建档实测，不是推断）：`direction_to_report_v2.yaml` 的 `novelty` 相
（当时 `:107-108`）与 `review` 相（当时 `:165-170`）**都**点名 `novelty_reviewer`。而
`protocol_compile/assignments.py` 按 `agent_candidates.get(role)` 取前 N 个、`resolution.py`
的 `agent_candidates` 只按 `agent.role == role_id` 过滤 + 排序、`selection.py::select_agents`
同样只吃 `role_id` —— **三条路都不看 phase**。⇒ 同一角色在两相**必然**选到同一个 agent
实例（`novelty_a`，`minimax-m3`）：`review` 相那两个 `review_decision` 里有一个是
「评审自己刚写的声明」。判据数的是「正文里出现了那个标识」，而 `novelty_claim` 本来就在
`novelty_a` 的提示词里（`review` 的 `inputs` 含 `novelty:novelty_claim`）⇒ 复述是
**结构必然**，不构成「独立评审者认可」。

**本文件判三件事**（缺一即判红）：

1. **角色面**：`novelty` 相的作者角色 ≠ `review` 相任一评审者角色；
2. **实例面**：两相解析到的 **agent id 不同**，且 `(endpoint, model_name)` 也不同
   （只判 id 不够 —— GOAL-084 已证明 agent 名与底层模型可以完全脱钩）；
3. **一般性**（不只是 v2）：**任何**出厂协议里，「某相的评审者」不得同时是「它评审的那件
   产物的作者」。这条是**跨协议**的，因为本轮修的缺陷形态与 v2 无关 —— 换一份协议照样
   能写出同一个形状。

**反证臂**：把 `novelty` 相的角色改回 `novelty_reviewer`（真文件实测）⇒ 判据**点名判红**，
并按 raw `sha256` 逐字节复原。没有这一臂，「两相不同」可能只是「恰好写了两行」。"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from adapters.contracts.protocol_loaders import load_protocol
from adapters.contracts.roles_loaders import load_agents, load_roles
from packages.application.preflight.review_independence import (
    describe_target,
    resolve_agent_targets,
)
from packages.application.protocol_compile import compile_protocol
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[2]
_PROTOCOLS = _ROOT / "examples" / "protocols"
_PROTOCOL = "direction_to_report_v2.yaml"
_PROTOCOL_ID = "direction_to_report_v2_0_0"

#: 本协议的两相与它们的角色（本轮之后：作者 `novelty_author`、评审者 `novelty_reviewer`）。
_AUTHOR_PHASE = "novelty"
_REVIEW_PHASE = "review"
_AUTHOR_ROLE = "novelty_author"
_REVIEWER_ROLE = "novelty_reviewer"
_AUTHOR_AGENT = "novelty_writer"
_REVIEWER_AGENT = "novelty_a"


def _raw(name: str = _PROTOCOL) -> dict[str, Any]:
    path = _PROTOCOLS / name
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _phases(name: str = _PROTOCOL) -> dict[str, dict[str, Any]]:
    return {str(phase["id"]): cast(dict[str, Any], phase) for phase in _raw(name)["phases"]}


def _roles_of(phase: dict[str, Any]) -> set[str]:
    return {str(item["role"]) for item in phase.get("required_roles") or []}


def _compiled(name: str = _PROTOCOL) -> Any:
    protocol = load_protocol(f"examples/protocols/{name}")
    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    return result.plan


# --- 1. 角色面 ---------------------------------------------------------------


def test_the_author_role_is_not_the_reviewer_role() -> None:
    """(1) `novelty` 相的作者角色 ≠ `review` 相任一评审者角色（按文件字节判）。"""
    phases = _phases()
    author_roles = _roles_of(phases[_AUTHOR_PHASE])
    reviewer_roles = _roles_of(phases[_REVIEW_PHASE])
    assert author_roles == {_AUTHOR_ROLE}, author_roles
    assert _REVIEWER_ROLE in reviewer_roles, reviewer_roles
    overlap = author_roles & reviewer_roles
    assert not overlap, (
        "the novelty author role is also a reviewer role in the same protocol "
        f"(a self-review shape): {sorted(overlap)}"
    )


def test_the_author_role_is_not_a_reviewer_panel_role() -> None:
    """(1) 作者**不是**评审者：`review_panel_role` 必须不是 `REVIEWER`。

    这一格不是措辞：`is_reviewer()` 只读 `role.review_panel_role`，为假时才**不会**把被评
    对象塞进它的提示词。若作者也被标成 `REVIEWER`，它会收到一份「被评对象」——而那是
    它自己要写的东西。
    """
    roles = load_roles("examples/config/roles.yaml")
    assert _AUTHOR_ROLE in roles, sorted(roles)
    assert roles[_AUTHOR_ROLE].review_panel_role.value != "REVIEWER", (
        "novelty_author must not be a review-panel role: it is the author, not a reviewer"
    )


def test_the_reviewer_role_is_still_a_reviewer() -> None:
    """(1) 反向：`novelty_reviewer` **仍然**是 `REVIEWER`（拆开作者不等于削弱评审面）。"""
    roles = load_roles("examples/config/roles.yaml")
    assert roles[_REVIEWER_ROLE].review_panel_role.value == "REVIEWER"


# --- 2. 实例面 ---------------------------------------------------------------


def test_the_two_roles_resolve_to_different_agents() -> None:
    """(2) 两相解析到的 **agent id 不同**（按编译期 `agent_candidates` 判）。"""
    plan = _compiled()
    authors = plan.agent_candidates.get(_AUTHOR_ROLE) or []
    reviewers = plan.agent_candidates.get(_REVIEWER_ROLE) or []
    assert authors == [_AUTHOR_AGENT], authors
    assert reviewers == [_REVIEWER_AGENT], reviewers
    assert set(authors) & set(reviewers) == set(), (
        f"the author and the reviewer resolve to the same agent instance: {authors}"
    )


def test_the_two_agents_land_on_different_models() -> None:
    """(2) `(endpoint, model_name)` 也不同 —— 只判 agent id 会漏掉「换个名字同一个模型」。"""
    plan = _compiled()
    catalog = load_catalog_snapshot()
    targets: dict[str, set[str]] = {}
    for agent_id in (_AUTHOR_AGENT, _REVIEWER_AGENT):
        agent = catalog.agents[agent_id]
        resolved = resolve_agent_targets(
            agent_id, agent, catalog, resolved_model_id=plan.resolved_models.get(agent_id)
        )
        assert resolved.resolved, resolved.problems
        targets[agent_id] = {describe_target(item) for item in resolved.targets}
    shared = targets[_AUTHOR_AGENT] & targets[_REVIEWER_AGENT]
    assert not shared, (
        "the author and the reviewer can land on the same execution target "
        f"(endpoint/model_name): {sorted(shared)}"
    )
    # 四个不同的底层模型：生产侧 + 三位评审者 + 作者，彼此全部不同。
    author_target = sorted(targets[_AUTHOR_AGENT])
    assert len(author_target) == 1, author_target
    assert author_target[0].endswith("/deepseek-v4-pro-0813"), author_target


def test_the_phase_assignments_name_the_author_in_the_author_phase() -> None:
    """(2) 编译期**相位投影**里，作者只出现在作者相、评审者只出现在评审相。"""
    plan = _compiled()
    assignments = {item.phase_id: item.role_assignments for item in plan.phase_assignments}
    assert assignments[_AUTHOR_PHASE].get(_AUTHOR_ROLE) == (_AUTHOR_AGENT,)
    assert assignments[_AUTHOR_PHASE].get(_REVIEWER_ROLE) is None
    assert assignments[_REVIEW_PHASE].get(_REVIEWER_ROLE) == (_REVIEWER_AGENT,)
    assert assignments[_REVIEW_PHASE].get(_AUTHOR_ROLE) is None


# --- 3. 一般性：跨协议的「自评」形态 ----------------------------------------


def _panel_roles() -> dict[str, str]:
    """出厂角色 → `review_panel_role`（`load_roles` 走 schema 校验，不另造一份）。"""
    return {
        role_id: role.review_panel_role.value
        for role_id, role in load_roles("examples/config/roles.yaml").items()
    }


def self_review_shapes(name: str) -> list[tuple[str, str, str, list[str]]]:
    """一份协议里的**自评**形态：`[(评审相, 产出方相, 产物名, 相交角色)]`。

    判法（只读文件字节，不猜执行序）：对每个「声明了 `REVIEWER` 角色」的相，看它的
    **跨相输入** `producer:artifact`；若该产物确实是产出方相 `outputs` 里的名字，而产出方
    相 `required_roles` 与评审相的评审者角色**有交集** ⇒ 那一位既写又评。
    """
    phases = _phases(name)
    panel = _panel_roles()
    shapes: list[tuple[str, str, str, list[str]]] = []
    for phase_id, phase in phases.items():
        reviewers = {role for role in _roles_of(phase) if panel.get(role) == "REVIEWER"}
        if not reviewers:
            continue
        for item in phase.get("inputs") or []:
            text = str(item)
            if ":" not in text:
                continue
            producer, artifact = text.split(":", 1)
            upstream = phases.get(producer)
            if upstream is None or artifact not in (upstream.get("outputs") or []):
                continue
            both = sorted(reviewers & _roles_of(upstream))
            if both:
                shapes.append((phase_id, producer, artifact, both))
    return shapes


def test_no_shipped_protocol_reviews_its_own_output() -> None:
    """(3) **跨协议**：出厂协议里不存在「某一相的评审者同时是它评审的那件产物的作者」。

    这是本轮的靶子形态的**一般化**：缺陷与 v2 无关 —— 换一份协议照样能写出同一个形状，
    所以判据必须遍历出厂协议集合，而不是只钉住 v2 那一处。
    """
    offenders: dict[str, list[tuple[str, str, str, list[str]]]] = {}
    for path in sorted(_PROTOCOLS.glob("*.yaml")):
        shapes = self_review_shapes(path.name)
        if shapes:
            offenders[path.name] = shapes
    assert not offenders, (
        "these shipped protocols let a reviewer review a phase it authored "
        f"(self-review): {offenders}"
    )


def test_the_scan_finds_the_shape_when_it_is_present() -> None:
    """(3) 反证臂：把作者角色改回 `novelty_reviewer` ⇒ 上面那条**点名判红**。

    按压在**真文件**上做（改字节 → 判据必须红 → 按 raw `sha256` 逐字节复原）。按压用
    **真实的缺陷形态**（写回本轮修复前的那一行），不是合成一个别的错。
    """
    path = _PROTOCOLS / _PROTOCOL
    original = path.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    pristine = _phases()
    author_line = "      - {role: novelty_author, min_instances: 1, max_instances: 1}\n"
    reviewer_line = "      - {role: novelty_reviewer, min_instances: 1, max_instances: 1}\n"
    # 作者相里**唯一**那一行 `novelty_author` 换回 `novelty_reviewer`（修复前的形态）。
    assert pristine[_AUTHOR_PHASE]["required_roles"] == [
        {"role": _AUTHOR_ROLE, "min_instances": 1, "max_instances": 1}
    ]
    text = original.decode("utf-8")
    start = text.index(author_line)
    pressed = (text[:start] + reviewer_line + text[start + len(author_line) :]).encode("utf-8")
    assert hashlib.sha256(pressed).hexdigest() != before
    try:
        path.write_bytes(pressed)
        shapes = self_review_shapes(_PROTOCOL)
        assert shapes, (
            "the self-review scan did not flag the pre-fix shape "
            "(a reviewer role authoring the artifact it then reviews) — "
            "that means the scan cannot see the defect it exists to catch"
        )
        # 形态是 `(评审相, 产出方相, 产物名, 相交角色)`：评审相 `review` 在评
        # 产出方相 `novelty` 写的 `novelty_claim`，而相交角色就是 `novelty_reviewer`。
        first = shapes[0]
        assert first[0] == _REVIEW_PHASE, shapes
        assert first[1] == _AUTHOR_PHASE, shapes
        assert first[2] == "novelty_claim", shapes
        assert first[3] == [_REVIEWER_ROLE], shapes
        assert _REVIEWER_ROLE in {role for item in shapes for role in item[3]}, shapes
        # 角色面那条也判红（两条独立判据都咬得住）。
        phases = _phases()
        assert _roles_of(phases[_AUTHOR_PHASE]) & _roles_of(phases[_REVIEW_PHASE])
    finally:
        path.write_bytes(original)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before, "press archive restore failed"


def test_the_scan_is_clean_on_the_real_tree_after_the_press() -> None:
    """按压之后真实树仍干净（复原是真的，不是「按压时刚好也绿」）。"""
    assert self_review_shapes(_PROTOCOL) == []


# --- 交付面：装配与模型目录 --------------------------------------------------


def test_the_author_agent_is_bound_to_a_fifth_distinct_model() -> None:
    """作者绑定的模型与**生产侧 + 三位评审者**都不同（四个不同的底层模型）。"""
    agents = load_agents("examples/config/agents.yaml")
    assert agents[_AUTHOR_AGENT].role == _AUTHOR_ROLE
    catalog = load_catalog_snapshot()
    plan = _compiled()
    mine = resolve_agent_targets(
        _AUTHOR_AGENT,
        catalog.agents[_AUTHOR_AGENT],
        catalog,
        resolved_model_id=plan.resolved_models.get(_AUTHOR_AGENT),
    )
    assert mine.resolved, mine.problems
    others = {
        "reviewer_a": "reviewer_a",
        "reviewer_b": "reviewer_b",
        "novelty_a": "novelty_a",
        "researcher": "domain_a",
    }
    for label, agent_id in others.items():
        theirs = resolve_agent_targets(
            agent_id,
            catalog.agents[agent_id],
            catalog,
            resolved_model_id=plan.resolved_models.get(agent_id),
        )
        shared = mine.targets & theirs.targets
        assert not shared, (
            f"the novelty author shares an execution target with {label} ({agent_id}): "
            f"{[describe_target(item) for item in sorted(shared)]}"
        )


def test_the_contract_and_the_phase_are_still_the_same_ones() -> None:
    """零回归：作者的更换**没有**动合约、产物名与跨相边（只换了写它的角色）。"""
    phases = _phases()
    assert phases[_AUTHOR_PHASE]["task_contract"] == "novelty_claim_proposal"
    assert phases[_AUTHOR_PHASE]["outputs"] == ["novelty_claim"]
    assert phases[_AUTHOR_PHASE]["inputs"] == ["retrieval:retrieval_report"]
    assert f"{_AUTHOR_PHASE}:novelty_claim" in phases[_REVIEW_PHASE]["inputs"]
    assert f"{_AUTHOR_PHASE}:novelty_claim" in phases["plan"]["inputs"]


def test_the_protocol_still_compiles_with_zero_errors() -> None:
    """零回归：七相、零 ERROR（新角色没有把编译面搞坏）。"""
    plan = _compiled()
    assert plan.protocol_id == _PROTOCOL_ID
    assert tuple(phase.id for phase in plan.phases) == (
        "question",
        "retrieval",
        "novelty",
        "plan",
        "experiment",
        "review",
        "report",
    )


def test_the_author_is_in_the_shipped_team_pool() -> None:
    """池里必须有作者（缺 ⇒ 编译期 `ROLE_CAPACITY` ⇒ run 起不来；与评审者同一条理由）。"""
    settings = load_project_settings()
    catalog = load_catalog_snapshot()
    template = catalog.team_templates[str(settings.team_template_id)]
    pool = dict(template.roles)
    assert _AUTHOR_ROLE in pool, sorted(pool)
    assert int(cast(Any, pool[_AUTHOR_ROLE]).max_instances) == 1


@pytest.mark.parametrize("name", sorted(path.name for path in _PROTOCOLS.glob("*.yaml")))
def test_every_shipped_protocol_still_loads(name: str) -> None:
    """遍历面非空且每份协议仍可解析（受判面不是「恰好只剩一份」）。"""
    assert _phases(name), name
