"""GOAL-116 EC-01 的**判词侧**：PRD 的说法 vs 树的事实，逐条对拍。

**每条违反都以条号开头**（`C-R05` / `C-R10` / `C-CONSOLE` / …），所以反证臂可以
断言「点名了哪一条」，而不是只看「有没有红」。

判词只读 `Facts`（`prd_tree_facts.collect_facts` 的一次读数）与三份文档文本；
不改任何文件、不跑子进程、不出网。
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from tests.tooling.prd_tree_facts import (
    INDEX_PATH,
    LEGACY_POINTERS,
    NOT_JUDGED_THEMES,
    REQUIRED_CLAIMS,
    SECTION_TOPICS,
    STATUS_VOCAB,
    SUBMISSION_PIECES,
    Facts,
)

_BACKTICK = re.compile(r"`([^`]+)`")
_HEADING = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
_PATH_TOKEN = re.compile(r"[A-Za-z0-9_./-]+")
_PRD_LINK = re.compile(r"\]\([^)]*PRD\.md\)")
_TABLE_HEADER = "| ID | 需求 | 状态 | 判据 |"


@dataclass(frozen=True)
class RequirementRow:
    id: str
    cells: tuple[str, ...]
    raw: str

    @property
    def status(self) -> str:
        return self.cells[2] if len(self.cells) > 2 else ""

    @property
    def criteria(self) -> str:
        return self.cells[3] if len(self.cells) > 3 else ""


def headings(prd: str) -> dict[int, str]:
    return {int(number): title.strip() for number, title in _HEADING.findall(prd)}


def requirement_rows(prd: str) -> tuple[RequirementRow, ...]:
    rows: list[RequirementRow] = []
    for line in prd.splitlines():
        if not line.startswith("| R-"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        rows.append(RequirementRow(id=cells[0], cells=cells, raw=line))
    return tuple(rows)


def _squash(text: str) -> str:
    """去掉全部空白：PRD 的长句会折行，逐字 needle 不能依赖换行位置。"""
    return re.sub(r"\s+", "", text)


def _claim(rid: str) -> str:
    return "C-" + rid.replace("-", "")


def _row(rows: tuple[RequirementRow, ...], rid: str) -> RequirementRow | None:
    for row in rows:
        if row.id == rid:
            return row
    return None


def _status(rows: tuple[RequirementRow, ...], rid: str, expected: str, why: str) -> list[str]:
    row = _row(rows, rid)
    if row is None:
        return [f"{_claim(rid)}: 需求表缺 {rid} 行（{why}）"]
    if row.status != expected:
        return [f"{_claim(rid)}: {rid} 状态={row.status!r}，树的事实要求 {expected!r}（{why}）"]
    return []


def _needle(text: str, needle: str, claim: str, label: str) -> list[str]:
    if _squash(needle) in _squash(text):
        return []
    return [f"{claim}: PRD 未写出树的事实 {label}：期望出现 {needle!r}"]


def _citation_violations(rows: tuple[RequirementRow, ...], facts: Facts) -> list[str]:
    found: list[str] = []
    for row in rows:
        for token in _BACKTICK.findall(row.criteria):
            candidate = token.strip()
            if "/" not in candidate or not _PATH_TOKEN.fullmatch(candidate):
                continue
            if not (facts.root / candidate).exists():
                found.append(f"C-CITE: {row.id} 引用的路径不在树里: {candidate}")
    return found


def _structure_violations(prd: str) -> list[str]:
    found: list[str] = []
    found_headings = headings(prd)
    for number, topics in SECTION_TOPICS:
        title = found_headings.get(number)
        if title is None:
            found.append(f"C-STR: PRD 缺第 {number} 节（九节契约）")
            continue
        for topic in topics:
            if topic not in title:
                found.append(f"C-STR: 第 {number} 节标题={title!r} 不含主题词 {topic!r}")
    if _TABLE_HEADER not in prd:
        found.append(f"C-STR: 需求登记表列序不是 {_TABLE_HEADER}")
    return found


def _table_violations(prd: str, facts: Facts) -> list[str]:
    rows = requirement_rows(prd)
    if not rows:
        return ["C-STR: 需求登记表为空"]
    found: list[str] = []
    for row in rows:
        if len(row.cells) != 4:
            found.append(
                f"C-STR: {row.id} 有 {len(row.cells)} 列（应为 4：ID | 需求 | 状态 | 判据）"
            )
        if row.status not in STATUS_VOCAB:
            found.append(f"C-STR: {row.id} 状态={row.status!r} 不在四值词表 {STATUS_VOCAB}")
    expected = [f"R-{index:02d}" for index in range(1, len(rows) + 1)]
    if [row.id for row in rows] != expected:
        found.append(f"C-STR: 需求 ID 不是连续序列 R-01…R-{len(rows):02d}")
    found += [
        f"C-STR: 需求表缺 EC-01 点名的 {rid}" for rid in REQUIRED_CLAIMS if _row(rows, rid) is None
    ]
    return found + _citation_violations(rows, facts)


def _index_violations(index: str) -> list[str]:
    found: list[str] = []
    for needle in ("product/PRD.md", "benchmarks/RESEARCHCLAWBENCH.md"):
        found += _needle(index, needle, "C-INDEX", f"{INDEX_PATH} 的登记行")
    return found


def _legacy_violations(legacy: Mapping[str, str]) -> list[str]:
    found: list[str] = []
    for path in LEGACY_POINTERS:
        text = legacy.get(path, "")
        if not text:
            found.append(f"C-LEGACY: 读取不到 {path}")
            continue
        head = "\n".join(text.splitlines()[:15])
        if _PRD_LINK.search(head) is None:
            found.append(f"C-LEGACY: {path} 顶部没有指向 PRD.md 的链接（指针缺失）")
        sections = [line for line in text.splitlines() if line.startswith("## ")]
        if len(sections) < 3 or len(text.splitlines()) < 50:
            found.append(
                f"C-LEGACY: {path} 内容疑似被删（{len(sections)} 节 / {len(text.splitlines())} 行）"
            )
    return found


def _console_violations(prd: str, facts: Facts) -> list[str]:
    expected = (
        f"{facts.console_total} 路由 = **{facts.console_full} full / "
        f"{facts.console_partial} partial / {facts.console_gap} gap**"
    )
    return _needle(prd, expected, "C-CONSOLE", "console 覆盖（页数 / 三态计数）")


def _openapi_violations(prd: str, facts: Facts) -> list[str]:
    split = " · ".join(f"{count} {method.upper()}" for method, count in facts.openapi_methods)
    found = _needle(
        prd,
        f"{facts.openapi_paths} paths / {facts.openapi_operations} operations",
        "C-OPENAPI",
        "后端路径与操作数",
    )
    return found + _needle(prd, split, "C-OPENAPI", "后端方法分布")


def _capability_violations(prd: str, facts: Facts) -> list[str]:
    found: list[str] = []
    found += _needle(prd, f"{facts.declared_capabilities} 条声明", "C-CAPS", "能力声明数")
    found += _needle(
        prd, f"{facts.provider_capabilities} 条有 provider", "C-CAPS", "有 provider 的能力数"
    )
    found += _needle(
        prd, f"{facts.protocol_capabilities} 条被协议实际使用", "C-CAPS", "协议使用的能力数"
    )
    return found


def _phase_violations(prd: str, facts: Facts) -> list[str]:
    found: list[str] = []
    found += _needle(prd, f"{facts.phases_total} 相", "C-PHASES", "协议相数")
    found += _needle(prd, f"{facts.phases_session} 个会话相", "C-PHASES", "会话相数")
    found += _needle(
        prd, f"{facts.session_role_instances} 个角色实例", "C-PHASES", "会话相角色实例数"
    )
    found += _needle(prd, f"{facts.phases_deterministic} 个确定性相", "C-PHASES", "确定性相数")
    return found


def _r05(prd: str, facts: Facts) -> list[str]:
    complete = len(facts.submission_pieces) == len(SUBMISSION_PIECES)
    found = _status(requirement_rows(prd), "R-05", "已实现" if complete else "未实现", "投稿包五件")
    missing = [piece for piece in SUBMISSION_PIECES if piece not in facts.submission_pieces]
    if missing:
        found.append(f"{_claim('R-05')}: 汇编器里缺投稿包件 {missing}")
    return found


def _r07(prd: str, facts: Facts) -> list[str]:
    found = _status(requirement_rows(prd), "R-07", "已实现", "硬门合约")
    if not facts.review_thresholds:
        found.append(f"{_claim('R-07')}: 树里没有 REVIEW_SCORE 验收条件")
    relaxed = [
        (operator, threshold)
        for operator, threshold in zip(facts.review_operators, facts.review_thresholds, strict=True)
        if operator != "GTE" or threshold != 0.8
    ]
    if relaxed:
        found.append(f"{_claim('R-07')}: REVIEW_SCORE 不再是 GTE 0.8，读到 {relaxed}")
    return found + _needle(prd, "REVIEW_SCORE ≥ 0.8", _claim("R-07"), "硬门阈值")


def _r08(prd: str, facts: Facts) -> list[str]:
    expected = "已实现" if len(facts.retrieval_adapters) == 2 else "未实现"
    found = _status(
        requirement_rows(prd), "R-08", expected, f"检索适配器={facts.retrieval_adapters}"
    )
    return found + _needle(prd, "Europe PMC", _claim("R-08"), "Europe PMC 元数据检索")


def _r09(prd: str, facts: Facts) -> list[str]:
    expected = "未实现" if not facts.full_text_terms else "已实现"
    found = _status(requirement_rows(prd), "R-09", expected, f"正文抓取词={facts.full_text_terms}")
    if not facts.full_text_terms:
        found += _needle(prd, "无 PMC 正文", _claim("R-09"), "全文缺席的口径")
    return found


def _r10(prd: str, facts: Facts) -> list[str]:
    expected = "已实现" if facts.default_retmax > 0 and facts.max_retmax > 0 else "未实现"
    found = _status(requirement_rows(prd), "R-10", expected, "检索深度可配")
    found += _needle(prd, f"DEFAULT_RETMAX={facts.default_retmax}", _claim("R-10"), "出厂默认")
    return found + _needle(prd, f"MAX_RETMAX={facts.max_retmax}", _claim("R-10"), "上限")


def _r12(prd: str, facts: Facts) -> list[str]:
    expected = "已实现" if facts.authored_by_default else "部分"
    found = _status(requirement_rows(prd), "R-12", expected, "AUTHORED 默认关闭")
    flag = f"AUTHORED_ALLOWED_BY_DEFAULT = {facts.authored_by_default}"
    found += _needle(prd, flag, _claim("R-12"), "默认关闭常量")
    if facts.authored_profile != "authored-experiments-v1":
        found.append(f"{_claim('R-12')}: 放行 profile 名漂移为 {facts.authored_profile!r}")
    return found


def _r13(prd: str, facts: Facts) -> list[str]:
    expected = "未实现" if not facts.sandbox_science_stack else "已实现"
    found = _status(
        requirement_rows(prd), "R-13", expected, f"沙盒科学栈={facts.sandbox_science_stack}"
    )
    if not facts.sandbox_science_stack:
        found += _needle(prd, "无 numpy", _claim("R-13"), "科学栈缺席的口径")
    return found + _needle(prd, facts.sandbox_base, _claim("R-13"), "沙盒基础镜像")


def _r14(prd: str, facts: Facts) -> list[str]:
    expected = "未实现" if facts.code_hypothesis_files == 0 else "已实现"
    found = _status(
        requirement_rows(prd),
        "R-14",
        expected,
        f"HypothesisSet 代码文件={facts.code_hypothesis_files}",
    )
    return found + _needle(prd, "HypothesisSet", _claim("R-14"), "假设发散的域概念")


def _r15(prd: str, facts: Facts) -> list[str]:
    expected = "未实现" if facts.openapi_submission_hits == 0 else "已实现"
    found = _status(
        requirement_rows(prd),
        "R-15",
        expected,
        f"openapi 内 submission 命中={facts.openapi_submission_hits}",
    )
    if facts.openapi_submission_hits == 0:
        found += _needle(prd, "零命中", _claim("R-15"), "投稿端点缺席的口径")
    return found


def _r16(prd: str, facts: Facts) -> list[str]:
    found = _status(requirement_rows(prd), "R-16", "不宣称", "身份 / 多租户")
    if not facts.principal_mentions_m18:
        found.append(f"{_claim('R-16')}: principal.py 不再声明 M18 DEFERRED")
    return found + _needle(prd, "M18 DEFERRED", _claim("R-16"), "M18 延期口径")


def _r19(prd: str, facts: Facts) -> list[str]:
    found = _status(requirement_rows(prd), "R-19", "不宣称", "NOT_JUDGED 五项")
    if len(facts.not_judged) != 5:
        found.append(f"{_claim('R-19')}: NOT_JUDGED 是 {len(facts.not_judged)} 项（应为 5）")
    joined = " ".join(facts.not_judged).lower()
    missing = [theme for theme in NOT_JUDGED_THEMES if theme not in joined]
    if missing:
        found.append(f"{_claim('R-19')}: NOT_JUDGED 缺主题 {missing}")
    return found + _needle(prd, "NOT_JUDGED", _claim("R-19"), "未判五项的出处")


def _r20(prd: str, facts: Facts) -> list[str]:
    expected = "未实现" if facts.models_vision_keys == 0 else "已实现"
    found = _status(
        requirement_rows(prd), "R-20", expected, f"VISION 声明={facts.models_vision_keys}"
    )
    if facts.models_vision_keys == 0:
        found += _needle(prd, "无视觉", _claim("R-20"), "视觉缺席的口径")
    return found + _needle(prd, "VISION", _claim("R-20"), "视觉能力词")


_CLAIM_CHECKS = (_r05, _r07, _r08, _r09, _r10, _r12, _r13, _r14, _r15, _r16, _r19, _r20)


def violations(prd: str, index: str, legacy: Mapping[str, str], facts: Facts) -> list[str]:
    """PRD 的说法 vs 树的事实：返回全部违反（每条以条号开头）。"""
    found: list[str] = []
    found += _structure_violations(prd)
    found += _table_violations(prd, facts)
    found += _index_violations(index)
    found += _legacy_violations(legacy)
    found += _console_violations(prd, facts)
    found += _openapi_violations(prd, facts)
    found += _capability_violations(prd, facts)
    found += _phase_violations(prd, facts)
    for check in _CLAIM_CHECKS:
        found += check(prd, facts)
    return found


def documents(root: Path) -> tuple[str, str, dict[str, str]]:
    """读判词需要的三份文档（PRD / INDEX / 两份历史档案）。"""
    prd = (root / "docs/product/PRD.md").read_text(encoding="utf-8")
    index = (root / Path(INDEX_PATH)).read_text(encoding="utf-8")
    legacy = {path: (root / path).read_text(encoding="utf-8") for path in LEGACY_POINTERS}
    return prd, index, legacy
