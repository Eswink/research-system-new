"""改稿闭环的**装配与准入**（GOAL-20261031-102 EC-02；域面在 `packages/domain/artifacts.py`）。

**它补哪一环**（建档实测）：`revision` 相产出的是**逐条应答**（`author_responses`），
`response_letter.md` 渲染 `**Action taken.** {answer.action_taken or '_(none stated)_'}` ——
作者可以写「已修改」，但**没有任何东西验证手稿真的变了**。本模块把闭环补成结构事实：

1. 应答会话的回复里携带**第二块** `revised_manuscript`（与 `author_responses` 同一封信、
   各自一个围栏 JSON 块；`declared_object` 按**期望键**筛选 ⇒ 两块互不顶替）；
2. 装配面把它装成 `manuscript_v2.md`，其 `Artifact.supersedes` 指向 v1
   （`{run_id}:manuscript.md`）—— 父指针在装配期经域层 `validate_supersedes`
   逐跳校验（目标在场 / 同 run / 不成环）；
3. **每一条** `action_taken` 必须引用 `manuscript_v2.md`（不许空谈），且正文里
   引用的**每一个** `.md` / `.json` 名字都必须是本 run 真的带着的制品名
   （编造引用点名拒绝）。

**两种「空」必须分得开**（与手稿正文那一格同一纪律）：

- 本 run **没有** `author_responses` 制品 ⇒ 返回 `None`（这次 run 没走返修回路）；
- 应答在场但**没有** `revised_manuscript` 块 ⇒ 返回 `None`（旧形状的应答：GOAL-100 的
  既有产物只有逐条回应、没有改稿正文 —— 对它们不做改稿判，也不回头改写历史产物）；
- 块在、但正文违反数字禁令 / 引用不闭合 / 引用编造 ⇒ **点名抛错**
  （`RevisionError` / `ResponseError`），由报告任务以 `EXECUTION_FAILURE` 收敛。

**为什么装在报告相**（与 v1 手稿同一分工）：改稿正文由**模型**写（应答会话），
数字与参考文献由**汇编器**写（报告相）—— `manuscript_facts` 的两个执行期事实
（判词、汇编时状态）只在报告相的装配面在场。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from packages.application.deliverable.author_response import (
    AuthorResponse,
    ResponseError,
    parse_responses,
)
from packages.application.deliverable.manuscript import (
    MANUSCRIPT_MIME,
    ManuscriptAdmission,
    ManuscriptError,
    build_manuscript,
    manuscript_digest,
    validate_manuscript,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.manuscript_assembly import (
    ASSEMBLED_CREATOR_PREFIX,
    MANUSCRIPT_ARTIFACT_NAME,
    response_artifact_content,
)
from packages.application.run_orchestration.phase_input_material import declared_object
from packages.domain.artifacts import Artifact, SupersedesError, validate_supersedes
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

#: 应答回复里承载**改稿正文**的那个键（第二块；与 `author_responses` 并列、不嵌套）。
REVISED_BLOCK_KEY = "revised_manuscript"
#: 改稿制品的名字（run 级 id `{run_id}:manuscript_v2.md`；合约与判据按它引用）。
MANUSCRIPT_V2_NAME = "manuscript_v2.md"
#: `action_taken` 里可判的制品名形态（**闭集**：`.md` / `.json`；其余后缀不在判据射程内，
#: 如实登记 —— 不是「任何名字都判」）。
_CITABLE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.(?:md|json)\b")


class RevisionError(ManuscriptError):
    """改稿闭环不可装配（正文不可用 / 父指针不可解析）—— **点名**，不回落。

    继承 `ManuscriptError`（它是 `NarrativeError` 的子类）：报告任务把那一家族折成
    `EXECUTION_FAILURE` —— 改稿的每一种点名拒绝与手稿同一条收敛，不需要第二张网。
    """


def manuscript_v2_artifact_id(run_id: str) -> str:
    """改稿制品的 canonical id（**run 级**；与 v1 同一命名面，判据与读面共用）。"""
    return f"{run_id}:{MANUSCRIPT_V2_NAME}"


def parse_revised_manuscript(content: str) -> Mapping[str, Any] | None:
    """应答制品正文 → 改稿正文的八个键（**块不在场 ⇒ `None`**；解不出 ⇒ 点名）。"""
    try:
        parsed: Any = json.loads(content)
    except ValueError as error:
        raise RevisionError(f"author response artifact is not valid JSON: {error}") from error
    if not isinstance(parsed, Mapping):
        raise RevisionError("author response artifact must be a JSON object")
    try:
        block = declared_object(parsed, key=REVISED_BLOCK_KEY)
    except InvalidInputError:
        # `declared_object` 在这里抛错的唯一含义是「找不到带期望键的对象」⇒ 块不在场
        # （旧形状的应答），不是失败 —— 两种「空」分得开。
        return None
    except ValueError as error:
        raise RevisionError(f"the {REVISED_BLOCK_KEY!r} block is unusable: {error}") from error
    inner = block.get(REVISED_BLOCK_KEY)
    return inner if isinstance(inner, Mapping) else None


def validate_action_references(
    responses: tuple[AuthorResponse, ...], *, known_names: frozenset[str]
) -> None:
    """**每一条** `action_taken` 必须引用改稿制品，且引用的名字必须真的在场（**点名**）。

    两条判据、顺序固定：
    ① 不许空谈：不含 `manuscript_v2.md` ⇒ 点名那一条应答；
    ② 不许编造：正文里引用的每个 `.md` / `.json` 名字都必须在 `known_names`
    （本 run 证据投影里真实带着的制品名后缀集合）里。
    """
    for item in responses:
        if MANUSCRIPT_V2_NAME not in item.action_taken:
            raise ResponseError(
                f"action_taken for {item.point_id} does not reference the revised manuscript "
                f"artifact {MANUSCRIPT_V2_NAME!r}: a stated action that points at nothing "
                "cannot be verified against the work"
            )
        for name in sorted(set(_CITABLE_NAME.findall(item.action_taken))):
            if name not in known_names:
                raise ResponseError(
                    f"action_taken for {item.point_id} cites {name!r}, which this run does "
                    f"not carry (known artifact names: {sorted(known_names)})"
                )


@dataclass(frozen=True, slots=True)
class RevisionClosureResult:
    """一次改稿闭环的产物（制品 + 应答信引用面；判据与读面共用）。"""

    artifact: Artifact
    supersedes: str
    responses: tuple[AuthorResponse, ...]


def revision_closure_step(  # noqa: PLR0913 - 装配面：五个 Port + created_by（与 assemble_manuscript 同一豁免纪律）
    artifacts: Any, ledger: Any, reviews: Any, run: Any, run_id: str, *, created_by: str
) -> RevisionClosureResult | None:
    """本 run 的应答产物 → 改稿制品 + 引用校验（无应答 / 无改稿块 ⇒ `None`）。

    调用点在报告相装配面（`manuscript_assembly.maybe_assemble_manuscript`）：v1 已在场，
    v2 在**应答信之前**装配（信的引用判据要指着它）。
    """
    from packages.application.run_orchestration.report_facts import evidence_of_run

    evidence = evidence_of_run(ledger, run_id) if ledger is not None else ()
    content = response_artifact_content(artifacts, evidence)
    if content is None:
        return None
    try:
        responses = parse_responses(content)
        revised = parse_revised_manuscript(content)
    except ResponseError as error:
        raise RevisionError(f"the author response artifact is unusable: {error}") from error
    if revised is None:
        return None
    v1_id = f"{run_id}:{MANUSCRIPT_ARTIFACT_NAME}"
    if artifacts.meta(v1_id) is None:
        raise RevisionError(
            f"the run carries a {REVISED_BLOCK_KEY!r} block but no {v1_id}: a revision "
            "supersedes an existing manuscript, it does not appear from nothing"
        )
    artifact = _assemble_v2(artifacts, ledger, reviews, run, run_id, revised, created_by)
    # 引用判据在 **v2 落库之后**判：它引用的正是刚注册的那件制品（重读一次证据投影，
    # 让「在场」的定义仍是 claim→relation 投影，而不是"装配路径说了算"）。
    fresh = evidence_of_run(ledger, run_id) if ledger is not None else ()
    names = _known_names(fresh, v1_id) | {MANUSCRIPT_V2_NAME, MANUSCRIPT_ARTIFACT_NAME}
    try:
        validate_action_references(responses, known_names=names)
    except ResponseError as error:
        raise RevisionError(f"the revision citations are unusable: {error}") from error
    return RevisionClosureResult(artifact=artifact, supersedes=v1_id, responses=responses)


def _known_names(evidence: Iterable[Any], v1_id: str) -> frozenset[str]:
    """本 run 证据投影里的**制品名后缀**集合（引用判据的「在场」定义）。"""
    names = {v1_id.rsplit(":", 1)[-1]}
    for item in evidence:
        artifact_id = str(item.artifact_id or "")
        if artifact_id:
            names.add(artifact_id.rsplit(":", 1)[-1])
    return frozenset(names)


def _assemble_v2(  # noqa: PLR0913 - 装配面：五个 Port + 正文 + 归属（少一个就得让调用方先拼对象）
    artifacts: Any,
    ledger: Any,
    reviews: Any,
    run: Any,
    run_id: str,
    revised: Mapping[str, Any],
    created_by: str,
) -> Artifact:
    """改稿正文 + canonical 事实 → `manuscript_v2.md`（父指针经域层链校验后落库）。

    与 v1 同一条判据链（数字禁令 / 引用闭合 / 品质三条）：**改过的正文不降门槛** ——
    一次返修若把正文改坏了，点名拒绝比产出一份坏手稿诚实。
    """
    from packages.application.deliverable.manuscript import (
        MANUSCRIPT_KEYS,
        validate_manuscript_quality,
    )
    from packages.application.run_orchestration.manuscript_facts import manuscript_facts

    facts = manuscript_facts(artifacts, ledger, reviews, run, run_id)
    sections = {key: str(revised.get(key) or "") for key in MANUSCRIPT_KEYS}
    validate_manuscript(sections, facts.references)
    validate_manuscript_quality(sections, facts.references)
    admission = ManuscriptAdmission(
        author=f"{ASSEMBLED_CREATOR_PREFIX}{created_by}",
        returned_model=str(revised.get("returned_model") or ""),
        digest=manuscript_digest(sections),
        sections=sections,
    )
    markdown = build_manuscript(facts.inputs, admission, facts.references)
    v1_id = f"{run_id}:{MANUSCRIPT_ARTIFACT_NAME}"
    artifact = _put_v2(artifacts, run_id, markdown, admission, v1_id)
    _register_v2(ledger, run_id, artifact, v1_id)
    return artifact


def _put_v2(
    artifacts: Any, run_id: str, markdown: str, admission: ManuscriptAdmission, v1_id: str
) -> Artifact:
    """改稿字节 → 内容寻址制品（`supersedes` → v1；**链校验通过才落库**）。"""
    content = markdown.encode("utf-8")
    artifact = Artifact(
        id=manuscript_v2_artifact_id(run_id),
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type=MANUSCRIPT_MIME,
        storage_uri=None,
        created_by=admission.author,
        source_refs=[f"run:{run_id}"],
        classification="research_manuscript_revision",
        supersedes=v1_id,
    )
    validate_supersedes(artifact, run_id=run_id, resolve=artifacts.meta)
    artifacts.put(artifact, content)
    artifacts.mark(artifact.id, ArtifactState.VERIFIED)
    return artifact


def _register_v2(ledger: Any, run_id: str, artifact: Artifact, supersedes: str) -> None:
    """改稿制品 → SourceRecord + Evidence + Claim（**GENERATED**；supersedes 进 claim 陈述）。"""
    if ledger is None:
        return
    source = SourceRecord(
        origin=f"revision:{run_id}:{MANUSCRIPT_V2_NAME}",
        content_digest=str(artifact.digest),
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
        parser_version="revision-assembler-v1",
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
    claim_id = f"claim:revision:{run_id}"
    ledger.register_claim(
        Claim(
            id=claim_id,
            statement=(f"Run {run_id} assembled {MANUSCRIPT_V2_NAME} superseding {supersedes}"),
            status=ClaimStatus.PROPOSED,
            author=artifact.created_by,
            evidence_relations=[(evidence.id, EvidenceRelationType.SUPPORTS)],
        )
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim_id,
            evidence_id=evidence.id,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def revision_closure_of_run(artifacts: Any, run_id: str) -> dict[str, Any] | None:
    """**读面**：本 run 的改稿闭环（v2 在场 ⇒ 校验它的父指针链；不在场 ⇒ `None`）。

    判据按**存储状态**读，不信任装配路径"一定写了指针"：v2 在场却没带 `supersedes`
    ⇒ 点名判红（反证 (iii) 的读法）。
    """
    v2_id = manuscript_v2_artifact_id(run_id)
    v2 = artifacts.meta(v2_id)
    if v2 is None:
        return None
    v1_id = f"{run_id}:{MANUSCRIPT_ARTIFACT_NAME}"
    v1 = artifacts.meta(v1_id)
    problems: list[str] = []
    if v2.supersedes is None:
        problems.append(f"{v2_id} carries no supersedes pointer")
    else:
        if v1 is None:
            problems.append(f"{v2_id} supersedes {v1_id}, which is not in the store")
        if v2.supersedes != v1_id:
            problems.append(f"{v2_id} supersedes {v2.supersedes!r}, expected {v1_id!r}")
        # 链游走**总是**跑（指针指错 ≠ 链不成立这两件事都要点名；成环由域层抓）。
        try:
            validate_supersedes(v2, run_id=run_id, resolve=artifacts.meta)
        except SupersedesError as error:
            problems.append(str(error))
    return {
        "v2": v2,
        "v1": v1,
        "v2_id": v2_id,
        "v1_id": v1_id,
        "problems": tuple(problems),
    }


__all__ = [
    "MANUSCRIPT_V2_NAME",
    "REVISED_BLOCK_KEY",
    "RevisionClosureResult",
    "RevisionError",
    "manuscript_v2_artifact_id",
    "parse_revised_manuscript",
    "revision_closure_of_run",
    "revision_closure_step",
    "validate_action_references",
]
