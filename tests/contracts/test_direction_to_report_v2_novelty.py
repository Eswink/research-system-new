"""GOAL-20261026-097 EC-04：**创新点有两面**（声明面 + 评审面），且两面互相引用。

**它补哪一格**（本轮建档实测）：`packages/domain/` 里 `novel`/`idea` 零命中、
`rg -iln "novelty" packages/ services/ adapters/` **零条** ⇒ 「这项研究与最近的前人工作
差在哪」从未被写下、也从未被任何模型判过。而 `novelty_reviewer`
（`examples/config/roles.yaml`）是**死配置**：无 `review_panel_role` ⇒ `NONE`、
`agents.yaml` 无绑定、无协议点名 ⇒ 域层走 `"role not required by protocol"`。

**四件事逐条取证**（缺一即判红）：

1. 新协议 `direction_to_report_v2.yaml` **七相编译通过**，`novelty` 在 `retrieval` 与
   `plan` 之间（依赖链与跨相边两条都判）；
2. 声明的 `nearest_prior` **至少一条命中本 run 检索证据里真实出现的标识**；
   反证：换成不存在的标识 ⇒ **点名判红**；
3. `novelty_reviewer` 被**激活**（理由逐字 `"role is required by protocol"`）、
   `is_reviewer()` 为真、且它的判据面引用**同一个检索标识**（两面互相引用）；
4. **独立模型**：新 agent 的目标与生产侧、与另两位评审者的目标**都不同**。

**如实边界**：本文件判的是**声明面 + 结构面**（编译、激活、独立性、判据咬合）。
「模型真的在那次 run 里写出了合格的声明、评审者也真的引用了那个标识」属**真跑**证据，
在 EC-02 的取证文件与 `tests/e2e/` 里，不在这里假装。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from adapters.contracts.protocol_loaders import load_protocol
from adapters.contracts.roles_loaders import load_roles
from packages.application.protocol_compile import compile_protocol
from packages.application.run_orchestration.novelty_claim import (
    NoveltyClaim,
    novelty_claim,
)
from packages.application.run_orchestration.novelty_claim_step import (
    NOVELTY_CONTRACT_ID,
    novelty_verdict,
)
from packages.application.run_orchestration.review_material import is_reviewer
from packages.domain.activation import activate_roles
from packages.domain.enums import ReviewPanelRole
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[2]
_PROTOCOL = "direction_to_report_v2.yaml"
_PROTOCOL_ID = "direction_to_report_v2_0_0"
_PHASES = ("question", "retrieval", "novelty", "plan", "experiment", "review", "report")
_NOVELTY_ROLE = "novelty_reviewer"
_NOVELTY_AGENT = "novelty_a"


def _raw() -> dict[str, Any]:
    path = _ROOT / "examples" / "protocols" / _PROTOCOL
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _compiled() -> Any:
    protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    return result.plan


def test_the_protocol_declares_seven_phases_with_novelty_in_between() -> None:
    """(1) 文档自己写七相，`novelty` 在 `retrieval` 与 `plan` 之间。"""
    phases = {phase["id"]: phase for phase in _raw()["phases"]}
    assert tuple(phases) == _PHASES, tuple(phases)
    assert phases["novelty"]["depends_on"] == ["retrieval"]
    assert phases["novelty"]["inputs"] == ["retrieval:retrieval_report"]
    assert phases["novelty"]["task_contract"] == NOVELTY_CONTRACT_ID
    assert phases["novelty"]["outputs"] == ["novelty_claim"]
    # plan 站在 novelty 的下游，且 review 把声明的正文当**被评对象**。
    assert "novelty" in phases["plan"]["depends_on"]
    assert "novelty:novelty_claim" in phases["plan"]["inputs"]
    assert "novelty:novelty_claim" in phases["review"]["inputs"]


def test_the_retrieval_contract_tells_the_model_the_search_already_ran() -> None:
    """检索格的合约必须**明确说**检索已由运行链做完（真实 run 实测的缺陷）。

    实测：`research_question_retrieval`（被另两份协议共用）只写覆盖判据，真实模型于是把
    「去探索/去检索」当成自己的活 —— 第一句 `I'll start by exploring the repository
    structure…` 就停在那里（本相会话工具面是**空**的），制品里没有 `retrieval_report` 块，
    下游解析失败。v2 因此用**自己那份**合约（不改共用的那份，C-2）。
    """
    contracts: Any = yaml.safe_load(
        (_ROOT / "examples" / "contracts" / "task_contracts.yaml").read_text(encoding="utf-8")
    )["task_contracts"]
    contract_id = _raw()["phases"][1]["task_contract"]
    assert contract_id == "retrieval_report_from_the_run_chain", contract_id
    purpose = contracts[contract_id]["purpose"]
    assert "already been executed" in purpose, purpose[:200]
    assert "no tools" in purpose
    assert "retrieval_report" in purpose and "fenced JSON block" in purpose
    # 覆盖判据**逐字**沿用（不放松任何一维）。
    assert (
        contracts[contract_id]["acceptance_criteria"]
        == contracts["research_question_retrieval"]["acceptance_criteria"]
    )


def test_the_protocol_compiles_with_zero_errors() -> None:
    """(1) 编译零 ERROR，且两条跨相边（plan ← novelty、review ← novelty）都成立。"""
    plan = _compiled()
    compiled = {phase.id: phase for phase in plan.phases}
    assert tuple(compiled) == _PHASES
    edges = {
        phase.id: [(item[0], item[1]) for item in phase.cross_phase_inputs] for phase in plan.phases
    }
    assert ("novelty", "novelty_claim") in edges["plan"]
    assert ("novelty", "novelty_claim") in edges["review"]
    # C-1：两个不消费声明输入的执行体仍未声明（与 v1 同一条纪律）。
    assert edges["experiment"] == []
    assert edges["report"] == []


def test_the_novelty_contract_is_reachable_and_shipped() -> None:
    """声明面：合约在出厂文件里，且被协议点名（不靠在判据里手写常量）。"""
    contracts: Any = yaml.safe_load(
        (_ROOT / "examples" / "contracts" / "task_contracts.yaml").read_text(encoding="utf-8")
    )["task_contracts"]
    contract = contracts[NOVELTY_CONTRACT_ID]
    assert "nearest_prior" in contract["purpose"]
    assert contract["acceptance_criteria"] == [
        {"type": "ARTIFACT_EXISTS", "artifact": "novelty_claim"}
    ]


# --- 声明面的判定（2） -------------------------------------------------------


def _retrieved_evidence(identifier: str) -> tuple[Any, Any]:
    """一份**工具证据**（内容里带 `identifier`）+ 它的 `Evidence` 记录。

    判据自己造事实：`sources_of` 从工具结果内容的 `articles[].pmid` 读标识（与报告第 5 节
    同一口径：`tool:` 前缀的 source_ref + 内容里的 pmid），所以这里给的制品内容就是那份形状。
    `trust_label` 在 `SourceRecord` 上、**不在** `Evidence` 上 —— 证据的可信面由
    `sources_of` 的口径（只认工具证据）决定，本判据不另判性质维。
    """
    import json

    from adapters.fakes.artifact_store import FakeArtifactStore
    from packages.domain.artifacts import Artifact
    from packages.domain.core import Digest
    from packages.domain.evidence import Evidence

    artifacts = FakeArtifactStore()
    run_id = "9a8b7c6d-5e4f-4a3b-8c2d-1e0f3a5b7c9d"
    artifact_id = "task-nov:tool-result:literature_search"
    content = json.dumps({"articles": [{"pmid": identifier, "title": "prior work"}]}).encode()
    artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="system:run-chain",
            source_refs=["task:nov"],
        ),
        content,
    )
    evidence = Evidence(
        id="0b1c2d3e-4f5a-4b6c-8d7e-9f0a1b2c3d4e",
        run_id=run_id,
        # `report_facts.tool_evidence` 只认 `tool:` 前缀。
        source_ref=f"tool:literature_search:{identifier}",
        content_digest=str(Digest.of_bytes(content)),
        artifact_id=artifact_id,
        tool_refs=("literature_search",),
    )
    return artifacts, evidence


CLAIM_ARTIFACT_ID = "task-nov:novelty_claim"


def _put_claim(
    artifacts: Any,
    prior: list[str],
    *,
    claim: str = "An indexed duplicate detector halves the comparisons.",
    why: str = "The retrieved record measures recall only, not cost.",
) -> Any:
    """落一份 `novelty_claim` 制品并返回它的 `Evidence`（读面按**证据**找制品 id）。"""
    import json

    from packages.domain.artifacts import Artifact
    from packages.domain.core import Digest
    from packages.domain.evidence import Evidence

    content = json.dumps({
        "novelty_claim": {
            "claim": claim,
            "why_novel": why,
            "nearest_prior": prior,
        }
    }).encode()
    artifacts.put(
        Artifact(
            id=CLAIM_ARTIFACT_ID,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="agent:novelty_a",
            source_refs=["task:nov"],
        ),
        content,
    )
    return Evidence(
        id="1c2d3e4f-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
        run_id="9a8b7c6d-5e4f-4a3b-8c2d-1e0f3a5b7c9d",
        source_ref="agent:novelty_a",
        content_digest=str(Digest.of_bytes(content)),
        artifact_id=CLAIM_ARTIFACT_ID,
    )


def test_a_claim_grounded_in_the_retrieved_identifier_passes() -> None:
    """(2) 正向：`nearest_prior` 命中本 run 检索到的标识 ⇒ 声明成立（两面都在）。"""
    artifacts, evidence = _retrieved_evidence("39284801")
    claim_evidence = _put_claim(artifacts, ["PMID:39284801"])
    claim = novelty_claim(artifacts, (evidence, claim_evidence))
    assert claim is not None
    assert claim.matched_prior == "PMID:39284801"
    assert claim.claim and claim.why_novel


def test_a_fabricated_prior_identifier_is_named_red() -> None:
    """(2) 反证：换成**不存在的**标识 ⇒ 点名判红（列出声明与真实两边）。"""
    artifacts, evidence = _retrieved_evidence("39284801")
    claim_evidence = _put_claim(artifacts, ["PMID:99999999"])
    with pytest.raises(Exception) as caught:
        novelty_claim(artifacts, (evidence, claim_evidence))
    message = str(caught.value)
    assert "PMID:99999999" in message
    assert "39284801" in message


def test_an_empty_claim_or_why_is_named_red() -> None:
    """(2) `claim` / `why_novel` 任一为空 ⇒ 点名（「差异点与最近工作同时在」）。"""
    artifacts, evidence = _retrieved_evidence("39284801")
    claim_evidence = _put_claim(artifacts, ["PMID:39284801"], claim="   ")
    with pytest.raises(Exception, match="claim"):
        novelty_claim(artifacts, (evidence, claim_evidence))


def test_no_claim_artifact_is_absence_not_failure() -> None:
    """(2) 两种「空」分得开：没有制品 ⇒ `None`（缺席），不是抛错。"""
    _artifacts, evidence = _retrieved_evidence("39284801")
    from adapters.fakes.artifact_store import FakeArtifactStore

    assert novelty_claim(FakeArtifactStore(), (evidence,)) is None


# --- 评审面（3） -------------------------------------------------------------


def test_the_novelty_role_is_a_reviewer_and_activates_by_protocol() -> None:
    """(3) `is_reviewer()` 为真 + 激活理由逐字 `"role is required by protocol"`。"""
    roles = load_roles("examples/config/roles.yaml")
    role = roles[_NOVELTY_ROLE]
    assert role.review_panel_role is ReviewPanelRole.REVIEWER, role.review_panel_role
    catalog = load_catalog_snapshot()
    required = {
        str(requirement["role"])
        for phase in _raw()["phases"]
        for requirement in phase.get("required_roles") or []
    }
    assert _NOVELTY_ROLE in required
    result = activate_roles(
        {str(item) for item in required},
        {key: value for key, value in _team_roles().items()},
        dict(catalog.roles),
    )
    decision = next(item for item in result.decisions if item.role_id == _NOVELTY_ROLE)
    assert decision.activated is True
    assert decision.reason == "role is required by protocol"


def _team_roles() -> dict[str, Any]:
    """项目所选模板解析后的 RolePool（`project.yaml` → `standard`）。"""
    from services.api.catalog import load_project_settings

    settings = load_project_settings()
    catalog = load_catalog_snapshot()
    template = catalog.team_templates[str(settings.team_template_id)]
    return dict(template.roles)


def test_the_reviewer_receives_the_novelty_claim_as_the_reviewed_object() -> None:
    """(3) **两面互相引用**的结构前提：声明的正文进评审者的「被评对象」段。"""
    plan = _compiled()
    review = next(phase for phase in plan.phases if phase.id == "review")
    names = {item[1] for item in review.cross_phase_inputs}
    assert "novelty_claim" in names, names
    # 只有 `is_reviewer()` 为真的角色才会收到 material（机制在 review_material）。
    assert is_reviewer(_spec_context_for(_NOVELTY_ROLE))


def _spec_context_for(role_id: str) -> Any:
    from types import SimpleNamespace

    return SimpleNamespace(role=load_roles("examples/config/roles.yaml")[role_id])


def test_the_review_verdict_names_the_same_identifier() -> None:
    """(3) 判词**引用声明里那个标识**：门判据的拒绝判词逐字带出真实标识集合。

    这条判的是**机器可核的那一半**：判据输出里出现真实检索标识（`39284801`），
    且拒绝时给出被拒的声明值（`PMID:99999999`）—— 于是「评审说的是哪一条」可复述。
    """
    artifacts, evidence = _retrieved_evidence("39284801")
    claim_evidence = _put_claim(artifacts, ["PMID:99999999"])
    with pytest.raises(Exception) as caught:
        novelty_claim(artifacts, (evidence, claim_evidence))
    assert "39284801" in str(caught.value)
    # 正向：通过时 `matched_prior` 就是那个标识（评审提示词里的正文与它同源）。
    artifacts2, evidence2 = _retrieved_evidence("39284801")
    claim2 = _put_claim(artifacts2, ["PMID:39284801"])
    claim: NoveltyClaim | None = novelty_claim(artifacts2, (evidence2, claim2))
    assert claim is not None and claim.matched_prior == "PMID:39284801"


def test_other_contracts_are_not_judged_by_the_novelty_gate() -> None:
    """(3) 逐字不变：非创新点合约**不**受这道判据影响（`with_novelty` 直通）。"""
    from types import SimpleNamespace

    from packages.application.run_orchestration.novelty_claim_step import with_novelty

    sentinel = object()
    tctx = SimpleNamespace(contract=SimpleNamespace(id="research_report_plan"))
    assert with_novelty(None, tctx, sentinel) is sentinel
    # 而创新点合约在**没有** canonical 上下文时会判负（不静默放行）。
    novelty_tctx = SimpleNamespace(
        contract=SimpleNamespace(id=NOVELTY_CONTRACT_ID),
        task=SimpleNamespace(run_id=SimpleNamespace(value="9a8b7c6d-5e4f-4a3b-8c2d-1e0f3a5b7c9d")),
    )
    assert novelty_verdict(None, novelty_tctx) is not None


# --- 独立性（4） -------------------------------------------------------------


def test_the_three_reviewer_targets_are_all_distinct() -> None:
    """(4) 新 agent 的目标与生产侧、与另两位评审者的目标**都不同**。"""
    catalog = load_catalog_snapshot()
    targets = _targets(catalog)
    assert targets[_NOVELTY_AGENT] not in {
        targets["reviewer_a"],
        targets["reviewer_b"],
        targets["writer"],
        targets["director"],
        targets["domain_a"],
    }, targets


def _targets(catalog: Any) -> dict[str, tuple[str, str]]:
    """agent id → `(endpoint_id, model_name)`（按目录解析后的**执行目标**）。"""
    models = catalog.models
    found: dict[str, tuple[str, str]] = {}
    for agent_id, agent in catalog.agents.items():
        binding = agent.model_binding
        model_id = binding.value
        if binding.mode.value == "MODEL_PROFILE":
            model_id = catalog.model_profiles[binding.value].primary
        model = models[model_id]
        found[agent_id] = (model.endpoint_id, model.model_name)
    return found


def test_the_protocol_id_matches_the_schema_pattern() -> None:
    """(C-3) 协议 id 匹配 `^[a-z0-9]+(_[a-z0-9]+)*_vN_N_N$`。"""
    import re

    assert re.match(r"^[a-z0-9]+(?:_[a-z0-9]+)*_v[0-9]+_[0-9]+_[0-9]+$", _PROTOCOL_ID)
    assert _raw()["id"] == _PROTOCOL_ID


def test_the_sibling_protocol_v1_is_untouched() -> None:
    """(C-2) v1 的六相逐字不变（改它会让它自己的判据立刻红 —— 这里正面取证）。"""
    raw: Any = yaml.safe_load(
        (_ROOT / "examples" / "protocols" / "direction_to_report_v1.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert [phase["id"] for phase in raw["phases"]] == [
        "question",
        "retrieval",
        "plan",
        "experiment",
        "review",
        "report",
    ]
