"""手稿的**装配与准入**（GOAL-20261028-099 EC-02/EC-03；读面在 `manuscript_facts.py`）。

**它补哪一环**：`deliverable/manuscript.py` 是**纯函数**汇编器（正文 + 数据表 + References →
markdown），`references.py` 是元数据读取面。两者都还没有**产品路径** —— 只会被测试调用。
本模块把「本 run 的模型正文产物 + canonical 事实」装配成 `manuscript.md` 制品，
并在**报告相**（`report:` 声明的确定性执行体）里被调用：那次汇编本来就要读本 run 的
全部持久事实，手稿用的是**同一份**输入。

**为什么装配点在这里而不是手稿相里**（本轮的设计取舍，必须写明）：

- 手稿相**必须是会话相**（合约不声明 `report:`），否则编译期 `cross_phase_inputs` 会
  拒绝它的跨相 `inputs`（`_executor_consumes_declared_inputs` 对 `report`/`experiment`
  执行体一律返回 False）⇒ 模型**必须**能读到检索与立题材料，才写得出 Related Work 与
  Methods。于是手稿相产出的是**正文**（`manuscript_narrative`），不是最终 markdown。
- 装配 `manuscript.md` 需要 `reviews` / `run` 两个执行期事实（判词、汇编时状态），
  它们只在报告相的装配面在场（`ReportTaskDeps` / `SessionSpecContext.run`）。
- ⇒ 分工：**模型写正文**（手稿相，会话产物），**汇编器写数字与参考文献**（报告相，
  确定性装配）。制品的 `created_by` 记 `model_assisted:<agent>` —— 不冒充纯模型撰写，
  也不冒充纯汇编（`fix_policy.forbidden` 明令不许把「确定性汇编」说成「模型撰写」）。

**两种「空」必须分得开**：

- 本 run **没有** `manuscript_narrative` 制品 ⇒ 返回 `None`（这次 run 没走手稿相）
  —— 报告相的既有输出**逐字节不变**；
- 制品在、但解不出正文 / 正文违反数字禁令 / 引用不闭合 ⇒ **点名抛错**
  （`ManuscriptError`），由报告任务以 `EXECUTION_FAILURE` 收敛 —— 不静默产出一份
  「看起来像手稿」的残件。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.deliverable.manuscript import (
    MANUSCRIPT_ARTIFACT_NAME,
    MANUSCRIPT_KEYS,
    MANUSCRIPT_MIME,
    ManuscriptAdmission,
    ManuscriptError,
    build_manuscript,
    manuscript_digest,
    validate_manuscript,
)
from packages.application.deliverable.research_report import ReportInputs
from packages.application.run_orchestration.manuscript_facts import manuscript_facts
from packages.application.run_orchestration.phase_input_material import (
    ENVELOPE_CONTENT_KEY,
    ENVELOPE_MARK_KEY,
    declared_object,
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

#: 手稿**正文**制品的名字（手稿相会话产出；制品的 `id` 尾段）。
NARRATIVE_ARTIFACT_NAME = "manuscript_narrative"
#: 正文制品 `created_by` 的前缀（装配层写的归属：模型正文 + 汇编器数字）。
ASSEMBLED_CREATOR_PREFIX = "model_assisted:"


@dataclass(frozen=True, slots=True)
class ManuscriptAdmissionResult:
    """一次手稿装配的产物（制品 + 归因面 + 参考文献读数）。"""

    artifact: Artifact
    markdown: str
    admission: ManuscriptAdmission
    #: 本 run 参考文献条数（判据与读面共用；0 = 没有可引用的记录）。
    reference_count: int
    #: 逐条缺失说明（空 = 全部完整）。
    problems: tuple[str, ...]


def manuscript_narrative_of_run(
    artifacts: Any, evidence: tuple[Any, ...]
) -> Mapping[str, Any] | None:
    """本 run 的**模型正文**（无制品 ⇒ `None`；解不出 / 多制品 ⇒ 点名抛错）。"""
    artifact_id = _narrative_artifact_id(evidence)
    if artifact_id is None:
        return None
    return _narrative_block(artifacts, artifact_id)


# `PLR0913`：装配面 —— 五个 Port + run_id + created_by，少一个就得让调用方先拼对象
# （与 `experiment_task_for` / `report_task_for` 的装配面豁免同一纪律）。
def assemble_manuscript(  # noqa: PLR0913
    artifacts: Any,
    ledger: Any,
    reviews: Any,
    run: Any,
    run_id: str,
    *,
    created_by: str,
) -> ManuscriptAdmissionResult | None:
    """本 run 的正文产物 + canonical 事实 → `manuscript.md`（无正文制品 ⇒ `None`）。

    `created_by` 由调用方给出**真实的**执行者标识（报告相知道 agent id）——
    本模块不发明归属。
    """
    from packages.application.run_orchestration.report_facts import evidence_of_run

    block = manuscript_narrative_of_run(artifacts, evidence_of_run(ledger, run_id))
    if block is None:
        return None
    facts = manuscript_facts(artifacts, ledger, reviews, run, run_id)
    sections = {key: str(block.get(key) or "") for key in MANUSCRIPT_KEYS}
    validate_manuscript(sections, facts.references)
    admission = ManuscriptAdmission(
        author=f"{ASSEMBLED_CREATOR_PREFIX}{created_by}",
        returned_model=str(block.get("returned_model") or ""),
        digest=manuscript_digest(sections),
        sections=sections,
    )
    markdown = build_manuscript(facts.inputs, admission, facts.references)
    artifact = _put_manuscript(artifacts, run_id, markdown, admission)
    _register(ledger, run_id, artifact, facts.inputs, admission)
    return ManuscriptAdmissionResult(
        artifact=artifact,
        markdown=markdown,
        admission=admission,
        reference_count=len(facts.references.entries),
        problems=facts.references.problems,
    )


def _narrative_artifact_id(evidence: tuple[Any, ...]) -> str | None:
    """证据里 `:manuscript_narrative` 制品的 id（零条 ⇒ `None`；多于一条 ⇒ 点名）。"""
    suffix = f":{NARRATIVE_ARTIFACT_NAME}"
    matches = sorted({
        str(item.artifact_id)
        for item in evidence
        if item.artifact_id and str(item.artifact_id).endswith(suffix)
    })
    if not matches:
        return None
    if len(matches) > 1:
        raise ManuscriptError(
            f"run evidence carries {len(matches)} distinct {NARRATIVE_ARTIFACT_NAME!r} artifacts "
            f"({matches}); the manuscript body would be undecidable"
        )
    return matches[0]


def _narrative_block(artifacts: Any, artifact_id: str) -> Mapping[str, Any]:
    """正文制品 → 八个键的对象（解不出 ⇒ 点名）。

    **三层都认**（真实会话与受控夹具的形状不同，本轮必须同时支持）：

    1. 会话交付物信封：`{manuscript_narrative: {content: "<模型全文>", declared_artifact: …}}`
       —— `_deliverable` 的产物，正文里的 JSON 块才是答案；
    2. 直形态：顶层就是 `{manuscript_narrative: {…八个键…}}`；
    3. 最外层就是八个键（测试可以直接落这种形状）。

    解不出来不是「没有」（那由 `manuscript_narrative_of_run` 的 `None` 表示）⇒ 点名抛错。
    """
    raw = artifacts.get(artifact_id).decode("utf-8")
    try:
        parsed: Any = json.loads(raw)
    except ValueError as error:
        raise ManuscriptError(
            f"{NARRATIVE_ARTIFACT_NAME} artifact {artifact_id} is not valid JSON: {error}"
        ) from error
    found = _unwrap(parsed, artifact_id, depth=0)
    if found is None:
        raise ManuscriptError(
            f"{NARRATIVE_ARTIFACT_NAME} artifact {artifact_id} carries no object with the keys "
            f"the contract prescribes ({', '.join(MANUSCRIPT_KEYS)})"
        )
    return found


def _unwrap(payload: Any, artifact_id: str, *, depth: int) -> Mapping[str, Any] | None:
    """信封 / 具名块 / 裸对象三层逐层下钻（`None` = 这一层不是答案，交给调用方点名）。"""
    if not isinstance(payload, Mapping) or depth > 3:
        return None
    if ENVELOPE_MARK_KEY in payload and isinstance(payload.get(ENVELOPE_CONTENT_KEY), str):
        # 信封：`declared_object` 会按期望键在正文里找块（解不出它自己点名）。
        return _unwrap(
            declared_object(payload, key=NARRATIVE_ARTIFACT_NAME), artifact_id, depth=depth + 1
        )
    inner = payload.get(NARRATIVE_ARTIFACT_NAME)
    if isinstance(inner, Mapping):
        return _unwrap(inner, artifact_id, depth=depth + 1)
    if all(key in payload for key in MANUSCRIPT_KEYS):
        return payload
    return None


def _put_manuscript(
    artifacts: Any, run_id: str, markdown: str, admission: ManuscriptAdmission
) -> Artifact:
    """手稿字节 → 内容寻址制品（run 级 id；重复装配 ⇒ 覆盖写，digest 重算）。"""
    content = markdown.encode("utf-8")
    artifact = Artifact(
        id=f"{run_id}:{MANUSCRIPT_ARTIFACT_NAME}",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type=MANUSCRIPT_MIME,
        storage_uri=None,
        created_by=admission.author,
        source_refs=[f"run:{run_id}"],
        classification="research_manuscript",
    )
    artifacts.put(artifact, content)
    artifacts.mark(artifact.id, ArtifactState.VERIFIED)
    return artifact


def _register(
    ledger: Any,
    run_id: str,
    artifact: Artifact,
    inputs: ReportInputs,
    admission: ManuscriptAdmission,
) -> None:
    """手稿制品 → SourceRecord + Evidence + Claim（**GENERATED**：本系统装配）。"""
    if ledger is None:
        return
    source = SourceRecord(
        origin=f"manuscript:{run_id}:{MANUSCRIPT_ARTIFACT_NAME}",
        content_digest=str(artifact.digest),
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
        parser_version="research-manuscript-assembler-v1",
    )
    ledger.register_source(source)
    evidence = Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=source.origin,
        content_digest=str(artifact.digest),
        extracted_by=admission.author,
        captured_at=Timestamp.now(),
        artifact_id=artifact.id,
        run_id=run_id,
    )
    ledger.register_evidence(evidence)
    claim_id = f"claim:manuscript:{run_id}"
    ledger.register_claim(
        Claim(
            id=claim_id,
            statement=(
                f"Run {run_id} assembled {MANUSCRIPT_ARTIFACT_NAME} from {len(inputs.sources)} "
                f"retrieved source(s) and {len(inputs.metrics)} measured metric(s)"
            ),
            status=ClaimStatus.PROPOSED,
            author=admission.author,
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


def assembled_message(admission: Any, manuscript: "ManuscriptAdmissionResult | None") -> str:
    """报告任务的成功消息：报告总是有；手稿**只在真的装配出**时才进消息（不假装有）。"""
    message = f"report {admission.artifact.id} assembled (digest {admission.artifact.digest})"
    if manuscript is not None:
        message += f"; manuscript {manuscript.artifact.id} assembled"
    return message


def maybe_assemble_manuscript(deps: Any, task: Any, spec_context: Any) -> Any | None:
    """装配方开了开关 ⇒ 装一份手稿（本 run 没有正文制品 ⇒ `None`，那是正确读数不是失败）。

    放在本模块而不是 `report_task.py`：那里贴着 450 行硬上限（规模门），而「手稿怎么装」
    与「报告怎么装」是两件事 —— 派发面只需知道「有没有多产一件」。

    GOAL-20261029-100 EC-03：手稿装配**之后**再装一份 `response_letter.md`（作者逐条
    回应评审点）。它接在这里而不是另开一相：应答信的全部输入（评审点 + 作者应答）在
    报告相都已落库，另开一相只会多一次会话而没有新事实。**本 run 没有应答产物 ⇒
    不写这封信**（没做过返修就产出一封应答信，等于补造证据）。
    """
    if not getattr(deps, "manuscript", False):
        return None
    run_id = str(task.run_id.value)
    result = assemble_manuscript(
        deps.artifacts,
        deps.ledger,
        deps.reviews,
        spec_context.run,
        run_id,
        created_by=spec_context.agent.id,
    )
    maybe_assemble_response_letter(deps.artifacts, deps.ledger, deps.reviews, run_id)
    return result


def maybe_assemble_response_letter(
    artifacts: Any, ledger: Any, reviews: Any, run_id: str
) -> Any | None:
    """本 run 的**作者应答产物** + 评审点 → `response_letter.md`（无应答产物 ⇒ `None`）。

    **两种「空」必须分得开**（与手稿那一格同一纪律）：

    - 本 run **没有** `author_responses` 制品 ⇒ 返回 `None`（这次 run 没走返修回路）——
      不写一封空信，那会被读成「返修已回应」；
    - 制品在、但漏答 / 编造 `point_id` / 重复应答 / 畸形 ⇒ **点名抛错**，由报告任务以
      `EXECUTION_FAILURE` 收敛 —— 不静默产出一封看起来像应答信的残件。

    评审点由 `review_points.review_points_of_run` 派生（**与提示词那一段同一个函数**）：
    两处各派生一次的话，模型照提示词逐条答完、汇编器仍会判漏答（本 GOAL 实测到
    「提示词里 17 条、汇编时 19 条」这个形态）。不需要任何新表 / 新列 ⇒ 无迁移风险。
    """
    from packages.application.deliverable.author_response import (
        RESPONSE_LETTER_NAME,
        parse_responses,
        response_letter,
    )
    from packages.application.run_orchestration.report_facts import evidence_of_run
    from packages.application.run_orchestration.review_points import review_points_of_run

    content = _response_artifact_content(artifacts, evidence_of_run(ledger, run_id))
    if content is None:
        return None
    points = review_points_of_run(artifacts, ledger, run_id)
    markdown = response_letter(points, parse_responses(content))
    artifact = _put_response_letter(artifacts, run_id, markdown, RESPONSE_LETTER_NAME)
    _register_response_letter(ledger, run_id, artifact, len(points))
    return artifact


def _register_response_letter(ledger: Any, run_id: str, artifact: Artifact, points: int) -> None:
    """应答信 → SourceRecord + Evidence + Claim（**GENERATED**：本系统汇编）。

    **必须注册**（实测缺口）：只 `put` 进 `ArtifactStore` 的件**不在读面上** ——
    `GET /runs/{id}/artifacts` 走的是 claim→relation 投影，没挂关系的制品读不到。
    手稿有 `_register`，应答信同样要有；否则「信产出了」只能在进程内看见。
    """
    if ledger is None:
        return
    source = SourceRecord(
        origin=f"author_response:{run_id}",
        content_digest=str(artifact.digest),
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
        parser_version="author-response-assembler-v1",
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
    claim_id = f"claim:author_response:{run_id}"
    ledger.register_claim(
        Claim(
            id=claim_id,
            statement=(f"Run {run_id} answered {points} review point(s) in {artifact.id}"),
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


def _response_artifact_content(artifacts: Any, evidence: tuple[Any, ...]) -> str | None:
    """本 run 的应答制品正文（**不在场 ⇒ `None`**；多于一件 ⇒ 点名）。

    读取面与手稿正文同一手法（证据投影 → `:author_responses` 制品），只取**内容字节**：
    解包交给 `parse_responses`（信封 + 围栏块都认，与决定块同一处实现）。
    """
    from packages.application.deliverable.author_response import (
        RESPONSE_ARTIFACT_NAME,
        ResponseError,
    )

    ids = [
        str(item.artifact_id)
        for item in evidence
        if str(item.artifact_id or "").endswith(f":{RESPONSE_ARTIFACT_NAME}")
    ]
    if not ids:
        return None
    if len(ids) > 1:
        raise ResponseError(
            f"run carries {len(ids)} {RESPONSE_ARTIFACT_NAME} artifacts; a response letter must "
            f"be assembled from exactly one ({sorted(ids)})"
        )
    return str(artifacts.get(ids[0]).decode("utf-8"))


def _put_response_letter(artifacts: Any, run_id: str, markdown: str, name: str) -> Artifact:
    """应答信字节 → 内容寻址制品（run 级 id；重复装配 ⇒ 覆盖写，digest 重算）。"""
    content = markdown.encode("utf-8")
    artifact = Artifact(
        id=f"{run_id}:{name}",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type=MANUSCRIPT_MIME,
        storage_uri=None,
        created_by="system:author-response-assembler",
        source_refs=[f"run:{run_id}"],
        classification="author_response",
    )
    artifacts.put(artifact, content)
    artifacts.mark(artifact.id, ArtifactState.VERIFIED)
    return artifact


__all__ = [
    "ASSEMBLED_CREATOR_PREFIX",
    "MANUSCRIPT_ARTIFACT_NAME",
    "NARRATIVE_ARTIFACT_NAME",
    "ManuscriptAdmissionResult",
    "assemble_manuscript",
    "assembled_message",
    "manuscript_narrative_of_run",
    "maybe_assemble_manuscript",
    "maybe_assemble_response_letter",
]
