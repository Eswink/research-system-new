"""报告汇编的**事实读取面**（GOAL-20261014-077 EC-02；自 `report_task.py` 拆出守规模门）。

**为什么单列**：`report_task.py` 有 450 行硬上限（规模门），而它有两条职责 ——
「把持久事实读成 `ReportInputs`」与「把报告字节准入 canonical」。本模块放前者
（纯读；四个来源逐个对应一个**既有**读面），后者留在 `report_task.py`
（与全仓既有的「读面 vs 写面分列」同一手法：`read_surface.py` vs `read_provider.py`）。

**四条读法各自同源**（本模块不新造第二套查询，也不重算任何数字）：

| 读什么 | 怎么读 | 与哪个既有读面同源 |
| --- | --- | --- |
| run / 协议 / 状态 | `RunStore.get_run` | `run.read` 工具 / `GET /runs/{id}` |
| 来源逐条 | relation 投影的工具证据 → 制品内容里的 `articles[].pmid` | `GET /runs/{id}/evidence` |
| 指标 | 实验证据指向的制品内容里的数值项 | `GET /runs/{id}/experiments` |
| 判词 | `ReviewFindingStore.for_run` 的最近一次（按 `reviewed_at`） | `GET /runs/{id}/reviews` |

**如实边界**：来源只认**工具证据**（`source_ref` 前缀 `tool:`）—— 声明输入
（`USER_PROVIDED`）不算检索来源，与 `count_retrieved_sources` 同一口径；
指标只收数值与非空字符串项（布尔 / 嵌套对象**不折算**）。
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from packages.application.deliverable.research_report import ReportInputs
from packages.application.experiments.types import RESULT_FILE
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.run_orchestration.report_question import question_objective
from packages.domain.evidence import Evidence

#: 来源只认**工具证据**（`source_ref` 的固定前缀，由 `tool_evidence.source_origin_for` 生成）。
TOOL_SOURCE_PREFIX = "tool:"


def report_inputs(
    artifacts: ArtifactStore,
    ledger: EvidenceLedger,
    reviews: Any,
    run: Any,
    run_id: str,
) -> ReportInputs:
    """本 run 的持久事实 → `ReportInputs`（每条都经既有读面；见模块 docstring）。

    `run` 是**执行期在场的那份领域实体**（`SessionSpecContext.run`），不是从存储读的：
    执行期间控制面还没把 run 行落库 ⇒ 读存储只会读到「未知 run」。
    """
    evidence = evidence_of_run(ledger, run_id)
    return ReportInputs(
        run_id=run_id,
        protocol_id=str(run.protocol_id),
        state=str(run.state),
        sources=sources_of(artifacts, evidence),
        metrics=metrics_of(artifacts, evidence),
        verdict=latest_verdict(reviews, run_id),
        # GOAL-20261024-096 EC-03：第 1 节的问题正文来自**本 run 自己**的
        # `research_question` 制品（读取面在 `report_question.py`；无该制品 ⇒ `None`，
        # 渲染器把那一节写成「无 + 原因」）。此前这里写死 `None` ⇒ 该节恒空。
        objective=question_objective(artifacts, evidence),
        budget=None,
    )


def evidence_of_run(ledger: EvidenceLedger, run_id: str) -> tuple[Evidence, ...]:
    """本 run 的证据（经 claim→relation 投影，与 `services/api/run_evidence` 同一口径）。

    **只经 relation 走**：只登记不挂关系的证据读不到 —— 既有读面语义，本处不另开一条
    （承 `MEM: evidence-read-face-claim-relation`）。
    """
    found: list[Evidence] = []
    seen: set[str] = set()
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            evidence_id = relation.evidence_id
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            try:
                item = ledger.get_evidence(evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态：missing evidence）
                continue
            if item.run_id == run_id:
                found.append(item)
    return tuple(sorted(found, key=lambda item: item.id))


def tool_evidence(evidence: tuple[Evidence, ...]) -> tuple[Evidence, ...]:
    """来源只认**工具证据**（前缀固定；声明输入不算，见模块 docstring）。"""
    return tuple(
        item
        for item in evidence
        if str(item.source_ref).startswith(TOOL_SOURCE_PREFIX) and item.artifact_id
    )


def sources_of(
    artifacts: ArtifactStore, evidence: tuple[Evidence, ...]
) -> tuple[Mapping[str, str], ...]:
    """逐条来源（真标识 + 证据 id）——标识**逐字取自落库的工具结果内容**。

    为什么读内容而不从 id 里截串：`evidence.id` / `source_ref` 里的标识是**拼接产物**
    （`literature_read:39284801+40601758`）；真实标识（PMID / DOI / 标题）在工具结果的
    字节里。读它 = SELECT 持久事实；截串 = 在应用层重新发明一套解析。
    """
    entries: list[Mapping[str, str]] = []
    seen: set[str] = set()
    for item in tool_evidence(evidence):
        assert item.artifact_id is not None
        for identifier, title in _identifiers(artifacts, item.artifact_id):
            if identifier in seen:
                continue
            seen.add(identifier)
            entry: dict[str, str] = {"identifier": identifier, "evidence_id": item.id}
            if title:
                entry["title"] = title
            entries.append(entry)
    return tuple(entries)


def _identifiers(artifacts: ArtifactStore, artifact_id: str) -> tuple[tuple[str, str], ...]:
    """工具结果内容 → `(标识, 标题)` 序列（读不到内容 ⇒ 空 —— 缺件不是编造）。"""
    payload = _json_object(artifacts, artifact_id)
    if payload is None:
        return ()
    articles = payload.get("articles")
    if isinstance(articles, list):
        pairs = [
            (_identifier_of(article), str(article.get("title") or ""))
            for article in articles
            if isinstance(article, Mapping)
        ]
        return tuple((identifier, title) for identifier, title in pairs if identifier)
    ids = payload.get("ids")
    if isinstance(ids, list):
        return tuple((str(item), "") for item in ids if str(item))
    return ()


def _identifier_of(article: Mapping[str, Any]) -> str:
    """单条记录的主标识（PMID 优先、退化到 DOI；都缺 ⇒ 空串）。"""
    for key in ("pmid", "doi"):
        value = article.get(key)
        if value:
            return str(value)
    return ""


def _json_object(artifacts: ArtifactStore, artifact_id: str) -> Mapping[str, Any] | None:
    """制品内容 → JSON 对象（不在场 / 非 JSON / 非对象 ⇒ `None`，由调用方如实处置）。"""
    if artifacts.meta(artifact_id) is None:
        return None
    try:
        parsed: Any = json.loads(artifacts.get(artifact_id).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


def metrics_of(
    artifacts: ArtifactStore, evidence: tuple[Evidence, ...]
) -> tuple[Mapping[str, str], ...]:
    """实验证据指向的制品里的指标（与 `GET /runs/{id}/experiments` 的**同一处**来源）。

    **来源是 `experiment_result.json` 的 `metrics` 块，只此一处**（`RESULT_FILE`；与 HTTP
    读面 `routers/experiments.py::_metrics_for` 读的**是同一份字节**）—— 这样判据
    「报告里的指标值 == 读面上的指标值」才可能逐字成立：两处若各读一份来源，
    漂移只是时间问题。

    值按 **JSON 逐字**取值：数字用其规范文本（`300.0` 就是 `300.0`，**不**归一成 `300`）、
    布尔用 `true` / `false`、字符串原样（空白串丢掉）。**不折算**：把 `true` 写成 `1`
    或把 `300.0` 写成 `300` 都是**编造**，而报告的第一条纪律是「不重算不编造」。

    **多臂（GOAL-20261015-079 EC-02 起）：同名指标**来自**不同实验**时，逐臂各出一行**
    并带上 `experiment_run_id`（**不得**让后一个静默覆盖前一个 —— 那是把「两臂的读数」
    丢成「一臂的读数」而报告看不出来）。**单臂时行为逐字不变**（一个名字一行、不带臂列）。
    """
    by_name: dict[str, dict[str, str]] = {}
    for item in evidence:
        if not item.experiment_run_id or not item.artifact_id:
            continue
        if not str(item.artifact_id).endswith(RESULT_FILE):
            continue
        payload = _json_object(artifacts, item.artifact_id)
        block = payload.get("metrics") if payload is not None else None
        if not isinstance(block, Mapping):
            continue
        for name, value in block.items():
            text = _metric_text(value)
            if text is not None:
                by_name.setdefault(str(name), {})[str(item.experiment_run_id)] = text
    return tuple(row for name in sorted(by_name) for row in _metric_rows(name, by_name[name]))


def _metric_rows(name: str, per_run: Mapping[str, str]) -> tuple[Mapping[str, str], ...]:
    """一个指标的读数行：**每个实验一行**（多臂 ⇒ 逐臂一行，不并格、不丢臂）。

    **为什么逐臂一行而不是并成一格**（本轮 live 取证**实测**到的真缺陷）：把两臂的值用
    分隔符连进**一格**会把 markdown 表格**撑成比表头多一列** ⇒ 渲染直接坏掉
    （`research_report._experiment_section` 的表头只有固定列数）。逐臂一行则：
    ① 两臂的读数都**在**；② 表格列数与表头**一致**；③ 读者一眼看出同名指标来自**多个实验**。

    **单臂**（该指标只在一个实验里出现）⇒ 逐字沿用既有形态（含 `experiment_run_id` 一列，
    值原样）—— 渲染器的三列表格由它按「有没有该列」自动分派。
    """
    return tuple(
        {"name": name, "value": per_run[run_id], "experiment_run_id": run_id}
        for run_id in sorted(per_run)
    )


def _metric_text(value: object) -> str | None:
    """一个指标值的**逐字**文本（不可渲染的形态 ⇒ `None`，不折算）。

    - `bool` 先判（Python 的 `bool` 是 `int` 的子类）：`true` / `false`；
    - `int` / `float`：`str()`（`300.0` 逐字保留，**不**归一）；
    - 非空字符串：原样（空白串 ⇒ `None`）；
    - 其余（嵌套对象 / 列表 / `None`）：`None` —— 报告不重算、不编造。
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return value if value.strip() else None
    return None


