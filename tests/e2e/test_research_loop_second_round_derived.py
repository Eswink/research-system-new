"""GOAL-20261006-031 EC-03 判据：**科研真成环** —— 两轮研究，第二轮由第一轮结果**派生**。

**被测对象**：产品那条链 —— `two_round_research_loop_v1.yaml`（本轮新增）经
`compile → preflight → freeze → execute_phases` 跑完，两个 phase 都由**运行链**执行：

  * `round1`：`evidence.read`（读本 run 的证据投影）→ `literature.search`
    （`query` 取自声明输入）；
  * `round2`：`evidence.read`（**再读一次**投影）→ `artifact.read`（按**声明的后缀**
    选中 round1 的检索制品、读它的**内容**）→ `literature.read`（`ids` 来自
    **刚读到的内容**的 `content.ids`，`requires_previous_ids=False`）。

**四件事逐条取证**（(a) 声明 / (b) 两臂 / (c) 留痕与读面 / (d) 反证两向）：

1. **(a) 派生是声明的**：① 协议文档**自己**写了两个 phase 的 `capability_execution:
   run_chain` 与能力集（判据读 YAML 原文，不靠产品代码转述）；② 装配声明（`RunChainCall`
   的 `artifact_from_previous` / `ids_from_previous` / `requires_previous_ids`）**逐字**
   钉在判据里 —— 「第二轮读哪一个制品、从哪个路径取标识、什么时候跳过」三件事都是**声明的
   字段**，应用层没有「如果就」。
2. **(b) 两条臂都实测且判据能区分**：① **触发**臂（检索响应非空）⇒ 真跑第二轮，且第二轮
   读取步的**操作键/证据里逐字带着第一轮返回的 PMID**（可追到第一轮的具体产出）；②
   **不触发**臂（同一份协议与装配，只把检索响应换成零命中）⇒ 读取步**带理由跳过**
   （`run.completed` 的 `skipped` 逐字点名工具与字段）。**两条臂的判词不同**：触发臂
   有 `literature_read` 工具证据且无跳过事实；不触发臂**没有**该证据且**有**跳过事实 ——
   本判据对同一读数做**互斥断言**，单一判据不可能同时判过两臂。
3. **(c) 迭代留痕与读面**：每轮的交付物落 canonical（artifact / evidence，走既有
   `register_session_result` 路径）；第二轮**经读面**（`evidence.read` 的返回内容里含
   第一轮工具证据的 id；`artifact.read` 的返回**内容**等于第一轮检索制品的字节）
   读到第一轮的结论 —— **不是内存传递**。
4. **(d) 反证两向**：① 把派生规则改坏（`ids_from_previous` 指到不存在的路径）⇒ run
   **FAILED** 且判词点名那条路径；② 把第二轮的读面抓手摘掉（`artifact_from_previous`
   指到选不中的后缀）⇒ 第二轮**判负**（run FAILED，判词点名「选中数 ≠ 1」）。

**装配与读面辅助在 `tests/e2e/two_round_loop_support.py`**（规模门禁：本文件 ≤ 450 行）。

**如实边界**（本文件不声称已解决）：交付物契约只判**产物存在与来源覆盖**，不判内容
质量 —— 「模型读懂了第一轮的结论」不是本判据的主张；两轮是本轮射程，收敛/上限不在内。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient

from tests.e2e.live_run_support import start_run as _start
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay
from tests.e2e.two_round_loop_support import (
    IDS_PATH,
    MOCK_PMIDS,
    PROTOCOL,
    ROUND1_PHASE,
    ROUND2_PHASE,
    SEARCH_ARTIFACT_SUFFIX,
    TOOL_IDS,
    OfflineNcbi,
    all_calls,
    assembled_deps,
    content_of,
    derived_calls,
    rewire_calls,
    skip_facts,
    task_of_evidence,
    tool_evidence,
    with_read_step,
)
from tests.e2e.two_round_loop_support import (
    app as _app,
)

__all__ = ["mock_relay"]

_FROM_CANONICAL = "m12_artifact"
_FROM_NCBI = "ncbi_eutils"
_READ_REF = (_FROM_NCBI, TOOL_IDS["literature.read"])
_SEARCH_REF = (_FROM_NCBI, TOOL_IDS["literature.search"])
_ARTIFACT_REF = (_FROM_CANONICAL, TOOL_IDS["artifact.read"])


def _run(
    mock_relay: str, *, pmids: tuple[str, ...] = MOCK_PMIDS, calls: Any = None
) -> dict[str, Any]:
    """跑一次两轮 run 并取回读面快照（`calls` 非空 ⇒ 反证臂换声明）。"""
    offline = OfflineNcbi(pmids=pmids)
    deps = assembled_deps(mock_relay, offline=offline)
    if calls is not None:
        rewire_calls(deps, calls)
    with TestClient(_app(deps)) as client:
        run = _start(client, PROTOCOL)
        reads = _read_chain(client, run)
        skipped = skip_facts(client, run["id"])
    return {"run": run, "reads": reads, "skipped": skipped, "offline": offline}


class TestTheDerivationIsDeclared:
    """(a) 派生是**声明**的：协议文档 + 装配字段两面逐字在场。"""

    def test_the_protocol_document_declares_both_rounds_as_run_chain(self) -> None:
        """① 文档**自己**写了两轮与执行方式（判据读 YAML 原文，独立于产品代码）。"""
        raw = yaml.safe_load(Path(f"examples/protocols/{PROTOCOL}").read_text(encoding="utf-8"))
        phases = {phase["id"]: phase for phase in raw["phases"]}
        assert set(phases) == {ROUND1_PHASE, ROUND2_PHASE}, sorted(phases)
        for phase_id in (ROUND1_PHASE, ROUND2_PHASE):
            assert phases[phase_id].get("capability_execution") == "run_chain", phases[phase_id]
        assert set(phases[ROUND1_PHASE]["required_capabilities"]) == {
            "artifact.read",
            "evidence.read",
            "literature.search",
        }, phases[ROUND1_PHASE]
        assert set(phases[ROUND2_PHASE]["required_capabilities"]) == {
            "artifact.read",
            "evidence.read",
            "literature.read",
        }, phases[ROUND2_PHASE]

    def test_the_round_two_chain_declares_where_every_input_comes_from(self) -> None:
        """② 装配声明的**三个取值来源**逐字在场（缺一 ⇒ 本判据判红并点名缺哪条）。"""
        calls = derived_calls()
        by_tool = {call.tool_id: call for call in calls}
        assert set(by_tool) == {
            TOOL_IDS["evidence.read"],
            TOOL_IDS["artifact.read"],
            TOOL_IDS["literature.read"],
        }, sorted(by_tool)
        artifact_call = by_tool[TOOL_IDS["artifact.read"]]
        assert artifact_call.artifact_from_previous == SEARCH_ARTIFACT_SUFFIX, artifact_call
        read_call = by_tool[TOOL_IDS["literature.read"]]
        assert read_call.ids_from_previous == IDS_PATH, read_call
        assert read_call.requires_previous_ids is False, (
            "读取步必须声明「不触发 ⇒ 跳过」（缺省 True 会在零命中时判失败而非跳过）",
            read_call,
        )
        # 每一轮都声明了自己属于哪个 phase（过滤细化到 phase 级的前提）。
        phases = {call.phase_id for call in all_calls()}
        assert phases == {ROUND1_PHASE, ROUND2_PHASE}, phases

    def test_the_application_layer_has_no_if_then_business_logic(self) -> None:
        """③ 触发判定是**字段在场性**，不是业务判断：应用层不 import 任何领域语义。

        `phase_capability_triggers` 只做三件事（过滤 / 取字段 / 判空列表），不读
        tool_id 字面量、不做「哪个能力该跳」的判断 —— 那由声明决定。

        判据读**代码**（AST：函数体里的字符串常量与名字），不读散文 —— docstring 里
        出现工具名当例子不算硬编码（首版用裸 `in source` 扫全文，被自己的 doctest 例子
        误伤：那是**判据自身的构造缺陷**，改成 AST 后既咬得住真硬编码、又不误伤注释）。
        """
        import ast

        source = Path(
            "packages/application/run_orchestration/phase_capability_triggers.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        # docstring 节点集合（模块/类/函数**首条**语句里的那条字符串常量）。
        docstrings: set[int] = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                continue
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
        code_strings: set[str] = set()
        for node in ast.walk(tree):
            # 跳过 docstring：只取**可执行代码**里的字符串常量。
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
            ):
                code_strings.add(node.value)
        domain_names = sorted(
            item for item in code_strings if "literature" in item or "pmid" in item.lower()
        )
        assert domain_names == [], (
            "触发模块的**代码**里出现了领域能力名（判定被硬编码了）",
            domain_names,
        )


class TestTheFirstRoundTriggersTheSecond:
    """(b)① 触发臂：第二轮真跑，且输入**逐条可追到第一轮的具体产出**。"""

    def test_the_second_round_reads_the_first_rounds_pmids(self, mock_relay: str) -> None:
        """主判据：第二轮读取步的**证据**里逐字带着第一轮返回的 PMID。"""
        reads = _run(mock_relay)["reads"]
        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        second = tool_evidence(reads, phase=ROUND2_PHASE)
        assert _READ_REF in second, ("第二轮必须有检索读取的工具证据", sorted(second))
        read_evidence = second[_READ_REF]
        # 真实标识进证据链：读取步读的正是第一轮返回的那串 PMID。
        joined = " ".join(str(read_evidence[key]) for key in ("id", "source_ref", "artifact_id"))
        for pmid in MOCK_PMIDS:
            assert pmid in joined, (pmid, read_evidence)

    def test_the_declared_path_actually_carried_the_ids(self, mock_relay: str) -> None:
        """派生链的**第三跳**（`content.ids`）真的取到了东西：证据里两个 PMID 都在。"""
        reads = _run(mock_relay)["reads"]
        second = tool_evidence(reads, phase=ROUND2_PHASE)
        assert _SEARCH_REF in tool_evidence(reads, phase=ROUND1_PHASE), sorted(
            tool_evidence(reads, phase=ROUND1_PHASE)
        )
        assert _ARTIFACT_REF in second, (
            "第二轮必须先经读面读第一轮的制品（缺这一跳 ⇒ 派生是内存传递）",
            sorted(second),
        )
        read_evidence = second[_READ_REF]
        assert all(pmid in str(read_evidence["artifact_id"]) for pmid in MOCK_PMIDS), read_evidence

    def test_the_second_round_read_the_first_round_through_the_read_face(
        self, mock_relay: str
    ) -> None:
        """(c) 读面证据：`artifact.read` 的返回**内容** == 第一轮检索制品的字节。"""
        offline = OfflineNcbi()
        deps = assembled_deps(mock_relay, offline=offline)
        with TestClient(_app(deps)) as client:
            run = _start(client, PROTOCOL)
            reads = _read_chain(client, run)
            first = tool_evidence(reads, phase=ROUND1_PHASE)
            second = tool_evidence(reads, phase=ROUND2_PHASE)
            search_content = content_of(client, str(first[_SEARCH_REF]["artifact_id"]))
            artifact_content = content_of(client, str(second[_ARTIFACT_REF]["artifact_id"]))
            evidence_read = second[(_FROM_CANONICAL, TOOL_IDS["evidence.read"])]
            projection = content_of(client, str(evidence_read["artifact_id"]))
        assert search_content.get("ids") == list(MOCK_PMIDS), search_content
        # 内容逐字相等 ⇒ 第二轮读的就是第一轮那次检索的产出（经读面，不是内存）。
        assert artifact_content["content"] == search_content, artifact_content
        # 第二轮拿到的证据投影里含第一轮工具证据的 id（读面读数）。
        first_ids = {str(first[_SEARCH_REF]["id"])}
        projected = {str(item.get("id")) for item in projection.get("evidence", [])}
        assert first_ids <= projected, (sorted(first_ids), sorted(projected))


class TestWithoutAFIRSTRoundHitTheSecondIsSkippedNotFailed:
    """(b)② 不触发臂：零命中 ⇒ 读取步**带理由跳过**（run 照常成功，跳过可读）。"""

    def test_the_read_step_is_skipped_with_a_named_reason(self, mock_relay: str) -> None:
        """主判据：`run.completed` 的 `skipped` 逐字点名工具与字段。"""
        outcome = _run(mock_relay, pmids=())
        reads = outcome["reads"]
        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        facts = outcome["skipped"]
        assert facts, ("零命中时必须留下跳过事实（否则是静默降级）", reads.failures)
        reasons = [reason for fact in facts for reason in fact.get("reasons", [])]
        joined = " ".join(str(reason) for reason in reasons)
        assert TOOL_IDS["literature.read"] in joined, ("跳过理由必须点名工具", reasons)
        assert IDS_PATH in joined, ("跳过理由必须点名**声明的字段**", reasons)
        assert "requires_previous_ids=False" in joined, ("跳过理由必须说明是声明触发的", reasons)

    def test_the_skipped_call_left_no_tool_evidence(self, mock_relay: str) -> None:
        """跳过的机械形态：**不执行工具** ⇒ 没有 `literature_read` 工具证据、零读取请求。"""
        outcome = _run(mock_relay, pmids=())
        second = tool_evidence(outcome["reads"], phase=ROUND2_PHASE)
        assert _READ_REF not in second, ("跳过必须是不执行（不是执行了但没记）", sorted(second))
        assert _ARTIFACT_REF in second, (
            "读取步之前的读面跳不能跟着被吞——制品读取发生在跳过判定**之前**",
            sorted(second),
        )
        assert outcome["offline"].endpoints() == ["esearch.fcgi"], (
            "零命中只发一次检索请求（读取步一次都不该发）",
            outcome["offline"].endpoints(),
        )

    def test_the_two_arms_are_distinguishable_by_the_same_reading(self, mock_relay: str) -> None:
        """**判据能区分两臂**：同一次读数上，两组断言**互斥**（不可能同时判过同一组）。"""
        triggered = _run(mock_relay)
        skipped = _run(mock_relay, pmids=())
        triggered_second = tool_evidence(triggered["reads"], phase=ROUND2_PHASE)
        skipped_second = tool_evidence(skipped["reads"], phase=ROUND2_PHASE)
        # 臂的判别特征 1：读取证据在场 / 不在场。
        assert _READ_REF in triggered_second and _READ_REF not in skipped_second
        # 臂的判别特征 2：无跳过事实 / 有跳过事实。
        assert triggered["skipped"] == [] and skipped["skipped"] != []
        # 臂的判别特征 3：第二轮的交付物与证据**都**在（都跑完了），差别只在读取步。
        assert triggered["run"]["state"] == skipped["run"]["state"] == "SUCCEEDED"


class TestTheJudgeItselfBites:
    """(d) 反证两向：派生规则改坏 ⇒ 判红；读面抓手摘掉 ⇒ 第二轮判负。"""

    def test_breaking_the_declared_path_fails_and_names_it(self, mock_relay: str) -> None:
        """① `ids_from_previous` 指到不存在的路径 ⇒ FAILED 且判词点名那条路径。"""
        outcome = _run(mock_relay, calls=with_read_step("content.no_such_field"))
        reads = outcome["reads"]
        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        joined = " ".join(reads.failures)
        assert "content.no_such_field" in joined, (
            "派生规则改坏必须点名**哪条路径**取不到（否则无法诊断）",
            reads.failures,
        )
        assert outcome["offline"].endpoints() == ["esearch.fcgi"], outcome["offline"].endpoints()

    def test_removing_the_read_face_hook_makes_the_second_round_lose(self, mock_relay: str) -> None:
        """② 制品后缀选不中 ⇒ 第二轮**判负**（run FAILED，判词点名「选中数 ≠ 1」）。"""
        outcome = _run(mock_relay, calls=with_read_step(IDS_PATH, suffix="no_such_artifact"))
        reads = outcome["reads"]
        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        joined = " ".join(reads.failures)
        assert "exactly one" in joined and "no_such_artifact" in joined, (
            "摘掉读面抓手必须判负并点名缺的是哪个制品（不是静默跳过）",
            reads.failures,
        )

    def test_the_declared_run_is_not_failing_for_these_reasons(self, mock_relay: str) -> None:
        """反面对照：不破坏声明时**同一读数**里没有这些失败（本判据不空转）。"""
        reads = _run(mock_relay)["reads"]
        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        assert reads.failures == [], reads.failures

    def test_the_declared_call_set_covers_all_four_capabilities(self) -> None:
        """受判面的前提：四条能力的调用都在声明里（否则本判据在空集上恒真）。"""
        capabilities = {call.capability for call in all_calls()}
        assert capabilities == {
            "artifact.read",
            "evidence.read",
            "literature.search",
            "literature.read",
        }, sorted(capabilities)
        # 第二轮的证据确实属于 round2 的任务（不是被 round1 抢先跑掉的同一批）。
        assert task_of_evidence({"artifact_id": "tool-result:t1:op:literature_read"}) == "t1"
