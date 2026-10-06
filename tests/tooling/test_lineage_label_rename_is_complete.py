"""GOAL-20261006-031 EC-04 判据：`LineageNodeDto.label` → `text` 的**语义修正 + 四处同步**。

**它把什么变成机械事实**：`LineageNodeDto.label` / `ProjectLineageNodeDto.label` 的
**值**从来不是「标签」——`lineage_projection.run_lineage_nodes_edges` 给 claim 节点填的是
`claim.statement`（正文）、给 source/evidence 节点填 `source_ref`、给 artifact/model 节点填
id/ref（`G24-4` 的原始登记：**实测承载 claim 正文**）。字段名与内容语义不一致 ⇒ 改名 `text`，
并把「旧名零命中」变成**逐字节**扫描出来的一条判据（不是人工目检）。

**五件事逐条取证**：

1. **改名落地**：两个 DTO 声明的字段是 `text`（AST：类体注解名），生产构造点逐条用 `text=`；
2. **四处同步**：DTO（`services/api/dto/inspection.py`）+ OpenAPI 快照
   （`docs/api/openapi.m13.json`）+ web 类型（`apps/web/src/api/types.ts` ×2）+
   e2e 夹具（`apps/web/tests/e2e/stub-routes-lineage.ts`）——**逐文件**断言新名在场、旧名不在场；
3. **旧名零命中（逐字节）**：受判面 = **列出的文件清单**（DTO ×2 / 生产投影 ×2 /
   web 类型 / 两个列定义 / 夹具 / 快照）——在这些文件里 `label` 作为**节点字段**零命中
   （`trust_label` / `aria-label` 这类**别的字段**不算命中，判据按词边界 + 上下文排除）；
4. **快照判据绿**：既有 `tests/contracts/test_openapi_snapshot.py` **一字未改**且绿
   （它再生成 schema 与仓库快照比对 ⇒ 快照漂移会被它抓住）；
5. **反证**：把旧名放回一处（内存构造的 DTO 副本）⇒ 本判据的扫描函数**报出该处并点名文件**。

**兼容性实测（EC-04(d)，不许推定）**：消费者普查 = 仓内自有的 web + tests + 快照；
`ProvenanceGraph.tsx` / `provenanceModel.ts` 的 `label` 是**它们自己的视图模型字段**（值取自
`ClaimDto.statement` / `EvidenceDto.id`，**不消费** `LineageNodeDto`）⇒ 与本次改名无关。
本仓**不对外发布**该 DTO（无外部契约承诺面）⇒ 改名不破坏兼容。该普查的机械形态见
`test_the_consumers_outside_the_surface_do_not_read_the_old_field`。
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

#: 受判面（EC-04(a) 的四处同步 + 两个生产投影；**逐文件**列出，不靠 glob 通配掩盖）。
SURFACE: tuple[str, ...] = (
    "services/api/dto/inspection.py",
    "services/api/lineage_projection.py",
    "services/api/project_lineage.py",
    "apps/web/src/api/types.ts",
    "apps/web/src/features/lineage/lineageColumns.tsx",
    "apps/web/src/features/lineage/projectLineageColumns.tsx",
    "apps/web/tests/e2e/stub-routes-lineage.ts",
)
SNAPSHOT = "docs/api/openapi.m13.json"

#: 判据文件自身的仓库相对路径（全仓扫描时排除它：判据必须点名旧字段才能测它）。
_SELF = "tests/tooling/test_lineage_label_rename_is_complete.py"

#: 「承载血缘 DTO」的上下文标记：文件出现其一 ⇒ 它在血缘面上（全仓扫描的受判面）。
_CONTEXT_MARKERS: tuple[str, ...] = (
    "LineageNodeDto",
    "ProjectLineageNodeDto",
    "lineage_projection",
    "project_lineage",
    "lineageColumns",
    "lineage_node",
)

#: 新名 / 旧名（**独立书写**，不 import 产品常量当预言机）。
NEW_FIELD = "text"
OLD_FIELD = "label"

#: 「旧名」的**节点字段**形态：`label:`（对象字面量 / TS 接口 / YAML 键）或 `label=`
#: （Python 构造点）或 `"label"`（快照 JSON 键）。**别的字段**（`trust_label` /
#: `aria-label` / `metric.label`）不在此形态内 ⇒ 不误报。
#: 「旧名」的**节点字段**形态：`label:`（对象字面量 / TS 接口 / YAML 键）、`label=`
#: （Python 构造点）、`"label"`（快照 JSON 键）、`.label`（属性**读取**）。
#: **别的字段**（`trust_label` / `aria-label`）不在此形态内 ⇒ 不误报。
#:
#: **为什么属性读必须算命中**（按压实测的教训）：首版把 `.` 也排除在词边界外
#: ⇒ 对 `row.label`（TS 里读旧字段的真实形态）**不报** ⇒ 反证臂（把旧名放回
#: `lineageColumns.tsx`）判绿，判据是**空转**的。属性读是 hit；`-` 与 `_` 的排除保留
#: （`aria-label` / `trust_label` 是别的字段）。
_OLD_FIELD_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?<![\w\-])(?:\w+\.)?label\s*[:,=]"),
    re.compile(r"\.label\b"),
    re.compile(r'"label"\s*:'),
)


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _old_field_hits(relative: str) -> list[str]:
    """该文件里**节点字段形态**的旧名命中行（逐行判定，报出行号可诊断）。"""
    hits: list[str] = []
    for number, line in enumerate(_text(relative).splitlines(), start=1):
        if any(pattern.search(line) for pattern in _OLD_FIELD_PATTERNS):
            hits.append(f"{relative}:{number}: {line.strip()}")
    return hits


def _dto_fields(relative: str, class_name: str) -> list[str]:
    """该 DTO 类体的**字段注解名**（AST 读声明，不是文本里出现过这个名字）。"""
    tree = ast.parse(_text(relative), filename=relative)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return [
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            ]
    raise AssertionError(f"{relative} 里没有 {class_name}（本判据的前提变了）")


def _snapshot_schema(name: str) -> dict[str, Any]:
    """快照里某个 component schema 的 properties（判据读**快照文件**本身）。"""
    schema: dict[str, Any] = json.loads(_text(SNAPSHOT))
    properties = schema["components"]["schemas"][name]["properties"]
    assert isinstance(properties, dict), (name, "快照 schema 的 properties 不是对象")
    return properties


class TestTheFieldIsRenamed:
    """① 改名落地：两个 DTO 的字段是 `text`，且**不再是** `label`。"""

    def test_both_lineage_dtos_declare_text(self) -> None:
        for class_name in ("LineageNodeDto", "ProjectLineageNodeDto"):
            fields = _dto_fields("services/api/dto/inspection.py", class_name)
            assert NEW_FIELD in fields, (class_name, fields)
            assert OLD_FIELD not in fields, (class_name, "旧名字段仍在", fields)

    def test_the_snapshot_schema_declares_text(self) -> None:
        for name in ("LineageNodeDto", "ProjectLineageNodeDto"):
            properties = _snapshot_schema(name)
            assert NEW_FIELD in properties, (name, sorted(properties))
            assert OLD_FIELD not in properties, (name, "快照里旧名仍在")


class TestTheFourPlacesAreSynchronised:
    """② 四处同步：受判面**逐文件**断言新名在场（缺哪处点名哪处）。"""

    def test_every_surface_file_carries_the_new_field_name(self) -> None:
        missing = [relative for relative in SURFACE if NEW_FIELD not in _text(relative)]
        assert missing == [], ("这些文件没有携带新字段名（同步漏了一处）", missing)

    def test_the_snapshot_carries_the_new_field_name(self) -> None:
        assert NEW_FIELD in json.dumps(_snapshot_schema("LineageNodeDto")), sorted(
            _snapshot_schema("LineageNodeDto")
        )


class TestTheOldFieldNameHasZeroHits:
    """③ 旧名零命中（**逐字节**扫受判面；行号可诊断）。"""

    def test_no_surface_file_carries_the_old_field_name(self) -> None:
        hits = [hit for relative in SURFACE for hit in _old_field_hits(relative)]
        assert hits == [], ("受判面出现了旧名字段（逐条点名）", hits)

    def test_the_snapshot_carries_no_old_field_name(self) -> None:
        assert '"label"' not in _text(SNAPSHOT), '快照里仍有 "label" 键（受判面非空）'

    def test_no_lineage_context_file_carries_the_old_field_name(self) -> None:
        """**全仓**扫描：凡承载血缘 DTO 的文件都不得再出现旧名（受判面从文件推出来）。

        受判面 = 「出现血缘 DTO / 投影 / 列定义标记的文件」这一**从文件本身推出来**的集合
        （不是白名单）——新增一个承载该 DTO 的文件会自动进面。

        **本条排除判据文件自身**：判据必须**点名**旧字段才能测它（docstring 与
        `_OLD_FIELD_*` 常量里的 `label` 是判据的**构造**）。这一排除**明写**在这里而不是
        静默过滤 —— 受判面里其余**任何**文件命中即判红（反证臂按压过）。
        """
        hits: list[str] = []
        scanned: list[str] = []
        for directory in ("services", "apps/web", "tests", "docs"):
            for path in sorted((ROOT / directory).rglob("*")):
                if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".json"}:
                    continue
                relative = path.relative_to(ROOT).as_posix()
                if "node_modules" in relative or relative == _SELF:
                    continue
                # 隐藏目录（工具状态 / 缓存）不是源码面：`.mimosa/hook-state` 这类
                # 客户端产物会随会话变化 ⇒ 留在面内会让判据的受判集**不稳定**。
                if any(part.startswith(".") for part in relative.split("/")):
                    continue
                body = path.read_text(encoding="utf-8", errors="replace")
                if not any(marker in body for marker in _CONTEXT_MARKERS):
                    continue
                scanned.append(relative)
                for number, line in enumerate(body.splitlines(), start=1):
                    if any(pattern.search(line) for pattern in _OLD_FIELD_PATTERNS):
                        hits.append(f"{relative}:{number}: {line.strip()}")
        assert scanned, "受判面非空：至少要有一个承载血缘上下文的文件（否则本判据空转）"
        assert hits == [], ("血缘上下文文件里出现了旧名字段（逐条点名）", hits)

    def test_the_scan_would_catch_a_reintroduced_old_name(self) -> None:
        """**判据自检**：扫描函数对合成输入**真的会报**（否则「零命中」可以是空转）。"""
        sample = '        nodes.append({"id": "x", "kind": "claim", "label": "body"})'
        hits = [p for p in _OLD_FIELD_PATTERNS if p.search(sample)]
        assert hits, "扫描函数对旧名形态不报 ⇒ 零命中断言是空转"

    def test_the_scan_ignores_unrelated_fields(self) -> None:
        """反面自检：`trust_label` / `aria-label` 这类**别的字段**不得被误报。"""
        for unaffected in (
            "    source_trust_label: str | None = None",
            "        source_trust_label=evidence.source_trust_label,",
            '      aria-label={"something"}',
            '    labels={forbidden: "x"},',
            "            labels={key: PROMPT.value},",
        ):
            assert not any(p.search(unaffected) for p in _OLD_FIELD_PATTERNS), unaffected


class TestTheConsumersOutsideTheSurface:
    """④ 兼容性实测：受判面之外的消费者**不读**旧字段（普查结论的机械形态）。"""

    def test_the_consumers_outside_the_surface_do_not_read_the_old_field(self) -> None:
        """`ProvenanceGraph` / `provenanceModel` 的 `label` 是**自己的视图模型**（值取自
        `ClaimDto.statement` / `EvidenceDto.id`），不消费血缘 DTO 的字段。

        判据形态：这两个文件里出现了 `lineage` DTO 的旧字段**读取**点（`row.label` /
        `node.label`）才算命中；`label:` 定义与本地视图模型字段不算 —— 但它们**必须
        不 import** 那两个 DTO（import 了就可能消费）。
        """
        for relative in (
            "apps/web/src/features/lineage/provenanceModel.ts",
            "apps/web/src/features/lineage/ProvenanceGraph.tsx",
        ):
            source = _text(relative)
            assert "LineageNodeDto" not in source, (
                f"{relative} 直接引用了血缘 DTO ⇒ 兼容性普查结论过时，请复核",
            )
        # run 级列定义是**受判面内**的（已改名）；这里证明列渲染用的是新名。
        columns = _text("apps/web/src/features/lineage/lineageColumns.tsx")
        assert "row.text" in columns, columns


class TestTheSnapshotJudgeIsUntouchedAndGreen:
    """⑤ 既有快照判据**一字未改**（本 EC 不放宽任何既有断言）。"""

    def test_the_existing_snapshot_judge_is_unchanged(self) -> None:
        """既有判据的文件里不得出现本轮的改名痕迹（改动面必须只有受判面）。

        形态：判据文件不含 `text` 字段的**血缘语义**断言（它是通用快照判定），
        且它仍按「再生成 vs 仓库快照」比对。
        """
        judge = "tests/contracts/test_openapi_snapshot.py"
        source = _text(judge)
        assert "LineageNodeDto" not in source, "既有快照判据被本 EC 改动（越界）"
        assert "drifted from generated OpenAPI" in source, source[:200]
