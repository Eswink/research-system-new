"""十相手稿链的**受控会话回复**（GOAL-20261028-099 起的夹具面；GOAL-20261031-102 拆出）。

**为什么单列**：`direction_to_manuscript_support.py` 贴着 450 行硬上限（规模门），而
「每个会话格的受控回复」是一段可独立读的纯函数 —— 不碰服务器、不碰存储。本模块
**不含用例**；`direction_to_manuscript_support` 按名字再出口这些函数（既有 import 面
不变）。指纹按合约 `purpose` 的首句（**逐字**取自 `task_contracts.yaml`）分派。
"""

from __future__ import annotations

import json
import re

#: 手稿正文（**无任何数字**，只有 `[1]` 引用标记 —— 与合约的两条硬规则一致）。
MANUSCRIPT_SECTIONS: dict[str, str] = {
    "title": "Retrieval Grounding For Controlled Planning Studies",
    "abstract": "We ask whether grounding a research plan in the retrieved literature "
    "changes the design a controlled experiment can execute, and we report the measured "
    "comparison in the assembled table rather than in this prose.",
    "introduction": "Planning assistants propose studies that the literature may already "
    "settle; we ask what changes when the material is retrieved before the plan is written.",
    "related_work": "The closest retrieved work builds reproducibility tooling for "
    "computational research and documents the cost of custom pipelines [1]; it leaves open "
    "which planning choices actually move a measured outcome, which is what this study "
    "varies.",
    "methods": "Two arms run the same shipped benchmark script. The treatment arm sets a "
    "larger item count than the control arm, so the comparison isolates the workload under "
    "a fixed procedure.",
    "results": "The treatment arm's comparison count differs from the control arm's; the "
    "per-arm readings and their sources are published in the data table below, by name, so "
    "each value can be checked against this run rather than against this sentence [1].",
    "discussion": "The measured difference is a workload effect and nothing more: the study "
    "varies the item count alone, one script cannot speak for another, and the run carries "
    "a single retrieved record.",
    "conclusion": "Grounded planning yields an executable design here; whether it yields a "
    "better one is not something this run measured, and we do not claim it.",
}

__all__ = [
    "MANUSCRIPT_SECTIONS",
    "editorial_reply",
    "response_reply",
    "revised_sections",
    "submission_reply",
]


def response_reply(prompt: str) -> str:
    """应答格的受控回复：**逐条**回应提示词里列出的每一个 `P<n>` + 一份改稿正文。

    为什么从提示词里**读编号**（而不是写死 `P1`/`P2`）：本夹具的意义是证明「点表真的
    到了模型眼前」—— 写死编号会让它在点表缺失时**依然通过**（那是假绿）。这里按提示词
    实际给出的 id 生成应答，点表为空就**一条也不回**（那会让汇编器点名漏答 ⇒ 判据红，
    这正是我们要的行为）。

    GOAL-20261031-102 EC-02：回复还携带第二块 `revised_manuscript`（改稿正文，与
    `author_responses` 并列的两个围栏块）。改稿**真的改了**：Related Work 与 Discussion
    与 v1 逐字不同（回应编辑的 `required_changes`）；每条 `action_taken` 引用
    `manuscript_v2.md`（HARD RULE 5 的产品形态）。
    """
    # `prompt` 是 **JSON 序列化后**的 messages（本文件上游 `json.dumps` 过 ⇒ 换行是
    # 字面 `\n` 两字符），所以行首锚不能用 `^`+MULTILINE —— 直接按 `- P<n> (` 取。
    ids = re.findall(r"- (P\d+) \(([a-z_]+)\): ", prompt)
    block = json.dumps(
        {
            "author_responses": [
                {
                    "point_id": point_id,
                    "response": f"We accept {point_id}: the review is right about this one.",
                    "action_taken": (
                        f"revised the section named in {point_id}; see manuscript_v2.md"
                    ),
                }
                for point_id, _severity in ids
            ]
        },
        ensure_ascii=False,
    )
    revised = json.dumps({"revised_manuscript": revised_sections()}, ensure_ascii=False)
    return (
        "Here is our point by point response, followed by the revised body.\n\n"
        "```json\n" + block + "\n```\n\n```json\n" + revised + "\n```\n"
    )


