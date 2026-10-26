"""创新点声明（`novelty_claim`）的**判定面**（GOAL-20261026-097 EC-04(a)）。

**它补哪一格**：本轮的靶子之一是「让『创新点』有两面」。声明面由协议
（`examples/protocols/direction_to_report_v2.yaml` 的 `novelty` 相）+ 合约
（`novelty_claim_proposal`）建立；但「模型写了一段 JSON」本身不构成判据 ——
一段 `{"claim": "we are first", "why_novel": "nobody did it", "nearest_prior": ["PMID:1"]}`
与一段真的站在检索结果上的声明**长得一样**。本模块把「站在检索上」变成可判事实。

**判什么**（缺一即**点名拒绝**，不静默、不回落）：

1. `claim` 与 `why_novel` 都非空（差异点与理由**同时在**）；
2. `nearest_prior` 至少一条**命中本 run 检索证据里真实出现的标识**（PMID / DOI 逐字取自
   落库的工具结果内容 —— 与 `report_facts.sources_of` 同一抽取口径，不另造第二套解析）。

**三条边界**：

- **只读 canonical**（`ArtifactStore` + `EvidenceLedger` 的 claim→relation 投影），
  **零出网 / 零模型 / 零时钟**；
- **run 作用域**：只认**本 run** 的工具证据（他 run 的检索到过什么，与本 run 的声明无关）；
- **fail-closed 分得开两种「空」**：没有 `novelty_claim` 制品 ⇒ `None`（「这次 run 没声明」
  ≠ 失败）；制品在但解不出来 / 标识不在检索里 ⇒ **抛错**（那是声明坏掉，不是「没有」）。

**为什么判据落在读取面而不是契约的 `acceptance_criteria`**：`EVIDENCE_COVERAGE` 判的是
**计数**，而这里判的是**集合成员**（标识是否出现在检索结果里）。新增一个判据类型会扩展
验收词表（`AcceptanceCriterionType`），那是域层枚举扩容 —— 本 GOAL 不改（`C-4` 的同一条
纪律：能力面与验收面的词表都不扩）。判据由编排侧的 novelty 步骤调用（见
`novelty_claim_step.py`）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.run_orchestration.phase_input_material import (
    declared_object,
)
from packages.application.run_orchestration.report_facts import sources_of

#: 制品名（制品 id 的**尾段**：`{task_id}:novelty_claim`）。
NOVELTY_ARTIFACT_NAME = "novelty_claim"
#: 声明块里三个必填键。
CLAIM_KEY = "claim"
WHY_KEY = "why_novel"
PRIOR_KEY = "nearest_prior"
#: `nearest_prior` 里的标识前缀（合约正文要求这两种；其余前缀按「不认得」处理）。
PRIOR_PREFIXES = ("PMID:", "DOI:")


@dataclass(frozen=True, slots=True)
class NoveltyClaim:
    """一份**通过判定**的创新点声明（三件都非空；`nearest_prior` 至少一条真标识）。"""

    artifact_id: str
    claim: str
    why_novel: str
    nearest_prior: tuple[str, ...]
    #: 命中的那一条真标识（评审判据要它 —— 「引用的是哪一条」必须可复述）。
    matched_prior: str


def novelty_claim_of_run(
    artifacts: ArtifactStore, ledger: EvidenceLedger, run_id: str
) -> NoveltyClaim | None:
    """本 run 的创新点声明（无制品 ⇒ `None`；解不出 / 标识不在检索里 ⇒ **点名抛错**）。"""
    from packages.application.run_orchestration.report_facts import evidence_of_run

    evidence = evidence_of_run(ledger, run_id)
    return novelty_claim(artifacts, evidence)


def novelty_claim(artifacts: ArtifactStore, evidence: tuple[Any, ...]) -> NoveltyClaim | None:
    """已投影的证据 → 声明（无制品 ⇒ `None`）。

    **两个集合必须分开算**：`nearest_prior` 里的标识来自**模型正文**，而「真实出现的标识」
    来自**本 run 的工具证据内容**。用一个集合做两个用途会让判据变成同义反复
    （「模型写了 X，模型也写了 X」）。
    """
    artifact_id = _novelty_artifact_id(evidence)
    if artifact_id is None:
        return None
    payload = _claim_payload(artifacts, artifact_id)
    declared = _strings(payload, artifact_id)
    retrieved = {entry["identifier"] for entry in sources_of(artifacts, evidence)}
    matched = _match_prior(declared[PRIOR_KEY], retrieved, artifact_id)
    return NoveltyClaim(
        artifact_id=artifact_id,
        claim=declared[CLAIM_KEY],
        why_novel=declared[WHY_KEY],
        nearest_prior=tuple(declared[PRIOR_KEY]),
        matched_prior=matched,
    )


def _novelty_artifact_id(evidence: tuple[Any, ...]) -> str | None:
    """证据里 `:novelty_claim` 制品的 id（零条 ⇒ `None`；多于一条 ⇒ 点名）。"""
    suffix = f":{NOVELTY_ARTIFACT_NAME}"
    matches = sorted({
        str(item.artifact_id)
        for item in evidence
        if item.artifact_id and str(item.artifact_id).endswith(suffix)
    })
    if not matches:
        return None
    if len(matches) > 1:
        raise InvalidInputError(
            f"run evidence carries {len(matches)} distinct {NOVELTY_ARTIFACT_NAME!r} "
            f"artifacts ({matches}); the novelty claim would be undecidable"
        )
    return matches[0]


def _claim_payload(artifacts: ArtifactStore, artifact_id: str) -> Mapping[str, Any]:
    """制品原文 → 声明对象（信封形态解开；直形态原样）。解不出 ⇒ **点名**。"""
    raw = artifacts.get(artifact_id).decode("utf-8")
    try:
        parsed: Any = json.loads(raw)
    except ValueError as error:
        raise InvalidInputError(
            f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id} is not valid JSON: {error}"
        ) from error
    if not isinstance(parsed, Mapping):
        raise InvalidInputError(
            f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id} is not a JSON object"
        )
    content = parsed.get("content") if "declared_artifact" in parsed else None
    if not isinstance(content, str):
        return _declared_block(parsed, artifact_id)
    return _declared_block_from_text(content, artifact_id)


def _declared_block(payload: Mapping[str, Any], artifact_id: str) -> Mapping[str, Any]:
    """直形态载荷：带 `novelty_claim` 键的对象内层（缺键 ⇒ 点名）。"""
    inner = payload.get(NOVELTY_ARTIFACT_NAME)
    if isinstance(inner, Mapping):
        return inner
    if CLAIM_KEY in payload:
        return payload
    raise InvalidInputError(
        f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id} carries no object with the key "
        f"{NOVELTY_ARTIFACT_NAME!r} (expected the shape the contract prescribes)"
    )


def _declared_block_from_text(content: str, artifact_id: str) -> Mapping[str, Any]:
    """信封正文 → 带 `novelty_claim` 键的那个对象（解不出 ⇒ 点名）。

    复用 `phase_input_material.declared_object`（**同一份**「按期望键挑块」实现 ——
    `key=` 参数就是为这件事加的：真实正文常先给一段**示例**块再给答案块，不按期望键
    筛选会取到示例）。
    """
    envelope = {"content": content, "declared_artifact": NOVELTY_ARTIFACT_NAME}
    payload = declared_object(envelope, key=NOVELTY_ARTIFACT_NAME)
    if NOVELTY_ARTIFACT_NAME not in payload and CLAIM_KEY not in payload:
        raise InvalidInputError(
            f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id} carries no JSON block with "
            f"the key {NOVELTY_ARTIFACT_NAME!r} (expected the shape the contract prescribes)"
        )
    return _declared_block(payload, artifact_id)


def _strings(payload: Mapping[str, Any], artifact_id: str) -> dict[str, Any]:
    """三个键的**形态**校验（缺键 / 非字符串 / 空白 / 空列表 ⇒ 逐条点名）。"""
    claim = payload.get(CLAIM_KEY)
    why = payload.get(WHY_KEY)
    prior = payload.get(PRIOR_KEY)
    if not isinstance(claim, str) or not claim.strip():
        raise InvalidInputError(
            f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id}: {CLAIM_KEY!r} must be a "
            "non-empty string (a claim that says nothing cannot be judged)"
        )
    if not isinstance(why, str) or not why.strip():
        raise InvalidInputError(
            f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id}: {WHY_KEY!r} must be a "
            "non-empty string (the difference must be stated, not implied)"
        )
    if not isinstance(prior, list) or not prior:
        raise InvalidInputError(
            f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id}: {PRIOR_KEY!r} must be a "
            "non-empty list of identifiers"
        )
    items = [str(item).strip() for item in prior]
    if not all(items):
        raise InvalidInputError(
            f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id}: {PRIOR_KEY!r} carries an "
            "empty identifier (which names no prior work)"
        )
    return {CLAIM_KEY: claim, WHY_KEY: why, PRIOR_KEY: items}


def _match_prior(items: list[str], retrieved: set[str], artifact_id: str) -> str:
    """`nearest_prior` 里**命中本 run 检索结果**的那一条（一条都没有 ⇒ 点名 + 列出两边）。"""
    if not retrieved:
        raise InvalidInputError(
            f"run carries {NOVELTY_ARTIFACT_NAME} artifact {artifact_id} but no "
            "system-retrieved source: nothing could have been the nearest prior work"
        )
    for item in items:
        if _bare_identifier(item) in retrieved:
            return item
    raise InvalidInputError(
        f"{NOVELTY_ARTIFACT_NAME} artifact {artifact_id}: none of {PRIOR_KEY!r} "
        f"({items}) matches an identifier the run actually retrieved "
        f"({sorted(retrieved)}); a claim against work this run never saw is not "
        "a claim against the retrieved prior work"
    )


def _bare_identifier(item: str) -> str:
    """`PMID:12345678` → `12345678`（落库标识是**裸值**，声明带前缀 ⇒ 剥一层再比）。

    只剥 `PRIOR_PREFIXES` 里点名的前缀；其余形态原样返回（**不**猜「用户想说什么」）。
    """
    for prefix in PRIOR_PREFIXES:
        if item.upper().startswith(prefix):
            return item[len(prefix) :].strip()
    return item


__all__ = [
    "CLAIM_KEY",
    "NOVELTY_ARTIFACT_NAME",
    "NoveltyClaim",
    "PRIOR_KEY",
    "PRIOR_PREFIXES",
    "WHY_KEY",
    "novelty_claim",
    "novelty_claim_of_run",
]
