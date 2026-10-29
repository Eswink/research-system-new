"""GOAL-20261029-100 EC-01：引用编号**注入提示词**，且与 References 的序号逐条相等。

**它补哪一格**（GOAL-099 `W-1` 的实测缺陷）：会话提示词里检索那一段原本逐条列的是
**裸标识 + 摘录**（`- 39284801: <title excerpt>`），**不带** `[1]`…`[n]` ⇒ 模型必须
**自己数**「这是第几条」才能写对引用编号。而当时的判据钉的是「编号顺序 = 去重后首次
出现顺序」—— 那是**汇编器侧**的映射一致性。「模型数得对不对」不可判 ⇒ 手稿的引用标记
可以系统性错位而判据全绿。

**三向判据（缺一不算）**：

1. **正向**：提示词里每条**可引用**来源带 `[n]`，且 `n` 与 References 的序号逐条相等
   —— 两侧各算一遍是**两份独立实现**（汇编器读制品字节、渲染器读视图），相等才是同源；
2. **反证（编造编号）**：模型写一个大于条目总数的编号 ⇒ 汇编器点名判红；
3. **反证（改回裸标识）**：把注入拿掉、渲染器回到裸标识 ⇒ 第 1 条判据必须判红
   —— 这条证明判据**真的在看注入**，而不是只在看汇编器自己的编号（否则它可以一直绿）。

**零出网 / 零模型**：夹具是 `FakeArtifactStore` + 手搓视图/证据，全部离线。
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.application.deliverable.references import (
    ReferenceTable,
    citation_mark,
    numbered_records,
    reference_table,
)
from packages.application.run_orchestration.retrieval_context import (
    RetrievalContextView,
    RetrievalEntry,
)
from packages.application.run_orchestration.retrieval_prompt import (
    NOT_CITABLE_MARK,
    PROMPT_SECTION_TITLE,
    render_retrieval_prompt,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState
from packages.domain.evidence import Evidence
from packages.domain.memory import ContextSnapshot

_RUN = "run-cite-0001"
_TASK = "task-cite-0001"

#: 三条**完整著录**的记录（作者 / 刊名 / 年份齐备 ⇒ 都进 References）。
_RECORDS: tuple[dict[str, Any], ...] = (
    {
        "pmid": "39284801",
        "title": "ENCORE: a practical implementation",
        "journal": "Nat Commun",
        "year": "2024",
        "authors": ["Hoffmann C"],
    },
    {
        "pmid": "40601758",
        "doi": "10.1371/journal.pcbi.1013215",
        "title": "Fundamentals of FAIR biomedical data analyses",
        "journal": "PLoS Comput Biol",
        "year": "2025",
        "author_string": "Kanitz A, Gursoy G",
    },
    {
        "pmid": "41111111",
        "title": "A third record",
        "journal": "J Third",
        "year": "2023",
        "authors": ["Third T"],
    },
)


def _store(*record_groups: tuple[dict[str, Any], ...]) -> FakeArtifactStore:
    """逐组种 tool-result 制品（同上游：检索链两步各落一份）。"""
    store = FakeArtifactStore()
    for index, records in enumerate(record_groups, start=1):
        artifact_id = f"tool-result:{_TASK}:literature_read:{index}"
        content = json.dumps({"articles": list(records)}, sort_keys=True).encode("utf-8")
        store.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/json",
                created_by="system:tool-registry",
                classification="tool_result",
            ),
            content,
        )
        store.mark(artifact_id, ArtifactState.VERIFIED)
    return store


def _evidence(*indexes: int) -> tuple[Evidence, ...]:
    return tuple(
        Evidence(
            id=f"evidence:{_TASK}:{index}",
            source_ref=f"tool:europe_pmc:literature.read:{index}",
            content_digest="sha256:" + "0" * 64,
            extracted_by="system:tool-evidence",
            artifact_id=f"tool-result:{_TASK}:literature_read:{index}",
            run_id=_RUN,
        )
        for index in indexes
    )


def _view(entries: tuple[RetrievalEntry, ...]) -> RetrievalContextView:
    return RetrievalContextView(
        snapshot=ContextSnapshot(retrieval_digest="sha256:" + "0" * 64),
        entries=entries,
        run_id=_RUN,
    )


def _entry(identifier: str, *, citable: bool = True, tag: str = "e1") -> RetrievalEntry:
    return RetrievalEntry(
        evidence_id=f"evidence:{tag}",
        artifact_id=f"tool-result:{tag}",
        identifier=identifier,
        title=f"title of {identifier}",
        shown=f"title of {identifier}",
        truncated=False,
        citable=citable,
    )


def _prompt_marks(prompt: str) -> tuple[tuple[int, str], ...]:
    """提示词检索段 → `(编号, 标识)`（判据自己解析，不 import 渲染器的内部结构）。"""
    found: list[tuple[int, str]] = []
    for line in prompt.splitlines():
        match = re.match(r"^- \[(\d+)\] (\S+?)(?: \[truncated\])?: ", line)
        if match:
            found.append((int(match.group(1)), match.group(2)))
    return tuple(found)


class TestThePromptCarriesTheNumberTheReferencesUse:
    """① 正向：提示词里每条可引用来源带 `[n]`，与 References 序号**逐条相等**。"""

    def test_every_citable_source_carries_its_reference_number(self) -> None:
        """两侧**各自**算一遍：汇编器读制品字节，渲染器读视图 —— 相等才是同源。"""
        store = _store(_RECORDS)
        table = reference_table(store, _evidence(1))
        view = _view(
            tuple(
                _entry(entry.identifier, tag=f"e{index}")
                for index, entry in enumerate(table.entries, start=1)
            )
        )
        prompt = render_retrieval_prompt(view)

        prompt_marks = _prompt_marks(prompt)
        reference_numbers = re.findall(r"^(\d+)\. ", table.markdown(), re.MULTILINE)
        assert len(prompt_marks) == len(table.entries) == 3, (prompt, table.markdown())
        assert [mark for mark, _ in prompt_marks] == [int(n) for n in reference_numbers]
        # **逐条相等**：提示词第 k 条的编号所对的标识，就是 References 第 k 条的那个标识。
        for (number, identifier), ref_number, entry in zip(
            prompt_marks, reference_numbers, table.entries, strict=True
        ):
            assert number == int(ref_number), (prompt_marks, reference_numbers)
            assert identifier == entry.identifier, (identifier, entry.identifier)

    def test_the_identifier_to_number_map_agrees_across_the_two_sides(self) -> None:
        """同源判据的**更强形态**：标识→编号的映射两侧相同（不是「集合相同」）。"""
        store = _store(_RECORDS)
        table = reference_table(store, _evidence(1))
        view = _view(
            tuple(_entry(entry.identifier, tag=f"e{i}") for i, entry in enumerate(table.entries, 1))
        )
        prompt_map = {
            identifier: number
            for number, identifier in _prompt_marks(render_retrieval_prompt(view))
        }
        reference_map = {entry.identifier: index for index, entry in enumerate(table.entries, 1)}
        assert prompt_map == reference_map, (prompt_map, reference_map)

    def test_a_duplicate_record_keeps_the_same_number(self) -> None:
        """重复出现的记录**不占新编号**（检索链两步各落一份 ⇒ 模型看到重复行）。"""
        store = _store(_RECORDS, _RECORDS)
        table = reference_table(store, _evidence(1, 2))
        duplicated = list(_RECORDS) * 2
        view = _view(
            tuple(_entry(record["pmid"], tag=f"e{i}") for i, record in enumerate(duplicated))
        )
        marks = _prompt_marks(render_retrieval_prompt(view))
        assert marks == ((1, "39284801"), (2, "40601758"), (3, "41111111")) * 2, marks
        assert len(table.entries) == 3

    def test_an_id_only_record_takes_no_number(self) -> None:
        """`ids[]` 形状**不占编号**（它永远进不了 References ⇒ 占号会让其后整体错位）。"""
        view = _view((
            _entry("artifact:no-metadata", citable=False),
            _entry("39284801"),
            _entry("40601758"),
        ))
        prompt = render_retrieval_prompt(view)
        assert _prompt_marks(prompt) == ((1, "39284801"), (2, "40601758")), prompt
        # 它仍然**逐条列出**（可见，只是不编号）。
        assert "artifact:no-metadata" in prompt
        assert NOT_CITABLE_MARK in prompt

    def test_the_section_title_says_number_not_identifier(self) -> None:
        """标题逐字：模型要「按编号引用」，而编号现在就写在它眼前。"""
        assert PROMPT_SECTION_TITLE == ("RETRIEVED SOURCES (system-fetched; cite these by number)")

    def test_the_shared_numbering_rule_is_one_function(self) -> None:
        """编号权威只有一个：`numbered_records`（去重后首次出现、从 1 起）。"""
        assert numbered_records(("b", "a", "b", "", "c")) == ((1, "b"), (2, "a"), (3, "c"))
        assert citation_mark(1) == "[1]" and citation_mark(12) == "[12]"


class TestTheNegativeArmsAreReal:
    """② 反证（编造编号）＋ ③ 反证（改回裸标识）—— 两条都按在**真文件**上。"""

    def test_a_mark_beyond_the_highest_number_is_refused_by_name(self) -> None:
        """② 模型写了一个大于条目总数的编号 ⇒ 汇编器**点名**判红。"""
        from packages.application.deliverable.manuscript import (
            MANUSCRIPT_KEYS,
            ManuscriptError,
            validate_manuscript,
        )

        table = ReferenceTable(
            entries=tuple(_table_entry(identifier) for identifier in ("1", "2", "3"))
        )
        sections = {key: "Body without numerals [1][2][3]" for key in MANUSCRIPT_KEYS}
        validate_manuscript(sections, table)  # 三条都引 ⇒ 通过
        beyond = dict(sections)
        beyond["results"] = "Body text, but the mark is [4]"
        with pytest.raises(ManuscriptError) as raised:
            validate_manuscript(beyond, table)
        assert "[4]" in str(raised.value), str(raised.value)

    def test_removing_the_injection_makes_the_number_consistency_red(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """③ **改回裸标识** ⇒ 第 ① 组判据必须判红（证明它真的在看注入）。

        做法：读**真文件** `retrieval_prompt.py`，把注入那两行按源码文本还原成裸标识形态，
        写进 `tmp_path` 的一个模块里执行，再拿它的渲染结果跑与 ① 完全相同的比较。
        判据**不**接受「渲染器没注入」这个形态 —— 一旦真的回退，这里必须红。
        """
        import importlib.util
        import sys
        from pathlib import Path

        source_path = Path("packages/application/run_orchestration/retrieval_prompt.py")
        source = source_path.read_text(encoding="utf-8")
        # 锚**整条语句**而不是它的某一种排版：格式化器会把三元表达式折行/并成一行，
        # 按「当初怎么写的那几行」定位会让按压随格式化一起失效（本文件踩过一次）。
        injected = 'prefix = f"[{numbers[identifier]}] " if identifier in numbers'
        assert injected in source, "先决条件：注入那一段必须逐字在树（否则本按压测不到东西）"
        line = next(item for item in source.splitlines() if injected in item)
        reverted = source.replace(line, '        prefix = ""')
        # 断言「按压后的源码**不再**注入编号」—— 否则下面可能只是把同一段代码跑一遍。
        assert 'f"[{numbers[identifier]}] "' not in reverted

        module_path = tmp_path / "retrieval_prompt_reverted.py"
        module_path.write_text(reverted, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("retrieval_prompt_reverted", module_path)
        assert spec is not None and spec.loader is not None
        reverted_module = importlib.util.module_from_spec(spec)
        sys.modules["retrieval_prompt_reverted"] = reverted_module
        spec.loader.exec_module(reverted_module)

        view = _view((_entry("39284801"), _entry("40601758", tag="e2")))
        store = _store(_RECORDS)
        table = reference_table(store, _evidence(1))
        reference_map = {entry.identifier: index for index, entry in enumerate(table.entries, 1)}

        reverted_marks = _prompt_marks(reverted_module.render_retrieval_prompt(view))
        prompt_map = {identifier: number for number, identifier in reverted_marks}
        # 裸标识形态下**没有一条**带编号 ⇒ 映射为空 ⇒ 与 References 的映射不等 ⇒ ① 判红。
        assert reverted_marks == (), reverted_marks
        assert prompt_map != reference_map, (
            "按压失败：改回裸标识之后，提示词—References 编号一致判据**仍然绿** —— "
            "那说明它没在看注入",
            prompt_map,
            reference_map,
        )


def _table_entry(identifier: str) -> Any:
    from packages.application.deliverable.references import ReferenceEntry

    return ReferenceEntry(
        identifier=identifier,
        authors=("A A",),
        title=f"T{identifier}",
        journal="J",
        year="2001",
    )
