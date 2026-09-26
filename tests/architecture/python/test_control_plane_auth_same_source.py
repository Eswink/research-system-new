"""控制面写面认证的同源判据（GOAL-019 EC-04 / PLAN-20260926-192）。

四份文档（`docs/security/IDENTITY_AND_ACCESS.md`、`docs/security/THREAT_MODEL.md` §6、
`docs/api/CONTROL_PLANE_API.md`、`docs/integration/LIVE_MODEL_RUNBOOK.md`）与代码必须**同源**。
本判据判**结构**与**语义**，不判文笔。

**五组断言（每一组都能被按压判红）**：

- **AC-1 同源声明逐字在场**：四份文档各含**同一句**声明，且**恰好一次**。
  只改一处口径 ⇒ 红。
- **AC-2 未覆盖范围各自声明**：每份文档有**自己的**锚点与**自己的**措辞
  （不许互相顶替）；删掉任一份的未覆盖块 ⇒ 红。
- **AC-3 零夸大**：`读面已认证` / `已实现多租户` / `已实现 RBAC` 之类**肯定式**安全断言
  一律不得出现。**否定语境**（`不得`/`不是`/`禁止`… 紧邻 14 字内）是**有意豁免**
  ——§6.6 的「新口径不得被简写成『授权面已覆盖』」正是这种句子——**豁免本身也受判**
  （`test_the_prohibition_allowance_is_not_a_hole`）。
- **AC-4 判据绑到代码**：分类**复用** `_MUTATING_METHODS`（且全模块只有这一处方法字面集合）；
  认证面**不得**引用幂等面的 `_ANALYSIS_ACTIONS`（异常集不是认证集，见 MEM-143）；
  读面靠 `NotIn` 早期放行；token 比较走 `hmac.compare_digest` 且**没有** `==` 比较；
  变量名**只有一个读取点**且与文档同源；**无新增依赖**。
- **AC-5 注册顺序**：`create_app` 里认证注册在 `IdempotencyMiddleware` **之后**
  （Starlette `reversed(middleware)` ⇒ 后注册者在外层 ⇒ 认证先跑）。顺序反了读面也会被 401。

**不读真实凭据**：本判据只读源码常量名与文档字面量，**不读环境、不打印值**。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

#: 写面分类：用户判词 (i) 的**唯一**来源（`services/api/middleware.py` 的 `_MUTATING_METHODS`）。
_MUTATING_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})
_HTTP_METHODS = frozenset("GET HEAD POST PUT PATCH DELETE OPTIONS TRACE CONNECT".split())

#: 四份文档必须**逐字**共用的声明句（含全角标点）。改口径必须四处同改。
_CANONICAL = (
    "**认证覆盖**：写面（POST / PATCH / PUT / DELETE）已认证；"
    "读面（GET / HEAD）未认证；多租户与 RBAC 未实现。"
)

IDENTITY = REPO_ROOT / "docs/security/IDENTITY_AND_ACCESS.md"
THREAT_MODEL = REPO_ROOT / "docs/security/THREAT_MODEL.md"
API_SKETCH = REPO_ROOT / "docs/api/CONTROL_PLANE_API.md"
RUNBOOK = REPO_ROOT / "docs/integration/LIVE_MODEL_RUNBOOK.md"
MIDDLEWARE = REPO_ROOT / "services/api/middleware.py"
APP = REPO_ROOT / "services/api/app.py"

#: 每份文档**自己的**未覆盖范围锚点 + 它**必须**点到的措辞（逐份不同 ⇒ 不许互相顶替）。
_DOC_UNCOVERED: tuple[tuple[Path, str, tuple[str, ...]], ...] = (
    (
        IDENTITY,
        "### 未覆盖范围（明确不覆盖什么）",
        ("读面未认证", "多租户", "RBAC", "对象级授权", "R-M1"),
    ),
    (
        THREAT_MODEL,
        "### 6.7 实况更新：Control Plane 写面认证",
        ("读面", "多租户", "RBAC", "BOLA", "零夸大"),
    ),
    (API_SKETCH, "**未覆盖范围**", ("读面认证", "多租户与 RBAC", "对象级授权", "未做")),
    (
        RUNBOOK,
        "**未覆盖范围（不得读成更强结论）**",
        ("读面未认证", "多租户与 RBAC 未实现", "对象级授权", "不接受"),
    ),
)

#: 未覆盖块的观察窗（从锚点起算的字符数）。窗口**有界**：断言锚在声明附近，而不是"文档里某处有"。
_WINDOW = 1200

#: 肯定式安全断言（**只增不减**；新增措辞要连带加一条按压）。
_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "读面已认证",
    "读面已受保护",
    "已实现多租户",
    "多租户已实现",
    "已实现 RBAC",
    "RBAC 已实现",
    "已实现对象级授权",
    "已实现 BOLA",
    "已修复 BOLA",
    "已实现授权",
    "授权面已覆盖",
    "全部接口已认证",
    "认证已覆盖全部",
    "已满足最小权限",
    "已通过安全审计",
    "项目是安全的",
    "项目已安全",
    "安全边界已收口",
    "无未授权访问风险",
    "完全可复现",
    "调用方可自报身份",
)

#: 否定语境标记：与禁用短语同句出现时算「引述禁令」，不算宣示。
_PROHIBITION_MARKERS = ("不得", "不是", "禁止", "勿", "杜绝", "并不", "而非")
#: 同句判定：以句读切句，且**有界**（超长句只回看末 200 字）。
_SENTENCE_DELIMITERS = "。；;\n"
_ALLOWANCE_WINDOW = 200

#: 认证模块允许的**第三方**导入根（"不得新增依赖"的结构形态）。
_THIRD_PARTY_ALLOWED = frozenset({"fastapi", "starlette"})
_FIRST_PARTY_ROOTS = frozenset({"packages", "services", "adapters", "core", "tests", "apps"})

#: 变量名常量（**只登记名字**；值不进任何 tracked 文件）。
_ENV_CONSTANTS = ("CONTROL_PLANE_TOKEN_ENV", "CONTROL_PLANE_PRINCIPAL_ID_ENV")
_EXPECTED_ENV_NAMES = frozenset({
    "RESEARCHOS_CONTROL_PLANE_TOKEN",
    "RESEARCHOS_CONTROL_PLANE_PRINCIPAL_ID",
})

#: 非测试源码根（"一个开关一个读取点"的扫描面）。
_SOURCE_ROOTS = ("services", "packages", "adapters", "core", "apps")

_DOCS = (IDENTITY, THREAT_MODEL, API_SKETCH, RUNBOOK)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_text(path))


def _window(text: str, anchor: str) -> str:
    index = text.find(anchor)
    assert index != -1, f"未覆盖范围的锚点缺失：{anchor!r}"
    return text[index : index + _WINDOW]


def _overclaims(text: str) -> list[str]:
    """返回**非**否定语境下的肯定式安全断言（空列表 = 干净）。

    豁免规则：短语**所在句**里出现否定标记（`不得` / `不是` / `禁止` …）⇒ 视为引述禁令。
    句子按句读切分并回看最多 `_ALLOWANCE_WINDOW` 字 ⇒ 豁免不会跨句蔓延。
    """
    found: list[str] = []
    for phrase in _FORBIDDEN_PHRASES:
        start = 0
        while True:
            index = text.find(phrase, start)
            if index == -1:
                break
            if not any(marker in _sentence_before(text, index) for marker in _PROHIBITION_MARKERS):
                found.append(phrase)
            start = index + 1
    return found


def _sentence_before(text: str, index: int) -> str:
    """短语**所在句**的前文（到最近一个句读为止，且最多回看 `_ALLOWANCE_WINDOW` 字）。"""
    sentence_start = 0
    for delimiter in _SENTENCE_DELIMITERS:
        sentence_start = max(sentence_start, text.rfind(delimiter, 0, index) + 1)
    return text[max(sentence_start, index - _ALLOWANCE_WINDOW) : index]


def _assignment_value(tree: ast.Module, name: str) -> ast.expr:
    matches = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    ]
    assert len(matches) == 1, f"{name} 必须恰好有一处模块级赋值（实际 {len(matches)} 处）"
    return matches[0]


def _class(tree: ast.Module, name: str) -> ast.ClassDef:
    matches = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name]
    assert len(matches) == 1, f"{name} 必须恰好有一个类定义"
    return matches[0]


def _function(nodes: list[ast.stmt], name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"找不到函数 {name}")


def _names(node: ast.AST) -> set[str]:
    found: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            found.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            found.add(sub.attr)
    return found


def _method_literal_node(tree: ast.Module) -> ast.expr:
    """`_MUTATING_METHODS` 的**字面集合节点**（剥掉 `frozenset(...)` 包装）。"""
    node: ast.expr = _assignment_value(tree, "_MUTATING_METHODS")
    if isinstance(node, ast.Call):
        assert isinstance(node.func, ast.Name) and node.func.id == "frozenset", ast.unparse(node)
        node = node.args[0]
    return node


def _interpolated_names(node: ast.AST) -> set[str]:
    """f-string 里被插值**常量名**（用来证明警告真的点名了变量）。"""
    return {
        sub.value.id
        for sub in ast.walk(node)
        if isinstance(sub, ast.FormattedValue) and isinstance(sub.value, ast.Name)
    }


def _literal_method_sets(tree: ast.Module) -> dict[int, frozenset[str]]:
    """模块内所有「字面 HTTP 方法集合」：{行号: 集合}（用于证明分类只有一处）。"""
    found: dict[int, frozenset[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            values = frozenset(
                e.value
                for e in node.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            )
            if values and values <= _HTTP_METHODS:
                found[node.lineno] = values
    return found


def _string_constants(node: ast.AST) -> str:
    parts = [
        sub.value
        for sub in ast.walk(node)
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str)
    ]
    return "\n".join(parts)


def _token_comparisons(tree: ast.Module) -> list[str]:
    """token 相关的 `==` / `!=` 比较（应当**为空**——必须走常数时间比较）。"""
    suspects = {"provided", "expected", "token"}
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
            continue
        operands = [node.left, *node.comparators]
        if suspects & set().union(*(_names(operand) for operand in operands)):
            found.append(ast.unparse(node))
    return found


# --------------------------------------------------------------------------- AC-1


def test_canonical_declaration_is_verbatim_in_all_four_docs() -> None:
    for path in _DOCS:
        text = _text(path)
        assert text.count(_CANONICAL) == 1, (
            f"{path.relative_to(REPO_ROOT)} 必须**恰好一次**逐字包含同源声明句"
            f"（实际 {text.count(_CANONICAL)} 次）：{_CANONICAL}"
        )


# --------------------------------------------------------------------------- AC-2


def test_each_doc_declares_its_own_uncovered_range() -> None:
    for path, anchor, topics in _DOC_UNCOVERED:
        block = _window(_text(path), anchor)
        missing = [topic for topic in topics if topic not in block]
        assert not missing, (
            f"{path.relative_to(REPO_ROOT)} 的未覆盖范围块（锚点 {anchor!r}）"
            f"缺少必需措辞：{missing}"
        )


# --------------------------------------------------------------------------- AC-3


def test_no_affirmative_security_overclaim_in_any_doc() -> None:
    for path in _DOCS:
        offenders = _overclaims(_text(path))
        assert not offenders, (
            f"{path.relative_to(REPO_ROOT)} 出现肯定式安全断言：{offenders}"
            "（本 GOAL 只交付写面认证，**不得**被读成更强结论）"
        )


def test_the_prohibition_allowance_is_not_a_hole() -> None:
    """豁免机制**自身**受判：引述禁令可以，宣示不行。"""
    assert _overclaims("本节声称：授权面已覆盖。") == ["授权面已覆盖"]
    assert _overclaims("已实现 RBAC。") == ["已实现 RBAC"]
    assert _overclaims("不得把新口径简写成「授权面已覆盖」") == []
    assert _overclaims("这不是「项目是安全的」") == []


# --------------------------------------------------------------------------- AC-4


def test_auth_face_reuses_the_single_classification() -> None:
    tree = _tree(MIDDLEWARE)
    node = _method_literal_node(tree)
    assert frozenset(ast.literal_eval(node)) == _MUTATING_METHODS, (
        "写面分类必须仍恰为 POST / PATCH / PUT / DELETE"
    )

    literals = _literal_method_sets(tree)
    assert set(literals) == {node.lineno}, (
        "认证模块里出现了**第二处**方法字面集合（认证面必须复用 `_MUTATING_METHODS`，"
        f"不得自建）：{sorted(literals)}"
    )

    dispatch = _function(_class(tree, "PrincipalAuthMiddleware").body, "dispatch")
    pass_through = [
        node
        for node in ast.walk(dispatch)
        if isinstance(node, ast.Compare)
        and any(isinstance(op, ast.NotIn) for op in node.ops)
        and any(
            isinstance(comparator, ast.Name) and comparator.id == "_MUTATING_METHODS"
            for comparator in node.comparators
        )
    ]
    assert pass_through, (
        "认证中间件必须以 `method not in _MUTATING_METHODS` 的形式**放行读面**"
        "（读面不加认证是用户判词 (i)）"
    )


def test_auth_face_does_not_inherit_the_idempotency_exception_set() -> None:
    tree = _tree(MIDDLEWARE)
    auth_names = _names(_class(tree, "PrincipalAuthMiddleware"))
    assert "_ANALYSIS_ACTIONS" not in auth_names, (
        "`_ANALYSIS_ACTIONS` 是**幂等面**的例外集，不是认证面的分类；"
        "认证面引用它会把幂等特例带进认证（见 MEM-20260926-143）"
    )


def test_token_comparison_is_constant_time_and_env_sourced() -> None:
    tree = _tree(MIDDLEWARE)
    verify = _function(tree.body, "verify_control_plane_token")
    assert "compare_digest" in _names(verify), "token 比较必须走 `hmac.compare_digest`"
    assert _token_comparisons(tree) == [], (
        f"token 不得用 `==` / `!=` 直接比较：{_token_comparisons(tree)}"
    )

    from_env = _function(tree.body, "control_plane_auth_from_env")
    calls = [
        node
        for node in ast.walk(from_env)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "environ"
    ]
    assert len(calls) == 2, (
        "变量名只能有一个读取点：`control_plane_auth_from_env` 恰读两个变量"
        f"（token + 主体标识），实际 {len(calls)} 次"
    )

    names = {ast.literal_eval(_assignment_value(tree, name)) for name in _ENV_CONSTANTS}
    assert names == _EXPECTED_ENV_NAMES
    runbook = _text(RUNBOOK)
    for name in sorted(names):
        assert name in runbook, f"runbook 未登记变量名 {name}（值不得出现在任何 tracked 文件）"


def test_the_env_variable_value_has_a_single_reader_in_source() -> None:
    """变量名**字面量**在非测试源码里只出现一次（= 常量定义本身）。"""
    literal = ast.literal_eval(_assignment_value(_tree(MIDDLEWARE), "CONTROL_PLANE_TOKEN_ENV"))
    hits: list[Path] = []
    for root in _SOURCE_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if literal in path.read_text(encoding="utf-8"):
                hits.append(path.relative_to(REPO_ROOT))
    assert hits == [MIDDLEWARE.relative_to(REPO_ROOT)], (
        f"{literal} 的字面量只允许出现在常量定义处，实际命中：{hits}"
    )


def test_no_new_dependency_in_the_auth_module() -> None:
    tree = _tree(MIDDLEWARE)
    roots: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    unknown = {
        root
        for root in roots
        if root not in sys.stdlib_module_names
        and root not in _FIRST_PARTY_ROOTS
        and root not in _THIRD_PARTY_ALLOWED
    }
    assert not unknown, f"认证模块新增了未授权依赖：{sorted(unknown)}（token 校验必须用标准库）"


def test_disabled_auth_warning_names_the_state_and_the_boundaries() -> None:
    tree = _tree(MIDDLEWARE)
    warning_fn = _function(tree.body, "auth_disabled_warning")
    warning = _string_constants(warning_fn)
    assert "CONTROL PLANE AUTH IS DISABLED" in warning, "认证关闭时必须**显式**说「无认证」"
    assert "ANY caller" in warning, "警告必须写明「任何能连上本进程的调用方都能写」"
    assert "CONTROL_PLANE_TOKEN_ENV" in _interpolated_names(warning_fn), (
        "警告必须点名变量名（f-string 插值该常量；常量值另有同源判据）"
    )
    assert "NOT a statement that the project is secure" in warning, (
        "警告不得被读成安全结论（`R-M1` 未收口 ⇒ 不得宣称项目安全）"
    )


# --------------------------------------------------------------------------- AC-5


def test_auth_middleware_is_registered_after_idempotency() -> None:
    tree = _tree(APP)
    create_app = _function(tree.body, "create_app")
    order: dict[str, int] = {}
    for statement in create_app.body:
        for name in ("IdempotencyMiddleware", "_install_write_face_auth"):
            if name in _names(statement) and name not in order:
                order[name] = statement.lineno
    assert set(order) == {"IdempotencyMiddleware", "_install_write_face_auth"}, (
        "`create_app` 必须同时注册幂等中间件与写面认证（否则认证根本没装上）"
    )
    assert order["IdempotencyMiddleware"] < order["_install_write_face_auth"], (
        "认证必须在幂等**之后**注册：Starlette 用 `reversed(middleware)` 建栈，"
        "后注册者在外层 ⇒ 认证先跑；顺序反了连读面都会被 401"
    )
