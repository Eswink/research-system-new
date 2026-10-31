"""投稿包的**装配与准入**（GOAL-20261031-102 EC-03；渲染面在 `submission_renderers`）。

**它补哪一环**（建档实测）：`cover letter` / `author contribution` / `CRediT` /
`conflict of interest` / `data availability` / `supplementary` 在产品三根**全部 0 命中**
—— 「能投出去的稿」与「投出去的包」之间隔着五件制品，本模块把它们变成 canonical 事实：

| 制品 | 内容来源 | 谁写 |
| --- | --- | --- |
| `cover_letter.md` | 投稿会话的模型正文（**逐字**引用，不转述） | 汇编器包壳 |
| `author_contributions.md` | 本 run 协议的**角色分派**（phase × role）经闭集映射 | 汇编器 |
| `conflicts_of_interest.md` | 投稿会话的**结构化字段**（`has_conflict` 布尔 + 陈述） | 汇编器渲染 |
| `data_availability.md` | 本 run 的制品清单 + digest（证据投影） | 汇编器 |
| `supplementary.md` | 实验与工具结果的制品索引（id + digest） | 汇编器 |

**CRediT 是映射不是评分**：映射表在 `credit_roles.ROLE_CREDIT`（声明面）——判据只判
「列出的每个 CRediT 术语都来自本 run 分派过的角色」，不判映射的语义好坏。

**两种「空」必须分得开**：本 run 没有投稿会话产物 ⇒ `None`（这次 run 没走投稿相）；
产物在但结构不对（缺 `conflict_of_interest` / `has_conflict` 不是布尔 / 陈述为空）⇒
**点名抛错**（`SubmissionError`，`ManuscriptError` 家族 ⇒ 报告任务 `EXECUTION_FAILURE`）。

**装完复读**（`_verify_rendered`）：判据按**存储里的字节**判，不信任装配路径"一定写
对了" —— 分工与清单从制品正文解析回来再判一遍，COI 的渲染值与会话声明对拍。

**每件制品都登记 SourceRecord + Evidence + Claim + relation**（实测缺口：只 `put` 进
ArtifactStore 的件不在读面上 —— `GET /runs/{id}/artifacts` 走 claim→relation 投影）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import yaml

from packages.application.deliverable.credit_roles import CREDIT_TERMS, ROLE_CREDIT
from packages.application.deliverable.manuscript import ManuscriptError
from packages.application.run_orchestration.submission_renderers import (
    COI_NAME,
    CONTRIBUTIONS_NAME,
    COVER_LETTER_NAME,
    DATA_AVAILABILITY_NAME,
    HAS_CONFLICT_FIELD,
    STATEMENT_FIELD,
    SUBMISSION_ARTIFACT_NAME,
    SUPPLEMENTARY_NAME,
    availability_md,
    coi_md,
    contributions_md,
    cover_letter_md,
    supplementary_md,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)

#: `data_availability.md` 的行形态（判据按它解析 digest 列）。
_DIGEST_ROW = re.compile(r"^\| `(?P<id>[^`]+)` \| `(?P<digest>[^`]+)` \|$", re.MULTILINE)

__all__ = [
    "CREDIT_TERMS",
    "ROLE_CREDIT",
    "SubmissionError",
    "SubmissionPackageResult",
    "SubmissionStatement",
    "dispatched_roles",
    "maybe_assemble_submission",
    "parse_coii_fields",
    "parse_submission_statement",
    "validate_contribution_roles",
    "validate_inventory_digests",
]


class SubmissionError(ManuscriptError):
    """投稿包不可装配（会话产物不可用 / 结构化字段缺失）—— **点名**，不回落。"""


@dataclass(frozen=True, slots=True)
class SubmissionStatement:
    """投稿会话的**结构化声明**（cover letter 正文 + COI 字段；判据按字段读）。"""

    cover_letter: str
    has_conflict: bool
    statement: str


@dataclass(frozen=True, slots=True)
class SubmissionPackageResult:
    """一次投稿包装配的产物（五件制品 + 分派读数；判据与读面共用）。"""

    artifacts: tuple[Artifact, ...]
    credit_roles: tuple[str, ...]
    digests: tuple[str, ...]


def parse_submission_statement(content: str) -> SubmissionStatement:
    """投稿会话产物正文 → 结构化声明（缺字段 / 类型不对 ⇒ **逐项点名**）。"""
    try:
        parsed: Any = json.loads(content)
    except ValueError as error:
        raise SubmissionError(f"submission artifact is not valid JSON: {error}") from error
    if not isinstance(parsed, Mapping):
        raise SubmissionError("submission artifact must be a JSON object")
    block = parsed.get(SUBMISSION_ARTIFACT_NAME)
    if not isinstance(block, Mapping):
        block = _declared_block(parsed)
    cover = str(block.get("cover_letter") or "").strip()
    if not cover:
        raise SubmissionError("the submission block carries no cover_letter text")
    interest = block.get("conflict_of_interest")
    if not isinstance(interest, Mapping):
        raise SubmissionError(
            "the submission block carries no conflict_of_interest object: the declaration "
            "is a structured field (has_conflict + statement), not free prose"
        )
    has_conflict = interest.get(HAS_CONFLICT_FIELD)
    if not isinstance(has_conflict, bool):
        raise SubmissionError(
            f"conflict_of_interest.{HAS_CONFLICT_FIELD} must be a boolean, got "
            f"{type(has_conflict).__name__}: the field is machine-read, not prose"
        )
    statement = str(interest.get(STATEMENT_FIELD) or "").strip()
    if not statement:
        raise SubmissionError(
            f"conflict_of_interest.{STATEMENT_FIELD} is empty: a declaration states its basis"
        )
    return SubmissionStatement(cover_letter=cover, has_conflict=has_conflict, statement=statement)


def _declared_block(parsed: Mapping[str, Any]) -> Mapping[str, Any]:
    """信封形态解开（与应答/手稿同一处实现；解不出 ⇒ 点名）。"""
    from packages.application.run_orchestration.phase_input_material import declared_object

    try:
        block = declared_object(parsed, key=SUBMISSION_ARTIFACT_NAME)
    except Exception as error:  # noqa: BLE001 - 统一折成点名
        raise SubmissionError(
            f"the submission artifact carries no {SUBMISSION_ARTIFACT_NAME!r} block: {error}"
        ) from error
    inner = block.get(SUBMISSION_ARTIFACT_NAME)
    return inner if isinstance(inner, Mapping) else block


def dispatched_roles(run: Any) -> tuple[tuple[str, str], ...]:
    """本 run 协议的**角色分派**（phase × role；protocol_body 缺失 ⇒ 点名）。

    来源是 run 自己冻结的协议正文（`run.protocol_body`）—— 不是磁盘上"现在的"协议：
    投稿包 accompany 的是**那一次** run 的分派，协议文件后来怎么改都不影响它。
    """
    body = getattr(run, "protocol_body", None)
    if body is None or not str(getattr(body, "text", "") or "").strip():
        raise SubmissionError(
            "the run carries no frozen protocol body: the author contributions are read "
            "from the run's own role dispatch, not from the current protocol file"
        )
    try:
        protocol = yaml.safe_load(str(body.text))
    except yaml.YAMLError as error:
        raise SubmissionError(f"the run's frozen protocol body does not parse: {error}") from error
    pairs: list[tuple[str, str]] = []
    for phase in protocol.get("phases") or ():
        phase_id = str(phase.get("id") or "")
        for required in phase.get("required_roles") or ():
            role = str(required.get("role") or "")
            if role:
                pairs.append((phase_id, role))
    if not pairs:
        raise SubmissionError("the run's frozen protocol declares no role dispatch")
    unknown = sorted({role for _phase, role in pairs} - ROLE_CREDIT.keys())
    if unknown:
        raise SubmissionError(
            f"the run's dispatch carries roles outside the CRediT mapping: {unknown}"
        )
    return tuple(pairs)


def validate_contribution_roles(listed: Iterable[str], dispatched: Iterable[str]) -> None:
    """判据 (ii)：列出的每个 CRediT 术语都必须来自分派过的角色（**点名**多出来的）。"""
    allowed = {ROLE_CREDIT[role] for role in dispatched}
    invented = sorted({item for item in listed if item not in allowed})
    if invented:
        raise SubmissionError(
            "author contributions list CRediT roles the run's dispatch never carried: "
            f"{invented} (the dispatch maps to {sorted(allowed)})"
        )


def validate_inventory_digests(listed: Iterable[str], inventory: Iterable[str]) -> None:
    """判据 (iii)：清单里的每个 digest 都必须是本 run 制品的真实 digest（点名编造的）。"""
    known = set(inventory)
    fabricated = sorted({item for item in listed if item not in known})
    if fabricated:
        raise SubmissionError(
            f"the data availability statement lists digests this run does not carry: {fabricated}"
        )


def parse_coii_fields(markdown: str) -> tuple[bool, str]:
    """`conflicts_of_interest.md` → 结构化字段（**按字段读**；块缺失 / 非布尔 ⇒ 点名）。"""
    match = re.search(r"```json\s*(\{.*?\})\s*```", markdown, re.DOTALL)
    if match is None:
        raise SubmissionError(
            "conflicts_of_interest.md carries no structured block: the declaration is read "
            "as a field, not as prose"
        )
    try:
        fields = json.loads(match.group(1))
    except ValueError as error:
        raise SubmissionError(f"the conflict block does not parse: {error}") from error
    has_conflict = fields.get(HAS_CONFLICT_FIELD)
    if not isinstance(has_conflict, bool):
        raise SubmissionError(
            f"conflicts_of_interest.md {HAS_CONFLICT_FIELD} is not a boolean field"
        )
    return has_conflict, str(fields.get(STATEMENT_FIELD) or "")


def maybe_assemble_submission(
    artifacts: Any, ledger: Any, run: Any, run_id: str
) -> SubmissionPackageResult | None:
    """本 run 的投稿会话产物 → 五件投稿制品（无投稿产物 ⇒ `None`；坏产物 ⇒ 点名）。"""
    from packages.application.run_orchestration.report_facts import evidence_of_run

    evidence = evidence_of_run(ledger, run_id) if ledger is not None else ()
    content = _submission_artifact_content(artifacts, evidence)
    if content is None:
        return None
    declared = parse_submission_statement(content)
    pairs = dispatched_roles(run)
    inventory = _inventory(evidence, artifacts)
    package = _write_package(artifacts, ledger, run_id, declared, pairs, inventory)
    _verify_rendered(artifacts, run_id, declared, pairs, inventory)
    return package


def _submission_artifact_content(artifacts: Any, evidence: Iterable[Any]) -> str | None:
    """本 run 的投稿会话产物正文（**不在场 ⇒ `None`**；多于一件 ⇒ 点名）。"""
    ids = sorted({
        str(item.artifact_id)
        for item in evidence
        if str(item.artifact_id or "").endswith(f":{SUBMISSION_ARTIFACT_NAME}")
    })
    if not ids:
        return None
    if len(ids) > 1:
        raise SubmissionError(
            f"run carries {len(ids)} {SUBMISSION_ARTIFACT_NAME} artifacts; a submission "
            f"package must be assembled from exactly one ({ids})"
        )
    return str(artifacts.get(ids[0]).decode("utf-8"))


def _inventory(evidence: Iterable[Any], artifacts: Any) -> tuple[tuple[str, str], ...]:
    """本 run 的制品清单（id + digest；证据投影 ∩ 存储在场）。"""
    rows: list[tuple[str, str]] = []
    for item in evidence:
        artifact_id = str(item.artifact_id or "")
        if not artifact_id:
            continue
        meta = artifacts.meta(artifact_id)
        if meta is not None:
            rows.append((artifact_id, str(meta.digest)))
    return tuple(sorted(set(rows)))


def _verify_rendered(
    artifacts: Any,
    run_id: str,
    declared: SubmissionStatement,
    pairs: tuple[tuple[str, str], ...],
    inventory: tuple[tuple[str, str], ...],
) -> None:
    """装完**复读**：判据按存储里的字节判（信装配路径，不如信制品本身）。"""
    contributions = artifacts.get(f"{run_id}:{CONTRIBUTIONS_NAME}").decode("utf-8")
    listed = re.findall(r"^\| `[^`]+` \| `[^`]+` \| `([^`]+)` \|$", contributions, re.MULTILINE)
    validate_contribution_roles(listed, {role for _phase, role in pairs})
    availability = artifacts.get(f"{run_id}:{DATA_AVAILABILITY_NAME}").decode("utf-8")
    listed_digests = {match.group("digest") for match in _DIGEST_ROW.finditer(availability)}
    validate_inventory_digests(listed_digests, {digest for _id, digest in inventory})
    rendered_has, _rendered = parse_coii_fields(
        artifacts.get(f"{run_id}:{COI_NAME}").decode("utf-8")
    )
    if rendered_has != declared.has_conflict:
        raise SubmissionError(
            "conflicts_of_interest.md renders a different has_conflict than the session "
            f"declared ({rendered_has} != {declared.has_conflict})"
        )


def _write_package(  # noqa: PLR0913 - 装配面：五件制品共用的写入参数（收成对象只多一个名字）
    artifacts: Any,
    ledger: Any,
    run_id: str,
    declared: SubmissionStatement,
    pairs: tuple[tuple[str, str], ...],
    inventory: tuple[tuple[str, str], ...],
) -> SubmissionPackageResult:
    """五件制品逐件写出并登记（顺序固定：信 → 分工 → 冲突 → 数据 → 补充）。"""
    written = [
        _put(
            artifacts,
            ledger,
            run_id,
            COVER_LETTER_NAME,
            cover_letter_md(declared.cover_letter, run_id),
        ),
        _put(artifacts, ledger, run_id, CONTRIBUTIONS_NAME, contributions_md(pairs, run_id)),
        _put(artifacts, ledger, run_id, COI_NAME, coi_md(_coi_fields(declared), run_id)),
        _put(artifacts, ledger, run_id, DATA_AVAILABILITY_NAME, availability_md(inventory, run_id)),
        _put(artifacts, ledger, run_id, SUPPLEMENTARY_NAME, supplementary_md(inventory, run_id)),
    ]
    return SubmissionPackageResult(
        artifacts=tuple(written),
        credit_roles=tuple(sorted({ROLE_CREDIT[role] for _phase, role in pairs})),
        digests=tuple(digest for _id, digest in inventory),
    )


def _coi_fields(declared: SubmissionStatement) -> dict[str, object]:
    """COI 的结构化字段（渲染器收到的就是这份；`parse_coii_fields` 读回的也是它）。"""
    return {HAS_CONFLICT_FIELD: declared.has_conflict, STATEMENT_FIELD: declared.statement}


def _put(artifacts: Any, ledger: Any, run_id: str, name: str, markdown: str) -> Artifact:
    """一件投稿制品 → 内容寻址制品 + SourceRecord + Evidence + Claim（**GENERATED**）。"""
    content = markdown.encode("utf-8")
    artifact = Artifact(
        id=f"{run_id}:{name}",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/markdown",
        storage_uri=None,
        created_by="system:submission-assembler",
        source_refs=[f"run:{run_id}"],
        classification="submission_package",
    )
    artifacts.put(artifact, content)
    artifacts.mark(artifact.id, ArtifactState.VERIFIED)
    _register(ledger, run_id, artifact, name)
    return artifact


def _register(ledger: Any, run_id: str, artifact: Artifact, name: str) -> None:
    """登记进读面（claim→relation 投影；不挂 relation 的制品读不到 —— 实测缺口）。

    `origin` 按制品点名（`submission:{run_id}:{name}`）：五件制品的内容各不相同，
    共用一个 origin 会撞「同源不同 digest」的登记冲突。
    """
    if ledger is None:
        return
    source = SourceRecord(
        origin=f"submission:{run_id}:{name}",
        content_digest=str(artifact.digest),
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
        parser_version="submission-assembler-v1",
    )
    ledger.register_source(source)
    evidence = Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=source.origin,
        content_digest=str(artifact.digest),
        extracted_by=artifact.created_by,
        captured_at=Timestamp.now(),
        artifact_id=artifact.id,
        run_id=run_id,
    )
    ledger.register_evidence(evidence)
    claim_id = f"claim:submission:{run_id}:{name}"
    ledger.register_claim(
        Claim(
            id=claim_id,
            statement=f"Run {run_id} assembled {name} for submission",
            status=ClaimStatus.PROPOSED,
            author=artifact.created_by,
            evidence_relations=[(evidence.id, EvidenceRelationType.SUPPORTS)],
        )
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim_id, evidence_id=evidence.id, relation=EvidenceRelationType.SUPPORTS
        )
    )
