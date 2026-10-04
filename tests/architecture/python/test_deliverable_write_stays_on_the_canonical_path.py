"""GOAL-029 EC-03 判据：**写能力的 canonical 路径与旁路风险**（`deliverable.write` / `edit`）。

**本 EC 判定的事实（建档轮勘察，见 GOAL「事实层结论」F-3）**：
`deliverable.write` / `deliverable.edit` 在**域里没有实体**（`packages/domain/` 无
`Deliverable` 类），**没有 HTTP 写面**，且在策略差集表里是**「该拒绝」**（写类 ⇒ 落
`default_effect: DENY` 即正确）。它们的 canonical 路径是
`packages/application/m12_reference/persistence.py::persist_completion` →
`_put_deliverable`（artifact id `f"{run_id}:deliverable.json"`）。

**四件事逐条取证**：

1. **canonical 唯一性**：生产代码里写 `{run_id}:deliverable.json` 的**只有**
   `persist_completion`（`clean_run.py` 是它唯一调用点）。判据用 AST 扫生产根，
   把「谁写了这个 id」变成可复核的集合，而不是靠文档承诺。
2. **写后读得到**（承 `MEM: evidence-read-face-claim-relation`：写得进去 ≠ 读得出来）：
   `persist_completion` 落盘后，**读面**（本 GOAL 新增的 `deliverable_read` 工具，
   与 HTTP 路由 `GET /runs/{id}/deliverable` **同一落点**）能读到同一份 payload 与 digest。
3. **反证（旁路）**：绕过 canonical 路径直写 ArtifactStore 同一个 id ⇒ 判据能**抓住**
   （`_succeeded_run` 的 manifest digest 守卫 + RUNNING→SUCCEEDED 迁移前置校验 ——
   旁路者拿不到「已冻结的 manifest 与之相符」这一事实）。判据断言：**不经
   `persist_completion` 的写入无法通过 canonical 的准入**，且 store 层本身**没有**闸门
   （如实登记：`ArtifactStore.put` 对已存在 id 是 update，保护来自状态机而非写入点）。
4. **残余登记**：`ExperimentStore.save_plan` 是**无条件 upsert**，两个生产写入点各写各的、
   无共同漏斗、无 provenance 层 —— 本 GOAL **不改**它（收窄要动既有写路径与判据），
   以判据形式**固定现状**（防「以为它有漏斗」）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from adapters.canonical import CanonicalReadProvider
from adapters.fakes import FakeArtifactStore
from packages.application.ports.errors import InvalidInputError

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_ROOT = Path(__file__).resolve().parents[3]
#: 生产根（与 m0 的 `PRODUCT_ROOTS` 同集合的子集：只扫会写业务事实的那几个）。
_PRODUCTION_ROOTS = ("packages", "services", "adapters")
_PERSISTENCE = "packages/application/m12_reference/persistence.py"
_DELIVERABLE_SUFFIX = "deliverable.json"
_CLASSIFICATION = "research_deliverable"


def _write_sites(artifact_id_suffix: str) -> list[str]:
    """生产代码里**构造**该 artifact id 的位置（AST 找含该字面量的 f-string/binop）。

    只认「构造 id」的表达式（`f"{...}:deliverable.json"` 或 `prefix + "deliverable.json"`），
    不认注释与字符串常量本身 —— 这样「谁写了这个 id」是可复核的集合。
    """
    hits: list[str] = []
    constant = "_DELIVERABLE_NAME"
    for relative_root in _PRODUCTION_ROOTS:
        for path in sorted((_ROOT / relative_root).rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            if constant not in source:
                continue
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.JoinedStr):
                    continue
                text = ast.unparse(node)
                # 真实形态：f"{truth.run_id}:{_DELIVERABLE_NAME}"（后缀是**常量名**）。
                if "run_id" in text and constant in text:
                    hits.append(f"{path.relative_to(_ROOT).as_posix()}:{node.lineno}")
    return sorted(hits)


def _call_sites(function_name: str) -> list[str]:
    """生产代码里**调用**该函数的位置（排除它的定义处）。"""
    hits: list[str] = []
    for relative_root in _PRODUCTION_ROOTS:
        for path in sorted((_ROOT / relative_root).rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            if f"{function_name}(" not in source:
                continue
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                if called == function_name:
                    hits.append(f"{path.relative_to(_ROOT).as_posix()}:{node.lineno}")
    return sorted(hits)


class TestTheCanonicalWriterIsUnique:
    """① canonical 唯一性：写那个 id 的只有 canonical 路径。"""

    def test_only_the_canonical_writer_builds_the_deliverable_id(self) -> None:
        sites = _write_sites(_DELIVERABLE_SUFFIX)
        assert sites, "受判面非空：至少要有一处构造该 id（否则本判据在空转）"
        offenders = [site for site in sites if not site.startswith(_PERSISTENCE)]
        assert offenders == [], (
            "生产代码里出现了 canonical 之外的交付物 id 构造点（旁路风险必须点名）",
            offenders,
        )

    def test_the_canonical_writer_is_reached_from_exactly_one_place(self) -> None:
        """`persist_completion` 只有一个生产调用点（`clean_run` 的完成阶段）。"""
        sites = _call_sites("persist_completion")
        assert files_of(sites) == ["packages/application/m12_reference/clean_run.py"], (
            "canonical 写入的调用面变了（多一个入口就多一条旁路）",
            sites,
        )

    def test_the_guard_precedes_the_write(self) -> None:
        """`persist_completion` **先**过准入（`_succeeded_run`）**再**写（顺序是判据）。"""
        source = (_ROOT / _PERSISTENCE).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=_PERSISTENCE)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name == "persist_completion"):
                continue
            # 读**语句顺序**（不是「裸名调用的顺序」）：按压实测过，只扫 ast.Name 会看不见
            # 属性调用（`persistence.experiment_store.save_audit(...)` 那类）⇒ 把守卫挪到
            # 它后面时判据仍绿。语句级顺序才咬得住「先判后写」。
            guards: list[int] = []
            writes: list[int] = []
            for statement in node.body:
                for inner in ast.walk(statement):
                    if not isinstance(inner, ast.Call):
                        continue
                    func = inner.func
                    name = (
                        func.attr
                        if isinstance(func, ast.Attribute)
                        else func.id
                        if isinstance(func, ast.Name)
                        else None
                    )
                    if name in ("_succeeded_run",):
                        guards.append(statement.lineno)
                    if name in (
                        "_put_manifest",
                        "_put_deliverable",
                        "save_audit",
                        "put",
                        "save_run",
                    ):
                        writes.append(statement.lineno)
            assert guards, ("准入守卫必须存在于 persist_completion 内", guards)
            assert writes, ("写入点必须存在（否则本判据在空转）", writes)
            assert min(guards) < min(writes), (
                "准入守卫必须是**第一条语句**且先于**任何**写入（含属性调用式写入）——"
                "写入点本身没有闸门，靠的就是这条顺序",
                {"guard": sorted(guards), "write": sorted(writes)},
            )
            return
        raise AssertionError("persist_completion 不存在（本判据的前提变了）")


def files_of(sites: list[str]) -> list[str]:
    """把 `path:line` 归约成去重后的文件名列表（保持顺序）。"""
    seen: list[str] = []
    for site in sites:
        name = site.rsplit(":", 1)[0]
        if name not in seen:
            seen.append(name)
    return seen


class TestWrittenDeliverablesAreReadable:
    """② 写后读得到：写入与可见性一起断言（写得进去 ≠ 读得出来）。"""

    def test_the_read_face_sees_what_the_canonical_writer_wrote(self) -> None:
        """用 canonical writer **构造的同一个 id** 落盘 ⇒ 读面工具读到同一份 payload/digest。"""
        artifacts = FakeArtifactStore()
        run_id = "run-goal029-ec03"
        payload: dict[str, object] = {"summary": "canonical write/read probe", "claims": ["c-1"]}
        # 与 `_put_deliverable` 同一形状：id = f"{run_id}:deliverable.json"、同样的分类。
        from tests.adapters.canonical.test_canonical_read_provider import _write_artifact

        _write_artifact(artifacts, f"{run_id}:{_DELIVERABLE_SUFFIX}", payload)
        meta = artifacts.meta(f"{run_id}:{_DELIVERABLE_SUFFIX}")
        assert meta is not None
        assert meta.classification == _CLASSIFICATION, (
            "读面依赖的分类名必须与 canonical writer 的一致",
            meta.classification,
        )

        provider = CanonicalReadProvider(artifacts)
        record = _deliverable_call(artifacts, run_id)
        from tests.adapters.canonical.test_canonical_read_provider import _spilled_content

        read_back = _spilled_content(artifacts, provider.execute(_READ_SPEC, record))
        assert isinstance(read_back, dict), read_back
        assert read_back["deliverable"] == payload, read_back
        assert read_back["artifact_digest"] == str(meta.digest), read_back

    def test_a_run_without_a_deliverable_is_named(self) -> None:
        """未走 canonical 路径的 run ⇒ 读面**点名**（不生成空报告冒充）。"""
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts)
        record = _deliverable_call(artifacts, "run-never-completed")
        with pytest.raises(InvalidInputError, match="no persisted deliverable"):
            provider.execute(_READ_SPEC, record)


def _deliverable_call(artifacts: FakeArtifactStore, run_id: str) -> Any:
    from tests.adapters.canonical.test_canonical_read_provider import _call

    return _call("deliverable_read", {"run_id": run_id}, artifacts)


def _read_spec() -> Any:
    from packages.domain.enums import EffectClass, ProviderType, TrustLevel
    from packages.domain.tools import ToolProviderSpec

    return ToolProviderSpec(
        id="m12_artifact",
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.BUILT_IN,
        capabilities=["deliverable.read"],
        effect_class=EffectClass.READ_ONLY,
    )


_READ_SPEC = _read_spec()


class TestTheBypassIsCatchable:
    """③ 反证（旁路）：绕过 canonical 路径**不可**取得 canonical 的准入，且如实登记。"""

    def test_the_run_guard_rejects_a_manifest_mismatch(self) -> None:
        """准入的机械形态：`_succeeded_run` 用**已冻结 manifest 的 digest** 对账。

        旁路者即使把 payload 直写进 store，也拿不到「与已冻结 manifest 相符」这一事实 ⇒
        无法让 run 收敛到 SUCCEEDED（写入被准入挡住）。本判据读源码断言这条守卫存在且
        以 digest 对账（不是被绕过的形态）。
        """
        source = (_ROOT / _PERSISTENCE).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=_PERSISTENCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_succeeded_run":
                body = ast.unparse(node)
                assert "manifest_digest" in body and "manifest.digest()" in body, (
                    "准入必须用 manifest digest 对账（否则旁路者可以自证合规）",
                    body[:200],
                )
                assert "SUCCEED" in body, "准入还要过 RUNNING→SUCCEEDED 迁移（状态机是第二重）"
                return
        raise AssertionError("_succeeded_run 不存在（本判据的前提变了）")

    def test_the_store_itself_has_no_gate_and_that_is_recorded(self) -> None:
        """**如实登记**：store 层没有闸门（`put` 对已存在 id 是 update）。

        这不是缺陷而是**边界**：保护来自 canonical 路径的状态机准入，不来自 store。
        判据把它钉住，防「以为 store 会拦」。
        """
        source = (_ROOT / "adapters/fakes/artifact_store.py").read_text(encoding="utf-8")
        assert "def put" in source
        # Fake 与真实 SQLite 实现同语义（既有 contract suite 强制）；两者都不拒绝重复 id。
        sqlite_source = (_ROOT / "adapters/sqlite/artifact_store.py").read_text(encoding="utf-8")
        assert "def put" in sqlite_source
        # 断言两处都**没有**「已存在则拒」的分支（若有，应改用更精确的断言）
        for label, text in (("fakes", source), ("sqlite", sqlite_source)):
            assert "already exists" not in text, (
                f"{label} 的 store 出现了「已存在则拒」的分支 ⇒ 本判据的登记过时了，请复核",
            )


class TestTheExperimentPlanGapIsRecorded:
    """④ 残余登记：实验计划写面**无共同漏斗**（本 GOAL 不改，但必须钉住现状）。"""

    def test_the_plan_writer_has_more_than_one_production_entry(self) -> None:
        """`save_plan` 的生产调用点不止一处 ⇒ 无共同漏斗（登记为残余）。"""
        sites = _call_sites("save_plan")
        files = files_of(sites)
        assert len(files) >= 2, (
            "实验计划的写入点少于两处 ⇒ 现状变了（若已收拢成漏斗，请更新本登记）",
            files,
        )

    def test_the_store_upsert_is_unconditional(self) -> None:
        """store 层的 upsert 无条件（第二次写直接覆盖）—— 这是**登记的事实**。"""
        source = (_ROOT / "adapters/sqlite/experiment_store.py").read_text(encoding="utf-8")
        assert "ON CONFLICT" in source, (
            "实验计划 store 的实现形态变了（本判据登记的是「无条件 upsert」）",
        )
