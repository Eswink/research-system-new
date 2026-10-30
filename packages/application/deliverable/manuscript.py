"""**投稿形状的手稿**（IMRaD）：模型写正文，汇编器写数字与参考文献。

**它补哪一格**（GOAL-20261028-099 靶子 1）：此前的产物是**四节中文研究报告**（
`research_report.py` 的 `SECTION_HEADINGS`），来源渲染成 Python `dict` 字面量。
本模块产出的是**投稿形状**：英文 IMRaD 六节 + Abstract + `References`，
正文里的数字**只出现在汇编器写的图表数据表里**。

**核心接缝（这是本模块存在的全部理由）**：手稿相必须是**会话相**（合约不声明
`report:`，否则编译期 `cross_phase_inputs` 会拒绝它的跨相 `inputs`）⇒ **模型会写下正文**，
而正文里**不能有数字**（数字必须可核）。于是把文档切成**两块互不越界的面**：

1. **正文**（Abstract + 六个编号节）—— **模型**写的散文。除引用标记 `[n]` 外
   **不得出现任何 Unicode 十进制数位**：写了就**点名拒绝**（`ManuscriptError`），
   **不静默抽掉**（静默改写会让「这段是谁说的」不可判 —— 与 `report_narrative` 同一条纪律）。
2. **图表数据表 + References** —— **汇编器**写的。数据表的每一行带来源列、值逐字取自
   `ReportInputs`（四个既有读面）；References 的每一条**逐字**来自落盘的 tool-result
   字节（`references.py`）。

**引用编号的映射由汇编器保证**（模型只写 `[1]`…`[n]`，不知道该编号指向哪条文献）：

- 正文里任何 `[k]` 必须满足 `1 <= k <= n`（越界 ⇒ 点名拒绝）；
- 每一条 References **至少被引用一次**（孤儿条目 ⇒ 点名拒绝）—— 两向合起来才是
  「正文 `[n]` 与 References 逐条一一映射」。

**为什么模型不知道编号指向哪篇**：来源标识（PMID / DOI）**本身是数字串**，把它发给
模型是**请它违规**（`report_narrative.narrative_prompt` 已实测过这一点）。因此任务书
只给条数、以及**不含数字的标题**；含数字的标题按「扣留」登记，不发给模型。

**如实边界**：本模块**不判**叙述的**科学质量**，也**不判**引用是否**恰当**（`[2]` 是否
真的支持那句话）；它判的是「谁写的」「数字在哪」「编号是否闭合」三件结构事实。
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.deliverable.manuscript_quality import (
    ManuscriptQuality,
    validate_quality,
)
from packages.application.deliverable.references import ReferenceTable, render_references
from packages.application.deliverable.report_narrative import (
    FACT_TABLE_COLUMNS,
    NarrativeError,
    fact_ledger,
    fact_table_markdown,
)
from packages.application.deliverable.research_report import ReportInputs

#: 手稿制品的文件名（合约 `research_manuscript` 声明的名字）。
MANUSCRIPT_ARTIFACT_NAME = "manuscript.md"
#: 手稿制品的 MIME 类型（`text/markdown` ⇒ 命中既有的内联预览白名单）。
MANUSCRIPT_MIME = "text/markdown"

#: 手稿的八个叙述键（**标题** + 七节正文）。模型必须逐个给出。
MANUSCRIPT_KEYS: tuple[str, ...] = (
    "title",
    "abstract",
    "introduction",
    "related_work",
    "methods",
    "results",
    "discussion",
    "conclusion",
)

#: 七个节的二级标题（**逐字**；判据按它定位，改字 = 改契约）。
SECTION_HEADINGS: tuple[str, ...] = (
    "## Abstract",
    "## 1. Introduction",
    "## 2. Related Work",
    "## 3. Methods",
    "## 4. Results",
    "## 5. Discussion",
    "## 6. Conclusion",
)

#: 节标题与叙述键的**一一对应**（顺序即文档顺序）。
SECTION_KEYS: tuple[str, ...] = MANUSCRIPT_KEYS[1:]

#: 参考文献的二级标题（模型**不写**这一节）。
REFERENCES_HEADING = "## References"

#: 图表数据表的标题（在 `Results` 里；**数字只在这里**）。
DATA_TABLE_HEADING = (
    "### Table 1. Measured quantities and retrieved records "
    "(assembler-written; the only place in this manuscript where numbers appear)"
)

#: 正文里的引用标记（`[1]`、`[12]`）——**唯一**的语法定义。
CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class ManuscriptError(NarrativeError):
    """手稿不可用（缺键 / 正文含数字 / 引用越界 / 孤儿条目）—— **点名**，不改写不丢弃。"""


@dataclass(frozen=True, slots=True)
class ManuscriptAdmission:
    """一次手稿叙述的**归因面**（谁写的 / 写了什么 / 引用闭合与否）。"""

    #: 装配方声明的执行者（`model:<endpoint>/<model>` 形态；与 `Artifact.created_by` 同值）。
    author: str
    #: 供应商**返回**的模型名（与声明名可能不同 —— 同名漂移必须可见，AGENTS.md §4）。
    returned_model: str
    #: 叙述正文的 `sha256`（规范 JSON 文本）。
    digest: str
    #: 八个键的正文（已通过数字禁令与引用闭合判据）。
    sections: Mapping[str, str]


def _first_numeral(text: str) -> str | None:
    """去掉引用标记后，正文里的第一个 Unicode 十进制数位（没有 ⇒ `None`）。"""
    stripped = CITATION_PATTERN.sub(" ", text)
    for char in stripped:
        if unicodedata.category(char) == "Nd":
            return char
    return None


def citation_marks(text: str) -> tuple[int, ...]:
    """一段正文里的引用编号（按出现顺序；重复保留 —— 调用方负责去重）。"""
    return tuple(int(match.group(1)) for match in CITATION_PATTERN.finditer(text))


def validate_manuscript(sections: Mapping[str, str], table: ReferenceTable) -> None:
    """八键齐备、正文不含数字（引用标记除外）、引用**双向闭合**；违反即点名拒绝。

    三件事各自点名（不合并成一句「手稿不合法」：判词要能指出**哪一节**、**哪个编号**）。

    **射程（有意只到结构面）**：本函数判「谁写的 / 数字在哪 / 编号是否闭合」三件**结构
    事实**，**不**判叙述质量 —— 那是 `manuscript_quality.validate_quality` 的事，挂在
    **装配面**（`manuscript_assembly.assemble_manuscript`）而不是这里。分开的理由：把品质
    判据塞进结构入口，会让「编号越界」这类**结构**用例因为夹具正文写得短而红 —— 判词
    指向错误的面（本 GOAL 实测到 5 处这样的连带红）。
    """
    missing = [key for key in MANUSCRIPT_KEYS if not str(sections.get(key) or "").strip()]
    if missing:
        raise ManuscriptError(f"manuscript is missing these sections: {', '.join(missing)}")
    for key in MANUSCRIPT_KEYS:
        found = _first_numeral(str(sections[key]))
        if found is not None:
            raise ManuscriptError(
                f"manuscript section {key!r} contains the numeral {found!r}: every quantity in "
                "the body must be referred to by name (the data table carries the numbers), and "
                "citations must be single [n] marks"
            )
    cited = {index for key in MANUSCRIPT_KEYS for index in citation_marks(str(sections[key]))}
    total = len(table.entries)
    out_of_range = sorted(index for index in cited if index > total)
    if out_of_range:
        raise ManuscriptError(
            f"the body cites {out_of_range} but this run's reference list has {total} "
            f"entr{'y' if total == 1 else 'ies'}: a citation that resolves to nothing is a "
            "dangling reference"
        )
    orphans = sorted(set(range(1, total + 1)) - cited)
    if orphans:
        raise ManuscriptError(
            f"reference {orphans} is never cited in the body: every listed work must be a "
            "work the manuscript actually cites"
        )


def validate_manuscript_quality(sections: Mapping[str, str], table: ReferenceTable) -> None:
    """**品质三条**（GOAL-20261030-101 EC-01）：引用—主张相关 / 节间不重复 / 节非空洞。

    单独一个入口、且由**装配面** `assemble_manuscript` 调用 —— 不是 `validate_manuscript`
    的一部分。理由见后者的 docstring（结构用例不该因为正文短而红）。

    判负类型是 `manuscript_quality.ManuscriptQualityError`（**不**折成 `ManuscriptError`）：
    「写得不对」与「装不起来」是两类事实，报告任务的判词分类必须能分开读。
    """
    validate_quality(sections, ManuscriptQuality.of(table.entries))


def parse_manuscript(content: str | None) -> Mapping[str, str]:
    """模型输出 → 八个键的正文（JSON 对象；畸形即点名，不猜）。"""
    if content is None or not content.strip():
        raise ManuscriptError("manuscript narrative is empty")
    try:
        parsed: Any = json.loads(content)
    except ValueError as error:
        raise ManuscriptError(f"manuscript narrative is not a JSON object: {error}") from error
    if not isinstance(parsed, Mapping):
        raise ManuscriptError(
            f"manuscript narrative must be a JSON object, got {type(parsed).__name__}"
        )
    return {key: str(parsed.get(key) or "") for key in MANUSCRIPT_KEYS}


def manuscript_digest(sections: Mapping[str, str]) -> str:
    """叙述正文的规范摘要（键排序 + `ensure_ascii=False` ⇒ 同一内容同一串）。"""
    payload = json.dumps(
        {key: sections[key] for key in MANUSCRIPT_KEYS}, ensure_ascii=False, sort_keys=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _digit_free(title: str) -> bool:
    """标题里有没有任何 Unicode 十进制数位（含数字的标题**不发给模型**）。"""
    return not any(unicodedata.category(char) == "Nd" for char in title)


def build_manuscript(
    inputs: ReportInputs,
    admission: ManuscriptAdmission,
    table: ReferenceTable,
) -> str:
    """数据表 + References（汇编器）+ 正文（模型）→ 一份手稿（同输入同叙述 ⇒ 逐字节相同）。"""
    if not inputs.run_id.strip():
        raise ManuscriptError("manuscript requires a non-empty run_id")
    validate_manuscript(admission.sections, table)
    rows = fact_ledger(inputs)
    lines = _header_lines(inputs, admission)
    for heading, key in zip(SECTION_HEADINGS, SECTION_KEYS, strict=True):
        lines += [heading, "", admission.sections[key].strip(), ""]
        if key == "results":
            lines += [DATA_TABLE_HEADING, "", fact_table_markdown(rows), ""]
    lines += render_references(table).splitlines()
    lines += ["", *_footnote_lines(table, rows, admission)]
    return "\n".join(lines).rstrip("\n") + "\n"


def _header_lines(inputs: ReportInputs, admission: ManuscriptAdmission) -> list[str]:
    """抬头：标题（模型）+ 四个**汇编器写的**归因/状态字段。

    状态写成「汇编时状态」（不是「终态」）：手稿是**在 run 内**汇编的，那时终态尚未产生
    （与 `research_report._header_lines` 同一条口径）。
    """
    lines = [
        f"# {admission.sections['title'].strip()}",
        "",
        f"- **run**: `{inputs.run_id}`",
        f"- **protocol**: `{inputs.protocol_id}`",
        f"- **assembly state**: `{inputs.state}`",
        f"- **narrative author**: {admission.author}",
        f"- **returned model**: `{admission.returned_model}`",
        f"- **narrative digest**: `{admission.digest}`",
    ]
    if inputs.objective:
        lines.append(
            f"- **research question (this run's own; quoted verbatim)**: {inputs.objective}"
        )
    return [*lines, ""]


def _footnote_lines(
    table: ReferenceTable, rows: tuple[dict[str, str], ...], admission: ManuscriptAdmission
) -> list[str]:
    """文末的**如实登记**（谁写了哪块面、缺什么）。"""
    lines = [
        "**Who wrote which face (recorded, not asserted)**:",
        "",
        f"- The Abstract and the six numbered sections are **model-written** "
        f"({admission.author}, returned model `{admission.returned_model}`): the body carries "
        "no digits — a numeral is refused by name, never silently stripped.",
        f"- The data table under Results and the whole of {REFERENCES_HEADING} are "
        "**assembler-written**: every value is taken verbatim from this run's persisted facts, "
        f"every reference line from the retrieved tool-result bytes. Columns: "
        f"{', '.join(FACT_TABLE_COLUMNS)}.",
        "- The manuscript covers **this run only**; conclusions across runs are not in it, and "
        "the reliability of the findings rests on the upstream phases' own criteria.",
    ]
    if not rows:
        lines.append("- **This run carried no retrievable facts** ⇒ the data table has no rows.")
    if not table.entries:
        lines.append("- **This run retrieved no citable record** ⇒ the reference list is empty.")
    if table.problems:
        lines.append(
            f"- **{len(table.problems)} record(s) have incomplete metadata** and are named under "
            "References (not filled in with placeholders)."
        )
    return lines


__all__ = [
    "CITATION_PATTERN",
    "DATA_TABLE_HEADING",
    "MANUSCRIPT_ARTIFACT_NAME",
    "MANUSCRIPT_KEYS",
    "MANUSCRIPT_MIME",
    "REFERENCES_HEADING",
    "SECTION_HEADINGS",
    "SECTION_KEYS",
    "ManuscriptAdmission",
    "ManuscriptError",
    "build_manuscript",
    "citation_marks",
    "manuscript_digest",
    "parse_manuscript",
    "validate_manuscript",
]
