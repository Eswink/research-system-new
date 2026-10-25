"""报告第 1 节的**问题正文**读取面（GOAL-20261024-096 EC-03）。

**为什么单列一个新模块**：`report_task.py` 已 433/450 行、`report_facts.py` 已 260 行，
规模门都贴线 ⇒ 读取逻辑放进新文件（与 `report_facts.py` 当年从 `report_task.py` 拆出
同一手法）。本模块只做一件事：把「本 run 自己提出的问题」从 canonical 读出来，
给报告的第 1 节用 —— 现状 `report_facts.report_inputs` 把 `objective` 写死为 `None`，
报告第 1 节因此永远是「（无：本 run 未声明目标）」。

**它读什么**：本 run 的 `research_question` 制品（问题相的产物）。怎么找到它：
**制品 id 是 `{task_id}:{产物名}`**（`result_handler._artifact_for_output`），任务 id 在
编排期才生成 ⇒ 不能拼名字；只能从**本 run 的证据投影**（`report_facts.evidence_of_run`，
claims → relations → evidence，与 `GET /runs/{id}/evidence` 同一口径）里找
`artifact_id` 以 `:research_question` 结尾的那条。多于一条 ⇒ 点名（不取第一个）。

**「正文」取哪一段**（两种形态都认，判别与 `phase_input_material.declared_object`
同一口径；正文**逐字节**取自制品原文，不重排、不重渲染）：

- **信封形态**（真实会话）：制品载荷 = `{declared_artifact: …, content: 模型全文}`。
  正文 = `content` 里带 `research_question` 键的那个 JSON 块的**原文切片**
  （GOAL-089 live 取证的引用形态：那一块就是模型声明的问题）；
- **直形态**（受控夹具）：载荷本身就是问题对象（`_artifact_for_output` 落盘时已按
  规范 JSON 序列化）⇒ 正文 = 制品原文。

**fail-closed**（点名失败，不编造、不回落）：

- 无制品（本 run 没有 `research_question` 证据）⇒ `None` —— 调用方把第 1 节写成
  「无 + 原因」（既有「缺事实不是失败」口径）；
- 制品在、但解不出问题对象（缺键 / 多块歧义 / 内容损坏）⇒ **点名抛错**
  （`ValueError`，报告任务会以 `EXECUTION_FAILURE` 收敛）—— 「读不到」与「没有」
  必须分得开，静默降级会让报告看起来像「没有问题」而其实是「读不出来」。

**边界**：只读 canonical（`ArtifactStore` + 证据投影）、零出网、零模型、零时钟；
本模块不判问题提得好不好（那要人评或评审面），也不把问题正文改写成「目标」。
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.run_orchestration.phase_input_material import ENVELOPE_MARK_KEY
from packages.domain.evidence import Evidence

#: 问题相的产物名（制品 id 的**尾段**；`{task_id}:research_question`）。
QUESTION_ARTIFACT_NAME = "research_question"
#: 信封里承载模型正文的键（与 `phase_input_material.ENVELOPE_CONTENT_KEY` 同值）。
_ENVELOPE_CONTENT_KEY = "content"
#: 问题对象在模型声明块里的键（合约 `research_question_proposal` 的规定形状）。
_QUESTION_KEY = QUESTION_ARTIFACT_NAME


def question_objective_of_run(
    artifacts: ArtifactStore, ledger: EvidenceLedger, run_id: str
) -> str | None:
    """本 run 的 `research_question` 正文（第 1 节的 `objective`；无 ⇒ `None`）。

    证据投影经 `report_facts.evidence_of_run`（与报告的其余事实**同一次**遍历的口径），
    本模块不另开一条查询。
    """
    from packages.application.run_orchestration.report_facts import evidence_of_run

    return question_objective(artifacts, evidence_of_run(ledger, run_id))


def question_objective(artifacts: ArtifactStore, evidence: tuple[Evidence, ...]) -> str | None:
    """已投影的证据 → 问题正文（无 ⇒ `None`；解不出 ⇒ 点名抛错）。"""
    artifact_id = _question_artifact_id(evidence)
    if artifact_id is None:
        return None
    return _question_text(artifacts, artifact_id)


def _question_artifact_id(evidence: tuple[Evidence, ...]) -> str | None:
    """证据里 `:research_question` 制品的 id（零条 ⇒ `None`；多于一条 ⇒ 点名）。"""
    suffix = f":{QUESTION_ARTIFACT_NAME}"
    matches = sorted({
        str(item.artifact_id)
        for item in evidence
        if item.artifact_id and str(item.artifact_id).endswith(suffix)
    })
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError(
            f"run evidence carries {len(matches)} distinct {QUESTION_ARTIFACT_NAME!r} "
            f"artifacts ({matches}); the report question would be undecidable"
        )
    return matches[0]


def _question_text(artifacts: ArtifactStore, artifact_id: str) -> str:
    """制品原文 → 问题正文的**逐字节**切片（信封解开，直形态原样）。"""
    raw = artifacts.get(artifact_id).decode("utf-8")
    try:
        payload: Any = json.loads(raw)
    except ValueError as error:
        raise ValueError(
            f"{QUESTION_ARTIFACT_NAME} artifact {artifact_id} is not valid JSON: {error}"
        ) from error
    if not isinstance(payload, Mapping):
        raise ValueError(f"{QUESTION_ARTIFACT_NAME} artifact {artifact_id} is not a JSON object")
    content = payload.get(_ENVELOPE_CONTENT_KEY) if ENVELOPE_MARK_KEY in payload else None
    if not isinstance(content, str):
        return raw.strip()
    block = _keyed_block_text(content, _QUESTION_KEY)
    if block is None:
        raise ValueError(
            f"{QUESTION_ARTIFACT_NAME} artifact {artifact_id} carries no JSON object with "
            f"the key {_QUESTION_KEY!r} (expected the shape the contract prescribes)"
        )
    return block


def _keyed_block_text(text: str, key: str) -> str | None:
    """模型全文 → 带 `key` 键的那个 JSON 块的**原文切片**（零/多块歧义都点名）。

    同一个对象可能被两种候选（围栏块 / 裸括号段）各切一次，差别只在首尾空白 ⇒
    按**解析值**去重（与 `phase_input_material._json_in_text` 同一口径）、取**最紧**的
    切片；真正得多块（多份不同的对象都带该键）才算歧义。
    """
    best: dict[Any, str] = {}
    for candidate in _json_candidates(text):
        try:
            parsed: Any = json.loads(candidate)
        except ValueError:
            continue
        if not isinstance(parsed, Mapping) or key not in parsed:
            continue
        marker = json.dumps(parsed, sort_keys=True, ensure_ascii=False)
        previous = best.get(marker)
        if previous is None or len(candidate.strip()) < len(previous):
            best[marker] = candidate.strip()
    if not best:
        return None
    if len(best) > 1:
        raise ValueError(
            f"the reply carries {len(best)} distinct JSON objects for {key!r}; "
            "the report question would be undecidable"
        )
    return next(iter(best.values()))


def _json_candidates(text: str) -> list[str]:
    """全文的 JSON 候选：整段 + 每个 ``` 围栏块 + 围栏里夹说明时的裸括号段。"""
    stripped = text.strip()
    candidates = [stripped]
    candidates.extend(_fenced_blocks(stripped))
    candidates.extend(_braced_segments(stripped))
    return candidates


def _fenced_blocks(text: str) -> list[str]:
    """全部 ``` 围栏的内容（容忍 ```json 之类的语言标记）。"""
    pieces = text.split("```")
    blocks: list[str] = []
    # 奇数下标是围栏内部（0 是块外文字）。
    for index in range(1, len(pieces), 2):
        body = pieces[index]
        newline = body.find("\n")
        blocks.append(body[newline + 1 :] if newline != -1 else body)
    return blocks


def _braced_segments(body: str) -> list[str]:
    """以 `{` 开头、配平 `}` 结尾的最大片段（字符串里的括号不算）。

    只做**括号配对**的粗切（不解析语法、不猜键名）：从每个 `{` 起找到配平的 `}`；
    引号内的一切（含转义）被字符串态吃掉 —— 与
    `phase_input_material._braced_segments` 同一切法（那份是私有的，此处不跨模块
    import 私有名；两份的语义由各自的判据钉住）。
    """
    segments: list[str] = []
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for index, char in enumerate(body):
        in_string, escaped, consumed = _advance_string_state(char, in_string, escaped)
        if consumed:
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                segments.append(body[start : index + 1])
    return segments


def _advance_string_state(char: str, in_string: bool, escaped: bool) -> tuple[bool, bool, bool]:
    """(在串内, 待转义, 本字符已被引号面吃掉)；纯状态推进，不碰括号计数。"""
    if in_string:
        if escaped:
            return True, False, True
        if char == "\\":
            return True, True, True
        if char == '"':
            return False, False, True
        return True, False, True
    if char == '"':
        return True, False, True
    return False, False, False


__all__ = [
    "QUESTION_ARTIFACT_NAME",
    "question_objective",
    "question_objective_of_run",
]
