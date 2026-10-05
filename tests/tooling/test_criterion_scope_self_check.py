"""GOAL-20261005-030 EC-04 判据：**判据射程的自查**（承 GOAL-029 的教训）。

**为什么需要它**：GOAL-029 的 EC-02 主判据曾把受判面写成 `declared ∩ implemented` ——
那让「**声明了但没实现**」在**构造上不可能被报出来**（交集天然排除缺实现者），于是判据
全绿而缺口在场。GOAL-029 是在**完成核验**时才抓到的。本文件把这件事**提前**做成机械事实：
对**本轮新增的判据**检查它们的受判面是不是**被收窄**了。

**三件事**：

1. **观察器**（`scan_judge_faces`）：对判据文件做 **AST 扫描**，抽出每条 `assert`，
   检查它（以及它**引用**的那些赋值）里是否含掩蔽形态：
   - `intersection_as_expectation`：断言里出现交集（`&`）—— 求交会把「应有而未有」排除掉；
   - `intersection_narrowed_universe`：**遍历面**被交集收窄（`for x in declared & implemented`）
     —— 这是 GOAL-029 EC-02 的**原形**；
   - `difference_narrowed_universe`：**遍历面**被差集收窄（`for x in a - b`）。
   **关键区分**：`missing = set(expected) - set(actual)` 后 `assert missing == []` 是
   **诚实的缺口计算**（遍历面完整），**不得**判红 —— 观察器初版实测把这类正确写法误报过。
2. **射程自查表**（`SCOPE_TABLE`）：本轮新增的**每条判据**逐条登记 —— 受判面定义 /
   是否有掩蔽 / 按压形态 / 实测结果。**未登记者判红**（与 GOAL-029 的「射程逐条分类」同形）。
3. **反证（本判据自己的可判红用例）**：把 GOAL-029 的**原形**喂给观察器 ⇒ 必须报出；
   把**诚实的缺口计算**喂进去 ⇒ 必须报空；把本轮**真实的判据**喂进去 ⇒ 必须报空。

**如实边界**（本文件不声称已解决）：

- 观察器是**形态检测**（AST 层），不是语义证明：它抓的是「受判集合被集合运算收窄」这类
  **结构特征**。**语义级**的射程仍要靠**按压**取证（本 GOAL 的 EC-01…EC-03 各自做了按压，
  见 `RECHECK-20261005-284/286/288`）。
- 射程面（`JUDGES`）是**逐条写死**的清单：只覆盖**本轮新增**的判据；既有判据不在其内。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

#: 本轮新增的判据（**逐条写死**；未登记者由 `test_the_scope_table_covers_every_judge...` 判红）。
JUDGES: tuple[str, ...] = (
    "tests/e2e/test_capabilities_really_used_in_a_run.py",  # EC-01
    "tests/adapters/canonical/test_run_read_onboarding.py",  # EC-02
    "tests/e2e/test_scientific_action_depth.py",  # EC-03
)

#: 掩蔽形态 → 说明（判词里逐条点名）。
_MASKING_FORMS: dict[str, str] = {
    "intersection_as_expectation": (
        "断言里出现交集（`&`）：求交会把「应有而未有」排除掉 ⇒ 缺口在构造上发不出声"
    ),
    "intersection_narrowed_universe": (
        "**遍历面**被交集收窄（`for x in declared & implemented`）：这是 GOAL-029 EC-02 的"
        "**原始缺陷形态** —— 遍历范围内的每一项都必然有实现，缺口永不被报出"
    ),
    "difference_narrowed_universe": (
        "**遍历面**被差集收窄（`for x in a - b`）：被排除的那一类永不发声"
    ),
}


@dataclass(frozen=True, slots=True)
class Finding:
    """一处疑似掩蔽形态（文件 + 行 + 形态 + 报错原文）。"""

    path: str
    lineno: int
    form: str
    detail: str


def _binops(node: ast.AST) -> list[str]:
    """收集表达式里出现的集合运算符（`&` / `|` / `-`，**任意深度**，含推导式内部）。"""
    found: list[str] = []
    for item in ast.walk(node):
        if isinstance(item, ast.BinOp):
            if isinstance(item.op, ast.BitAnd):
                found.append("&")
            elif isinstance(item.op, ast.BitOr):
                found.append("|")
            elif isinstance(item.op, ast.Sub):
                found.append("-")
    return found


def _narrowed_universes(tree: ast.AST) -> list[str]:
    """找出**被集合运算收窄的遍历面**（`for x in A & B` / `for x in A - B`）。

    **这是本判据的核心定义**：掩蔽的形态不是「集合运算出现在断言里」，而是
    **受判的那个集合本身被收窄了** —— `for capability in declared & implemented:`
    里，遍历面天然排除「声明了但没实现」的那些 ⇒ 缺口在**构造上**不可能被报出
    （GOAL-029 EC-02 的原形）。

    与之相对，`missing = set(expected) - set(actual)` 然后 `assert missing == []` 是
    **诚实的缺口计算**（遍历面是完整的 `expected`），**不得**被判红 —— 否则判据会
    把正确写法一起打掉（本观察器初版实测就犯了这个错）。
    """
    hits: list[str] = []
    for node in ast.walk(tree):
        iterables: list[ast.AST] = []
        if isinstance(node, ast.comprehension):
            iterables.append(node.iter)
        if isinstance(node, ast.For):
            iterables.append(node.iter)
        for iterable in iterables:
            ops = _binops(iterable)
            if "&" in ops:
                hits.append("intersection_narrowed_universe")
            if "-" in ops:
                hits.append("difference_narrowed_universe")
    return sorted(set(hits))


def _masking_forms(node: ast.AST) -> list[str]:
    """判断一个表达式是否含掩蔽形态（返回命中的形态名）。

    两条：① 交集出现在表达式里（`&`）—— 判据里几乎不存在正当用途；② 遍历面被收窄。
    """
    hits: list[str] = []
    if "&" in _binops(node):
        hits.append("intersection_as_expectation")
    hits.extend(_narrowed_universes(node))
    return sorted(set(hits))


def _assertion_nodes(tree: ast.AST) -> list[ast.Assert]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]


def _compare_target(node: ast.AST) -> ast.AST:
    """从 `assert` 取出被断言的表达式（`assert not X` ⇒ `X`；`assert X` ⇒ `X`）。"""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return node.operand
    return node


def _assigned_set_ops(tree: ast.AST) -> dict[str, list[ast.AST]]:
    """本文件里「被赋值为含集合运算的表达式」的名字 → **全部**这类表达式（单层数据流）。

    **为什么需要**：真实的掩蔽形态**很少把集合运算写在 `assert` 里** —— 典型写法是
    `missing = [x for x in declared & implemented if …]` 然后 `assert missing == []`。
    只看断言表达式会**漏掉**它（本判据初版实测就漏了），因此要把赋值面也纳入扫描。

    **为什么值是列表而不是单个表达式**（本判据自己的第二个掩蔽缺陷，实测抓到并修）：
    同一名字在文件里可能被赋值**多次**（不同用例各写各的 `missing`），而**只有最后一次**
    会被提交时的单值 dict 保留 —— 于是被按压成掩蔽形态的那一次**被后来的诚实写法覆盖**，
    扫描器报空（**这正是 `MEM-20260922-160` 的形态，出现在自查器自己身上**）。
    取全部赋值后，任一形态命中即报出。
    """
    result: dict[str, list[ast.AST]] = {}
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        value: ast.AST | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        if value is None or not _binops(value):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                result.setdefault(target.id, []).append(value)
    return result


def scan_judge_faces(path: Path) -> list[Finding]:
    """AST 扫描一个判据文件，返回全部疑似掩蔽形态（只读）。

    两遍：① 收集「被赋值为含集合运算的表达式」的名字；② 对每条断言，检查它**直接**含的
    集合运算，以及它**引用**的那些名字背后的表达式。**引用面是关键** —— 掩蔽通常藏在赋值里。
    """
    source = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(path))
    assigned = _assigned_set_ops(tree)
    findings: list[Finding] = []
    for node in _assertion_nodes(tree):
        test = _compare_target(node.test)
        hits = list(_masking_forms(test))
        for name_node in [item for item in ast.walk(test) if isinstance(item, ast.Name)]:
            for definition in assigned.get(name_node.id, []):
                hits.extend(_masking_forms(definition))
        for form in sorted(set(hits)):
            findings.append(
                Finding(
                    path=str(path),
                    lineno=node.lineno,
                    form=form,
                    detail=_MASKING_FORMS[form],
                )
            )
    return findings


@dataclass(frozen=True, slots=True)
class ScopeRow:
    """射程自查表的一行（EC-04(b) 的四要素）。"""

    #: 受判面定义：这条判据**对什么**下断言（含受判集合的**构成方式**）。
    face: str
    #: 是否可能掩蔽：观察器的形态结论 + 人读的理由。
    masking: str
    #: 按压形态：怎么按的、按了之后哪条红。
    press: str
    #: 实测结果：`判红`（按压确实红）或 `全绿`（无掩蔽且未按压）。
    result: str
    #: 断言条数下界（受判面非空的机械证据；见 `test_every_judge_declares_a_non_empty_face`）。
    min_assertions: int


#: **射程自查表**（EC-04(b)）。每一条都回答：受判面定义 / 是否可能掩蔽 / 按压形态 / 实测结果。
SCOPE_TABLE: dict[str, ScopeRow] = {
    "tests/e2e/test_capabilities_really_used_in_a_run.py": ScopeRow(
        face=(
            "三条已放行承接读能力**逐条**的调用证据（`_tool_evidence(reads, phase=…)` 按 "
            "**phase 分索引**，不合并）+ 下游 `evidence.read` 的**返回内容**（按制品 id 的 "
            "task 段区分上/下游）+ 反证臂的 run 终态与判词。受判面 = **三条 × 两个 phase**，"
            "由 `_CAPABILITIES` 与 `_TOOL_IDS` 逐条写死。"
        ),
        masking=(
            "**初版有掩蔽（实测抓到并已修）**：`_tool_evidence` 用**单键索引** ⇒ 两个 phase 调"
            "同名工具时**后写覆盖前写**，上游产出与下游产出在看的人眼里变成同一条 ⇒ "
            "「下游是否消费了上游」被这个覆盖掩蔽（`MEM-20260922-160` 的形态）。"
            "**修法**：`_phase_of_task` + 按 phase 分索引。**现形态无掩蔽**（观察器报空）。"
        ),
        press=(
            "① 撤回 evidence id 的 `task_id` 修复 ⇒ **2 failed**（判词逐字复现 "
            "`conflicting evidence registration`）；② 协议改回会话语义 ⇒ **4 failed**"
            "（含判据自检那条，点名「声明面变了」）。两处均 `sha256` 逐字节复原。"
        ),
        result="判红",
        min_assertions=25,
    ),
    "tests/adapters/canonical/test_run_read_onboarding.py": ScopeRow(
        face=(
            "`run.read` 的四件事：出厂目录**声明** + `list_tools` **承载**（专属 tool id）+ "
            "出厂绑定表**有条目**（三者**分别断言**）+ `RunStore` 返回值**逐字段**比对 + "
            "三种缺失形态各自点名 + 「目录声明」与「策略 DENY」在**同一用例内**同时断言。"
        ),
        masking=(
            "**无掩蔽（观察器报空）**。四处易犯的形态都避开了：① 三者是**分别断言**的，"
            "不是先求交再比；② 未冻结用 `is None` 单点判定（不构造差集）；"
            "③ 「承接≠放行」写成两条**并存**断言；④ 反证面用**合成输入**（空 `_FakeRunStore`）。"
        ),
        press=(
            "撤回 `_TOOL_CAPABILITIES` 的 `run_read` 条目 ⇒ **3 failed**：实现面不复存在 / "
            "`('声明了承接但既没有实现、也没有登记理由', ['run.read'])` / "
            "`('射程内清单里有不具备实现能力的条目', ['run.read'])`。复原 `sha256sum -c` 全 `OK`。"
        ),
        result="判红",
        min_assertions=20,
    ),
    "tests/e2e/test_scientific_action_depth.py": ScopeRow(
        face=(
            "真科研动作（容器 `image_digest` + 六个科学指标**逐字段**）+ 三读面"
            "（artifacts / experiments / evidence）+ 下游消费（`verdict` 的 `evidence.read` "
            "返回内容含实验证据 id）+ 反证（抬高阈值 ⇒ run `FAILED` + 判词含指标/算子/阈值）+ "
            "**出厂目录里那条判据本身**（在场 / 指标名 / 算子 / 阈值逐字）+ 实验**实测值**越阈值。"
        ),
        masking=(
            "**初版有掩蔽（实测抓到并已补齐）**：反证臂只改**运行时快照**"
            "（`preflight_override`）⇒ 它证明「阈值被判了」，但**目录里那个数值本身**若被改小"
            "（实测 100 → 1）判据**全绿** ⇒ 「本协议对科学结论下了可否证的判据」这句话"
            "**没有受判**。**修法**：`TestTheFalsifiableCriterionIsPinnedInTheCatalog`。"
            "**现形态无掩蔽**（观察器报空）。"
        ),
        press=(
            "① 抬高阈值（运行时快照 `1e6`）⇒ 实验 phase 判拒并点名（主反证）；"
            "② 改小**出厂目录**阈值 100 → 1 ⇒ 补齐前**未抓到**、补齐后**判红**"
            "（`阈值必须是写死的那个数`）；③ 直接跑脚本取 metrics ⇒ 非空真（阈值可达）。"
        ),
        result="判红",
        min_assertions=25,
    ),
}


def test_the_scope_table_covers_every_judge_this_goal_added() -> None:
    """射程逐条分类：本轮新增的**每条判据**都在表里（未登记者判红）。"""
    assert JUDGES, "受判面非空（本判据不得在空集上恒真）"
    missing = [name for name in JUDGES if name not in SCOPE_TABLE]
    assert missing == [], ("有新判据没进射程自查表（每条都要逐条登记）", missing)
    ghosts = [name for name in SCOPE_TABLE if name not in JUDGES]
    assert ghosts == [], ("自查表里有不在本轮判据清单里的条目（幽灵条目）", ghosts)


def test_the_real_judges_carry_no_masking_form() -> None:
    """**主判据**：本轮三条判据的断言里**没有**掩蔽形态。

    受判面 = 三个文件的**全部断言**（逐文件、逐条扫），不是抽样。
    """
    assert JUDGES, "受判面非空"
    findings: list[Finding] = []
    for relative in JUDGES:
        path = _ROOT / relative
        assert path.is_file(), f"判据文件不存在：{relative}"
        findings.extend(scan_judge_faces(path))
    assert findings == [], (
        "本轮判据出现掩蔽形态（受判面被交集/差集收窄 ⇒ 最该被抓的形态发不出声）",
        [(item.path, item.lineno, item.form) for item in findings],
    )


def test_the_scope_table_records_press_evidence() -> None:
    """自查表逐条：受判面定义非空 + 按压形态非空 + 实测结果非空（不是空壳表）。"""
    for relative, row in SCOPE_TABLE.items():
        assert row.face.strip(), f"{relative} 没写受判面定义"
        assert row.press.strip(), f"{relative} 没写按压形态"
        assert row.result.strip(), f"{relative} 没写实测结果"
        assert row.result in {"判红", "全绿"}, (relative, row.result)


def test_every_judge_declares_a_non_empty_face() -> None:
    """受判面**非空**的机械证据：每条判据文件里 `assert` 的条数有下界。

    为什么单列：一个「受判面非空」的口头承诺挡不住有人把判据改成一个空转文件。
    这里给下界（写死在表里），条数不足即判红（承 `MEM-20260922-156`）。
    """
    for relative, row in SCOPE_TABLE.items():
        path = _ROOT / relative
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        count = len(_assertion_nodes(tree))
        assert count >= row.min_assertions, (
            f"{relative} 的断言条数低于下界（受判面疑似被削）",
            count,
            row.min_assertions,
        )


class TestTheScannerBitesOnAMaskingForm:
    """**反证（本判据自己的可判红用例）**：观察器必须抓得住掩蔽形态。

    掩蔽的**定义**（见 `_MASKING_FORMS`）：受判的那个集合本身被**收窄**了，或断言里
    出现交集。两种形态各有合成用例；**外加**一条反向自检 —— 诚实的缺口计算
    （`set(expected) - set(actual)` 后比空）**不得**被判红（观察器初版实测会误报它）。
    """

    def _scan_source(self, tmp_path: Path, source: str) -> list[Finding]:
        path = tmp_path / "synthetic_judge.py"
        path.write_text(source, encoding="utf-8")
        return scan_judge_faces(path)

    def test_the_goal029_defect_shape_is_reported_verbatim(self, tmp_path: Path) -> None:
        """**最忠实的形态**：GOAL-029 首版把受判面写成 `declared & implemented` 后**遍历它**。

        `for capability in declared & implemented:` —— 交集天然排除「声明了但没实现」的那些
        ⇒ 遍历范围内的每一项都必然有实现 ⇒ **缺口在构造上不可能被报出**。
        """
        findings = self._scan_source(
            tmp_path,
            "def test_x() -> None:\n"
            "    declared = {'a', 'b'}\n"
            "    implemented = {'a'}\n"
            "    missing = [name for name in declared & implemented if name not in implemented]\n"
            "    assert missing == []\n",
        )
        assert [item.form for item in findings] == [
            "intersection_as_expectation",
            "intersection_narrowed_universe",
        ], findings

    def test_a_difference_narrowed_universe_is_reported(self, tmp_path: Path) -> None:
        """**遍历面**被差集收窄：`for x in expected - allowed` ⇒ 被排除的那一类永不发声。"""
        findings = self._scan_source(
            tmp_path,
            "def test_y() -> None:\n"
            "    expected = {'a', 'b', 'c'}\n"
            "    allowed = {'a'}\n"
            "    missing = [name for name in expected - allowed if name not in allowed]\n"
            "    assert missing == []\n",
        )
        assert [item.form for item in findings] == ["difference_narrowed_universe"], findings

    def test_honest_gap_computation_is_not_reported(self, tmp_path: Path) -> None:
        """**反向自检**：`set(expected) - set(actual)` 是**诚实的缺口计算**，不得判红。

        遍历面是**完整的** `expected` ⇒ 「应有而未有」照样被报出。观察器初版把这类
        正确写法一起打掉（实测：EC-01 判据的 `sorted(set(upstream) - consumed)` 被误报）
        ⇒ 这条把「不许把正确写法判红」钉住。
        """
        findings = self._scan_source(
            tmp_path,
            "def test_ok() -> None:\n"
            "    expected = {'a', 'b'}\n"
            "    actual = {'a'}\n"
            "    missing = sorted(set(expected) - set(actual))\n"
            "    assert missing == []\n",
        )
        assert findings == [], findings

    def test_a_clean_judge_is_reported_clean(self, tmp_path: Path) -> None:
        """干净判据必须报空 —— 否则观察器只会把所有东西都判红（恒真告警器）。"""
        findings = self._scan_source(
            tmp_path,
            "def test_ok() -> None:\n"
            "    expected = {'a', 'b'}\n"
            "    actual = {'a', 'b'}\n"
            "    assert actual == expected\n"
            "    assert expected <= actual\n",
        )
        assert findings == [], findings

    def test_the_assignment_index_keeps_every_definition(self, tmp_path: Path) -> None:
        """**本判据自己的第二个掩蔽缺陷（实测抓到并已修）**：赋值索引**不得**后写覆盖前写。

        实测形态：`_assigned_set_ops` 初版用**单值 dict**，于是同一名字在文件里被赋值多次时
        （不同用例各写各的 `missing`），**只有最后一次**被保留 ⇒ 被按压成掩蔽形态的那一次
        **被后来的诚实写法覆盖**，扫描器报空。**这正是 `MEM-20260922-160` 的形态，出现在
        自查器自己身上** —— 所以这里用「同名两次赋值、前一次是掩蔽形态」把它钉住。
        """
        source = (
            "def test_a() -> None:\n"
            "    bases = {'x'}\n"
            "    picks = {c for c in bases if c}\n"
            "    missing = [c for c in bases & picks if c not in picks]\n"
            "    assert missing == []\n"
            "\n"
            "def test_b() -> None:\n"
            "    expected = {'x'}\n"
            "    actual = set()\n"
            "    missing = sorted(set(expected) - set(actual))\n"
            "    assert missing == []\n"
        )
        findings = self._scan_source(tmp_path, source)
        forms = {item.form for item in findings}
        assert "intersection_narrowed_universe" in forms, (
            "同名多次赋值时，前一次的掩蔽形态被覆盖 ⇒ 扫描器漏报（本判据自己的缺陷形态）",
            sorted(forms),
        )

    def test_the_observation_targets_the_real_files(self) -> None:
        """**受判面自检**：观察器真的扫到了本轮三条判据（不是扫了个空目录）。"""
        scanned = [relative for relative in JUDGES if (_ROOT / relative).is_file()]
        assert scanned == list(JUDGES), scanned
        total = sum(
            len(_assertion_nodes(ast.parse((_ROOT / relative).read_text("utf-8"))))
            for relative in JUDGES
        )
        assert total > 20, ("三条判据的断言总数过少 ⇒ 观察面可疑", total)
