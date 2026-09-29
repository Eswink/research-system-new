"""GOAL-026 EC-04（AC-4）：**明确否认** exactly-once 的机械判据。

口径（AGENTS.md §7）：投递语义只能是 **at-least-once + idempotency + deduplication**；
「假装实现 exactly once」被明文禁止。本判据把这个口径**机械化**，分两件事：

1. **ASCII lemma**（`exactly[ _-]once`，大小写不敏感）在**有界且显式声明**的面上
   **逐条分类**：`DENIAL`（禁止/否认语境）/ `EXEMPT`（登记豁免，理由非空）/
   `AFFIRMATIVE`（肯定式投递语义声明）⇒ **出现 `AFFIRMATIVE` 即判红**。
   受判面（扫描文件数 + 分类条数）都有**下界**断言 ⇒ 不是空真；
   豁免表有**上限**且必须**全部被用到**（不许留不生效的豁免位当暗余量）。
   否定词判定窗 = 本行 + **上一行**（Markdown 软换行会把「不假装」留在上一行，
   窗口**有界**：1 行）。
2. **CJK lemma**（「恰好一次」）在**产品 + 文档**面上必须**零命中** —— 因为在本仓里
   这个中文短语表达的是另一件事（「同源句恰好一次」= 某句在某文档里的出现次数），
   属**计数**语义而非投递语义。为了让「零命中」不是「检测器坏了」，同一判据要求
   检测器在**它确实出现的地方**（`.cursor/` 计划与记忆、`tests/`）找到**足够多**的命中
   （下界 `_MIN_CJK_CONTROL`）⇒ 正控制与零断言同时成立（承 MEM-156）。

**本文件自身豁免**（与 `test_reproducibility_wording.py` 同一手法，豁免写在明处）：
它含刻意构造的正例/反例串，是**夹具**而不是宣称。
"""

from __future__ import annotations

import os
import re

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

_ASCII_LEMMA = re.compile(r"exactly[ _-]once", re.IGNORECASE)
_CJK_LEMMA = "恰好一次"

#: 受判面（ASCII lemma）：口径会出现在代码 / 文档 / 记录 / 判据里。
#: **规则文本面**（`.cursor/plans/goals/**`）单列：那些文件**就是**禁令本身
#: （禁止面 / escalation 清单的逐条重述），把规则文本的每一行当「投递语义宣称」来分类是
#: 范畴错误；它由 `test_the_rule_face_states_the_ban_it_quotes` 另判（见该用例的说明）。
_ASCII_ROOTS: tuple[str, ...] = (
    "AGENTS.md",
    "docs",
    "packages",
    "adapters",
    "services",
    "apps/web/src",
    "tests",
    ".cursor/plans/tasks",
    ".cursor/plans/rechecks",
    ".cursor/memory",
)
#: 规则文本面 + 排除理由（非空）—— 排除必须写在明处，不能是 `_SKIP_DIRS` 里的静默跳过。
_RULE_FACE_ROOTS: tuple[str, ...] = (".cursor/plans/goals",)
_RULE_FACE_REASON = (
    "GOAL 记录是**禁令文本本身**（`fix_policy.forbidden` / `escalation_triggers` 的逐条重述），"
    "不是关于系统的投递语义宣称；对该面做逐行分类属范畴错误，故单列并由另一条判据处理"
)
_MIN_RULE_FACE_FILES = 20
_RULE_FACE_DENIAL_TOKENS: tuple[str, ...] = ("禁止", "不得", "否认", "不做", "BLOCKED", "口径")
#: CJK lemma 的**零命中**面：投递语义的宣称面是产品与文档。
_CJK_ZERO_ROOTS: tuple[str, ...] = (
    "AGENTS.md",
    "docs",
    "packages",
    "adapters",
    "services",
    "apps/web/src",
)
#: CJK lemma 的**正控制**面：检测器必须在这里找得到它（证明搜索没坏）。
_CJK_CONTROL_ROOTS: tuple[str, ...] = (".cursor/plans", ".cursor/memory", "tests")

