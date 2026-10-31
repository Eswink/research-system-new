"""角色分派 → CRediT 术语的**声明映射**（GOAL-20261031-102 EC-03）。

**这张表是什么**：把「本 run 协议分派过的角色」机械地映射成 CRediT taxonomy 的 14 个
术语 —— 每个角色恰好一个术语（多个角色可共享一个术语，CRediT 本就允许多人同角色）。

**这张表不是什么**：不是语义判断，更不是评分 —— 「这个角色**相当于**哪个 CRediT 术语」
是声明（映射表逐行可读），不是模型或汇编器的临场发挥。判据只判「列出的每个 CRediT
术语都来自分派过的角色」（`validate_contribution_roles`），不判映射的语义好坏。

**封闭性**：27 个角色逐一在表（与 `examples/config/roles.yaml` 的词表一一对应）；
新角色入表前不得进协议（`dispatched_roles` 对表外角色点名拒绝 —— fail-closed，不
静默跳过）。CRediT 的 14 个术语按官方拼写（含 `Writing – original draft` 的 en dash）。
"""

from __future__ import annotations

#: CRediT taxonomy 的 14 个术语（**闭集**）。
CREDIT_TERMS: frozenset[str] = frozenset({
    "Conceptualization",
    "Data curation",
    "Formal analysis",
    "Funding acquisition",
    "Investigation",
    "Methodology",
    "Project administration",
    "Resources",
    "Software",
    "Supervision",
    "Validation",
    "Visualization",
    "Writing – original draft",
    "Writing – review & editing",
})
#: 角色分派 → CRediT 术语（**声明映射**；新角色入表前不得进协议）。
ROLE_CREDIT: dict[str, str] = {
    "research_director": "Conceptualization",
    "research_planner": "Methodology",
    "supervisor": "Supervision",
    "domain_researcher": "Investigation",
    "literature_scout": "Investigation",
    "evidence_curator": "Data curation",
    "citation_graph_researcher": "Data curation",
    "opportunity_explorer": "Conceptualization",
    "idea_generator": "Conceptualization",
    "novelty_author": "Methodology",
    "novelty_reviewer": "Validation",
    "skeptic": "Validation",
    "methodologist": "Methodology",
    "experiment_designer": "Methodology",
    "experiment_engineer": "Investigation",
    "result_analyst": "Formal analysis",
    "statistician": "Formal analysis",
    "reproducibility_auditor": "Validation",
    "scientific_reviewer": "Validation",
    "methodology_reviewer": "Validation",
    "statistical_reviewer": "Validation",
    "evidence_reviewer": "Validation",
    "target_fit_reviewer": "Validation",
    "meta_reviewer": "Project administration",
    "research_writer": "Writing – original draft",
    "scientific_editor": "Supervision",
    "citation_auditor": "Data curation",
}

assert all(term in CREDIT_TERMS for term in ROLE_CREDIT.values()), (
    "ROLE_CREDIT must map into CREDIT_TERMS"
)

__all__ = ["CREDIT_TERMS", "ROLE_CREDIT"]
