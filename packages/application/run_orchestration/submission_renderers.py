"""投稿包五件制品的**渲染面**（GOAL-20261031-102 EC-03；装配与准入在 `submission_assembly`）。

**分工**：本模块只把**已校验的输入**（信正文、结构化 COI 字段、角色分派、制品清单）
变成 markdown 字节 —— 不做任何判定、不读存储、不碰时钟。判定（缺字段 / 越闭集 /
编造 digest）全部在 `submission_assembly`，渲染器收到的东西**已经**是可信形状。

**三条渲染纪律**（每条都可判）：

1. 信的正文**逐字**来自会话产物（汇编器只写抬头与归属行，不转述、不改写）；
2. `conflicts_of_interest.md` 把**结构化字段**渲染成机器可读的 fenced JSON 块 ——
   判据按字段读（`parse_coii_fields`），不读散文；
3. 清单面（数据可得性 / 补充材料）逐行 `| id | digest |` —— 行形态是判据的解析面
   （`_DIGEST_ROW`），不是装饰。
"""

from __future__ import annotations

import json
from typing import Mapping

from packages.application.deliverable.credit_roles import ROLE_CREDIT

#: 投稿会话产物名（合约 `submission_package` 的产物；信封键同名）。
SUBMISSION_ARTIFACT_NAME = "submission_package"
#: 五件投稿制品的名字（run 级 id `{run_id}:<name>`）。
COVER_LETTER_NAME = "cover_letter.md"
CONTRIBUTIONS_NAME = "author_contributions.md"
COI_NAME = "conflicts_of_interest.md"
DATA_AVAILABILITY_NAME = "data_availability.md"
SUPPLEMENTARY_NAME = "supplementary.md"
#: CRediT 的结构化字段键（**按字段读**，不是自由文本）。
HAS_CONFLICT_FIELD = "has_conflict"
STATEMENT_FIELD = "statement"

#: 清单行的形态（id + digest 两列；判据按它解析）。
ROW_FORMAT = "| `{artifact_id}` | `{digest}` |"


def cover_letter_md(text: str, run_id: str) -> str:
    """信的正文**逐字**引用（不转述）＋ 汇编器只写抬头与归属行。"""
    return (
        "# Cover Letter\n\n"
        f"Dear editors,\n\n{text}\n\n"
        "Sincerely,\nThe authors\n\n"
        "---\n\n"
        f"- **run**: `{run_id}`\n"
        "- **provenance**: the letter text above is the submission session's own words "
        f"(declared artifact `{SUBMISSION_ARTIFACT_NAME}`), assembled verbatim by the "
        "report phase\n"
    )


def contributions_md(pairs: tuple[tuple[str, str], ...], run_id: str) -> str:
    """分工：本 run 协议的 phase × role 分派，经闭集映射成 CRediT 术语。"""
    lines = [
        "# Author Contributions (CRediT)",
        "",
        "| Phase | Role | CRediT role |",
        "| --- | --- | --- |",
    ]
    for phase_id, role in pairs:
        lines.append(f"| `{phase_id}` | `{role}` | `{ROLE_CREDIT[role]}` |")
    lines += [
        "",
        "Derived mechanically from this run's frozen protocol role dispatch; the mapping "
        "from roles to CRediT terms is a declared table (`ROLE_CREDIT`), not a judgment.",
        "",
        f"- **run**: `{run_id}`\n",
    ]
    return "\n".join(lines).rstrip() + "\n"


def coi_md(fields: Mapping[str, object], run_id: str) -> str:
    """冲突声明：结构化字段**渲染成机器可读块**（判据按字段读，不是读散文）。"""
    return (
        "# Conflicts of Interest\n\n"
        "The submitting authors declare the following conflict-of-interest status.\n\n"
        "```json\n" + json.dumps(dict(fields), ensure_ascii=False) + "\n```\n\n"
        f"- **run**: `{run_id}`\n"
    )


def availability_md(inventory: tuple[tuple[str, str], ...], run_id: str) -> str:
    """数据可得性：本 run 的制品清单 + digest（逐行 `| id | digest |`）。"""
    lines = [
        "# Data Availability",
        "",
        "Every artifact this run had produced when the submission package was assembled, "
        "with its content digest; the artifact store serves the bytes by id.",
        "",
        "| Artifact | Digest |",
        "| --- | --- |",
    ]
    for artifact_id, digest in inventory:
        lines.append(f"| `{artifact_id}` | `{digest}` |")
    lines += ["", f"- **run**: `{run_id}`\n"]
    return "\n".join(lines).rstrip() + "\n"


def supplementary_md(inventory: tuple[tuple[str, str], ...], run_id: str) -> str:
    """补充材料索引：实验与工具结果制品（本 run 真的落盘的那些，不补造）。"""
    rows = [
        (artifact_id, digest)
        for artifact_id, digest in inventory
        if ":experiment" in artifact_id or artifact_id.startswith("tool-result:")
    ]
    lines = [
        "# Supplementary Material",
        "",
        "Index of this run's experiment outputs and tool-result records (raw bytes stay "
        "in the artifact store; this is the index, not a copy).",
        "",
        "| Artifact | Digest |",
        "| --- | --- |",
    ]
    for artifact_id, digest in rows:
        lines.append(f"| `{artifact_id}` | `{digest}` |")
    if not rows:
        lines += ["| — | — |", "", "_This run carried no experiment or tool-result artifacts._"]
    lines += ["", f"- **run**: `{run_id}`\n"]
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "CONTRIBUTIONS_NAME",
    "COI_NAME",
    "COVER_LETTER_NAME",
    "DATA_AVAILABILITY_NAME",
    "HAS_CONFLICT_FIELD",
    "STATEMENT_FIELD",
    "SUBMISSION_ARTIFACT_NAME",
    "SUPPLEMENTARY_NAME",
    "availability_md",
    "coi_md",
    "contributions_md",
    "cover_letter_md",
    "supplementary_md",
]