_SUFFIXES = (".py", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml")
_SKIP_DIRS = {"node_modules", "__pycache__", ".venv", "dist", ".git", "scratch"}

_NEGATION_MARKERS: tuple[str, ...] = (
    "禁止",
    "不得",
    "不假装",
    "不宣称",
    "否认",
    "不做",
    "不实现",
    "不是",
    "不能",
    "不为",
    "不静默",
    "而非",
    "绝不",
    "never",
    "not ",
    "forbidden",
    "cannot",
    "must not",
    "blocked",
    "prohibit",
)

#: 登记豁免：`(仓库相对路径, 去空白后的整行)` → 理由（非空、≥ `_MIN_REASON` 字符）。
#: 键含**整行内容** ⇒ 行一旦被编辑，豁免即失效并逼一次重新分类。
_EXEMPT: dict[tuple[str, str], str] = {
    (
        "services/api/worker_gateway/auth.py",
        '"""256-bit URL-safe session token (returned to the worker exactly once)."""',
    ): (
        "会话 token 的**响应形状**声明（明文只在创建时返回一次），不是事件投递语义；"
        "auth 面不在本 GOAL 覆盖范围，仍按残余登记（不因此承认它是已证事实）"
    ),
    (
        "tests/application/run_orchestration/test_execute_task_accounting.py",
        "def test_each_attempt_is_recorded_exactly_once() -> None:",
    ): "用例名描述**记录行数**唯一（计数语义，行级去重），不是投递保证；该用例自身断言行数",
    (
        "tests/architecture/python/test_live_switch_is_single_source.py",
        "def test_the_literal_is_assigned_exactly_once_in_product_code(self) -> None:",
    ): "用例名描述某个字面量在**产品代码里只被赋值一次**（计数语义），与投递无关",
    (
        "tests/architecture/python/test_live_switch_is_single_source.py",
        'f"the switch name must be declared exactly once, in the product layer: {declaring}"',
    ): "同上：断言字面量声明次数为 1（计数语义）",
    (
        "tests/postgres/test_claim_concurrency_pg.py",
        "assert len(all_claimed) == total  # every task claimed exactly once",
    ): (
        "并发认领的**唯一性**断言（每个任务只被认领一次 = 去重性质），"
        "断言对象是行集合相等，不是事件投递的 exactly-once 保证"
    ),
    (
        ".cursor/plans/rechecks/RECHECK-20260925-183-live-switch-and-observability-job-isolation.md",
        "`test_the_literal_is_assigned_exactly_once_in_product_code`）。",
    ): "复检记录里**引用另一个用例的名字**（计数语义：字面量只被赋值一次），不是投递宣称",
}

_MAX_EXEMPT = 8
_MIN_REASON = 20
_MIN_SCANNED_FILES = 2500
_MIN_CLASSIFIED = 16
_MIN_CJK_CONTROL = 8
#: 否定词窗的**有界**长度（± 各最多这么多行，且两侧按段落截断，见 `_classify`）。
_WINDOW_LINES = 6

#: 口径串必须出现在可靠性文档里（「at-least-once + idempotency + deduplication」的落点）。
#: 逐文档要求**实测**出来的那些串（ADR-0016 正文没有 `at-least-once` 的字面——只在文件名里）。
_CALIBRE_DOCS: dict[str, tuple[str, ...]] = {
    "docs/adr/ADR-0016-at-least-once-idempotency-outbox.md": ("idempotency", "outbox"),
    "docs/architecture/WORKFLOW_RELIABILITY.md": ("at-least-once", "idempotency", "outbox"),
}

#: 否认词表的**正控制**：这两行必须被判成 `DENIAL`（否则分类器只会一律说不清）。
_DENIAL_CONTROL: tuple[tuple[str, int], ...] = (
    ("AGENTS.md", 175),
    ("docs/adr/ADR-0016-at-least-once-idempotency-outbox.md", 5),
)


def _scan_files(roots: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for root in roots:
        target = os.path.join(REPO_ROOT, root)
        if os.path.isfile(target):
            found.append(target)
            continue
        for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in _SKIP_DIRS]
            for name in sorted(filenames):
                if name.endswith(_SUFFIXES):
                    found.append(os.path.join(dirpath, name))
    return found


def _relative(path: str) -> str:
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")


def _self_path() -> str:
    return os.path.abspath(__file__)


def _lemmatic_lines(lines: list[str]) -> list[tuple[int, str]]:
    return [
        (lineno, line) for lineno, line in enumerate(lines, start=1) if _ASCII_LEMMA.search(line)
    ]


def _classify(path: str, lines: list[str], lineno: int) -> str:
    """分类一条出现：豁免表 → 否定词窗 → 肯定式。

    窗口 = 本行 **±**最多 `_WINDOW_LINES` 行，**两侧都按段落截断**（遇空行即止），
    因此**有界**：记录 / 文档的软换行会把「明确不做」「立即 BLOCKED」「明文禁止」
    留在上一行或**下一行**（一条 bullet 就是一段）。窗口不截断就等于「全文搜索」，
    那会把判据变成空真。
    """
    line = lines[lineno - 1]
    if (path, line.strip()) in _EXEMPT:
        return "EXEMPT"
    window = [line]
    index = lineno - 2
    while index >= 0 and len(window) <= _WINDOW_LINES and lines[index].strip():
        window.append(lines[index])
        index -= 1
    index = lineno
    while index < len(lines) and len(window) <= _WINDOW_LINES and lines[index].strip():
        window.append(lines[index])
        index += 1
    text = "\n".join(window)
    if any(marker in text for marker in _NEGATION_MARKERS):
        return "DENIAL"
    return "AFFIRMATIVE"


def _classified_occurrences() -> list[tuple[str, int, str, str]]:
    rows: list[tuple[str, int, str, str]] = []
    for path in _scan_files(_ASCII_ROOTS):
        if os.path.abspath(path) == _self_path():
            continue
        with open(path, encoding="utf-8", errors="ignore") as handle:
            lines = handle.read().splitlines()
        relative = _relative(path)
        for lineno, line in _lemmatic_lines(lines):
            rows.append((relative, lineno, line.strip(), _classify(relative, lines, lineno)))
    return rows


def _cjk_hits(roots: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for path in _scan_files(roots):
        if os.path.abspath(path) == _self_path():
            continue
        with open(path, encoding="utf-8", errors="ignore") as handle:
            if _CJK_LEMMA in handle.read():
                hits.append(_relative(path))
    return hits


def test_no_affirmative_exactly_once_claim_in_the_declared_face() -> None:
    """**否认判据**：受判面上不得出现肯定式的 exactly-once 投递声明。"""
    scanned = len(_scan_files(_ASCII_ROOTS))
    rows = _classified_occurrences()
    affirmative = [row for row in rows if row[3] == "AFFIRMATIVE"]

    assert scanned >= _MIN_SCANNED_FILES, f"扫描面过低（{scanned}）⇒ 受判面不成立"
    assert len(rows) >= _MIN_CLASSIFIED, f"分类条数过低（{len(rows)}）⇒ 受判面不成立"
    assert not affirmative, f"出现肯定式 exactly-once 声明：{affirmative}"


def test_the_denial_vocabulary_is_actually_in_use() -> None:
    """正控制：已知的否认/禁止行必须被判成 `DENIAL`（否则词表只是摆设）。"""
    by_key = {(row[0], row[1]): row[3] for row in _classified_occurrences()}
    for path, lineno in _DENIAL_CONTROL:
        assert by_key.get((path, lineno)) == "DENIAL", f"{path}:{lineno} 必须判成 DENIAL"


def test_exemptions_are_bounded_and_all_used() -> None:
    """豁免表**有上限**、**理由非空**、且**不许留不生效的条目**（暗余量）。"""
    rows = _classified_occurrences()
    used_keys = {(row[0], row[2]) for row in rows if row[3] == "EXEMPT"}

    assert len(_EXEMPT) <= _MAX_EXEMPT, f"豁免条目过多（{len(_EXEMPT)} > {_MAX_EXEMPT}）"
    for (path, line), reason in _EXEMPT.items():
        assert len(reason) >= _MIN_REASON, f"豁免理由过短：{path} / {line}"
    unused = set(_EXEMPT) - used_keys
    assert not unused, f"豁免表里有不生效的条目（暗余量）：{unused}"
    assert used_keys, "豁免表必须至少命中一条（否则它证明不了受判面被真的走查过）"


def test_the_cjk_lemma_never_appears_in_product_or_docs() -> None:
    """CJK lemma 在产品 + 文档面**零命中**；检测器在别处**找得到**（正控制）。"""
    zero_hits = _cjk_hits(_CJK_ZERO_ROOTS)
    control_hits = _cjk_hits(_CJK_CONTROL_ROOTS)

    assert control_hits, "正控制失败：检测器在控制面上找不到该短语 ⇒ 零命中不可信"
    assert len(control_hits) >= _MIN_CJK_CONTROL, (
        f"正控制面命中过少（{len(control_hits)} < {_MIN_CJK_CONTROL}）"
    )
    assert zero_hits == [], f"产品 / 文档面不得出现该短语（实测：{zero_hits}）"


def test_the_rule_face_states_the_ban_it_quotes() -> None:
    """规则文本面：**引用该词的 GOAL 必须同时写出禁令**（排除不是静默跳过）。

    本判据与上面那条是**互补**的两条事实：受判面（产品 / 文档 / 判据 / 非 GOAL 记录）
    必须零肯定式；规则文本面（`.cursor/plans/goals/**`）不做逐行分类，但**凡是引用了
    这个词的 GOAL 文件**，里面必须出现禁令词表里的词 —— 即「可以谈它，但必须是在谈禁令」。
    受判文件数有**下界**（`_MIN_RULE_FACE_FILES`）⇒ 排除面本身也被走查过。
    """
    quoting: list[str] = []
    scanned: list[str] = []
    for path in _scan_files(_RULE_FACE_ROOTS):
        if os.path.abspath(path) == _self_path():
            continue
        scanned.append(_relative(path))
        with open(path, encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
        if not _ASCII_LEMMA.search(text):
            continue
        quoting.append(_relative(path))
        missing = [token for token in _RULE_FACE_DENIAL_TOKENS if token not in text]
        assert not missing, f"{_relative(path)} 引用了 exactly-once 却没有禁令词：{missing}"

    assert len(scanned) >= _MIN_RULE_FACE_FILES, f"规则文本面过低（{len(scanned)}）"
    assert quoting, f"规则文本面必须至少有一个引用（否则排除面证明不了任何事）：{_RULE_FACE_REASON}"


def test_the_calibre_tokens_are_present_in_the_reliability_docs() -> None:
    """口径串在位：可靠性文档里写着 `at-least-once` / `idempotency` / `outbox`。"""
    missing: list[str] = []
    for doc, tokens in _CALIBRE_DOCS.items():
        with open(os.path.join(REPO_ROOT, doc), encoding="utf-8") as handle:
            text = handle.read()
        for token in tokens:
            if token not in text:
                missing.append(f"{doc} 缺 {token}")
    assert not missing, missing