def revised_sections() -> dict[str, str]:
    """改稿正文（与 v1 逐字可分；同样的两条硬规则 —— 无数字、`[1]` 引用闭合）。"""
    revised = dict(MANUSCRIPT_SECTIONS)
    revised["related_work"] = (
        "The closest retrieved work builds reproducibility tooling for computational "
        "research and documents the cost of custom pipelines [1]; what the present study "
        "adds is a named planning choice — the item count the arms set — varied under a "
        "fixed procedure, which that work leaves open."
    )
    revised["discussion"] = (
        "The measured difference is a workload effect and nothing more: the study varies "
        "the item count alone, one script cannot speak for another, and the retrieved "
        "record set is a single work. The planning choice named in Related Work is the "
        "only lever this design moves, and we do not claim more."
    )
    return revised


def editorial_reply() -> str:
    """编辑决定格的受控回复（形状照合约 `editorial_decision` 的规定）。

    取 `minor_revision` 而不是 `accept`：**带改动的决定**才会经过
    「`required_changes` 必须非空」那条判据 —— 用 `accept` 作夹具会让那个分支在
    产品入口上从未被走到（判据侧的单测会绿，产品路径**没有**证据）。
    """
    block = json.dumps(
        {
            "editorial_decision": {
                "decision": "minor_revision",
                "rationale": "the review asks which planning choice moved the measured "
                "outcome, and the Related Work section does not yet say so in its own words",
                "required_changes": [
                    "name the planning choice that differs between the two arms in Related Work",
                ],
                # GOAL-20261031-102 EC-04：期刊选择（闭集声明面；依据引用 scope 关键词）。
                "target_journal": "Journal of Reproducible Research Tooling",
                "selection_rationale": "the study builds reproducibility tooling for a "
                "controlled workflow and evaluates it against the closest retrieved record",
            }
        },
        ensure_ascii=False,
    )
    return (
        "The manuscript needs limited edits before it can proceed.\n\n```json\n" + block + "\n```\n"
    )


def submission_reply() -> str:
    """投稿包格的受控回复（形状照合约 `submission_package` 的规定）。

    `has_conflict` 是**布尔字段**（不是散文）：夹具给 `false` + 一句「查过什么」的
    陈述 —— 让「按字段读」那条判据在产品路径上真的被走到。信里**不点名期刊**
    （合约 HARD RULE 2：期刊选择是另一张声明面）。
    """
    block = json.dumps(
        {
            "submission_package": {
                "cover_letter": "This study asks what grounding the plan in the retrieved "
                "literature changes for a controlled experiment. The closest retrieved work "
                "builds tooling but does not vary which planning choice moves a measured "
                "outcome; we vary that choice under a fixed procedure. The review's point "
                "about naming the differing planning choice is addressed in the revised "
                "Related Work, and the editorial decision required exactly that change.",
                "conflict_of_interest": {
                    "has_conflict": False,
                    "statement": "The authors checked funding, employment and data-sharing "
                    "arrangements for this run and declare none that bear on the study.",
                },
            }
        },
        ensure_ascii=False,
    )
    return "The submission statement follows.\n\n```json\n" + block + "\n```\n"


def manuscript_reply() -> str:
    """手稿格的受控回复（形状照合约 `research_manuscript` 的规定）。"""
    block = json.dumps({"manuscript_narrative": MANUSCRIPT_SECTIONS}, ensure_ascii=False)
    return (
        "The body below states no quantity: every number lives in the assembled data table."
        "\n\n```json\n" + block + "\n```\n"
    )


def novelty_reply(pmid: str) -> str:
    """创新点格的受控回复（`nearest_prior` 用本 run 真取回的标识）。"""
    block = json.dumps(
        {
            "novelty_claim": {
                "claim": "This study ties the planning step to what retrieval returned.",
                "why_novel": "the closest retrieved work builds tooling but does not vary "
                "which planning choices move a measured outcome",
                "nearest_prior": [f"PMID:{pmid}"],
            }
        },
        ensure_ascii=False,
    )
    return (
        "That record leaves the planning choice open, which is what this study varies."
        "\n\n```json\n" + block + "\n```\n"
    )