def latest_verdict(reviews: Any, run_id: str) -> Mapping[str, Any] | None:
    """**最近一次**验收结论（按 `reviewed_at`）—— 它就是评审 phase 对本 run 的判定。

    为什么按时间取而不是取最后一条：`for_run` 以 `finding_id` 排序，而 id 含执行期生成的
    UUID ⇒ **字典序 ≠ 执行序**。`reviewed_at` 是落库事实，取最大者是唯一可辩护的「最近」。
    本 phase 自己的结论在汇编**之后**才落库 ⇒ 这里读到的是它之前的那次（评审 phase 的判定）。
    """
    records = tuple(reviews.for_run(run_id))
    if not records:
        return None
    newest = max(records, key=lambda item: _stamp(item.finding.reviewed_at))
    finding = newest.finding
    return {
        "decision": str(finding.verdict),
        "reason": "; ".join(str(item) for item in finding.findings),
        "cited_facts": (f"contract={newest.contract_id}", f"task={newest.task_id}"),
    }


def _stamp(value: object) -> tuple[bool, str]:
    """排序键：有时间的排在没时间的之后（`reviewed_at` 可空，取逐字文本比大小）。"""
    return (value is not None, "" if value is None else str(value))


__all__ = [
    "TOOL_SOURCE_PREFIX",
    "evidence_of_run",
    "latest_verdict",
    "metrics_of",
    "report_inputs",
    "sources_of",
    "tool_evidence",
]
