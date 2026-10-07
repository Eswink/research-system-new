"""三轮循环 e2e 的装配支持（GOAL-20261008-034 EC-01；规模门：判据文件另放）。

**与两轮支持（`two_round_loop_support.py`）的关系**：同一批产品对象、同一份协议族，
差别只在**轮次声明**——本模块给同一条链装上 `RoundLoop`（max_rounds / 判据），
并让每一轮的**检索词**随轮次变化（否则后轮拿不到新标识 ⇒ 第一轮就收敛，测不出多轮）。

**为什么需要「每轮换检索词」**：停止判据是「本轮无新标识 ⇒ 停」。若三轮都用同一个词，
离线响应每次都返回同一批 PMID ⇒ 第 2 轮就判「无新标识」而停 —— 那**是判据在正确工作**，
但测不到「≥3 轮」。⇒ 让检索词带轮次（声明面新增一个 `arguments_from_input` 的
备选：`fixed_arguments` 三元组按轮替换），三轮因此各返回一批新标识。

**如实边界**：本模块**不**声称「模型读懂了上一轮」（交付物契约只判产物存在与来源覆盖）；
三轮之后**不**声称收敛（那是本模块 `max_rounds` 之外的语义）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from packages.application.run_orchestration.round_loop import RoundLoop
from packages.application.run_orchestration.round_loop_runner import round_specs
from tests.e2e.two_round_loop_support import (
    CANONICAL_ID,
    IDS_PATH,
    NCBI_ID,
    SEARCH_ARTIFACT_SUFFIX,
    TOOL_IDS,
    all_calls,
    assembled_deps,
)

#: 三轮共用**同一个** phase（循环就是「这一组重复跑」）——两轮协议里是两个不同 phase，
#: 而**循环**语义是同一段重复，所以这里只取 round1 那一支。
LOOPED_PHASE = "round1"
#: 每轮的检索词（带轮次 ⇒ 每轮离线响应返回**不同**的 PMID ⇒ 有「新标识」）。
QUERIES: tuple[str, ...] = ("multi-round-1", "multi-round-2", "multi-round-3")
#: 每轮离线检索返回的标识（与 `QUERIES` 一一对应）。
ROUND_PMIDS: tuple[tuple[str, ...], ...] = (
    ("39500001", "39500002"),
    ("39500011", "39500012"),
    ("39500021", "39500022"),
)


class RoundsOfflineNcbi:
    """离线 NCBI：按**检索词**决定返回哪一批 PMID（每轮因此有不同标识）。

    与 `OfflineNcbi` 同一形态（`httpx.MockTransport`），差别只在「按 query 分派」——
    那是多轮夹具的必需能力（单一响应会让第 2 轮就收敛）。
    """

    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []

    def client(self) -> Any:
        import httpx

        def handler(request: httpx.Request) -> httpx.Response:
            endpoint = request.url.path.rsplit("/", 1)[-1]
            query = str(request.url.params.get("term", ""))
            self.requests.append((endpoint, str(request.url.query)))
            if endpoint == "esearch.fcgi":
                index = QUERIES.index(query) if query in QUERIES else 0
                pmids = ROUND_PMIDS[index]
                return httpx.Response(
                    200,
                    json={"esearchresult": {"count": str(len(pmids)), "idlist": list(pmids)}},
                )
            if endpoint == "efetch.fcgi":
                pmid = str(request.url.params.get("id", "")).split(",")[0]
                return httpx.Response(200, content=_efetch_xml(pmid))
            return httpx.Response(404, text="not found")

        return httpx.Client(transport=httpx.MockTransport(handler))

    def endpoints(self) -> list[str]:
        return [endpoint for endpoint, _ in self.requests]


def _efetch_xml(pmid: str) -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8"?><PubmedArticleSet><PubmedArticle>'
        b"<MedlineCitation><PMID>" + pmid.encode("ascii") + b"</PMID><Article>"
        b"<ArticleTitle>Multi-round continuation</ArticleTitle>"
        b"<Journal><Title>J Multi Round</Title></Journal></Article>"
        b"</MedlineCitation></PubmedArticle></PubmedArticleSet>"
    )


def looped_calls(round_index: int) -> tuple[Any, ...]:
    """该轮的运行链声明：检索词换成**本轮**的（其余逐字不变）。

    检索词原本来自 `arguments_from_input`（声明输入制品里的字段）——本轮改成
    **本轮的固定量**（每轮不同）。这是「轮次之间的差异由**声明**承担」的具体形态：
    改的是声明的调用参数，不是代码里的「如果就」。
    """
    search_call = TOOL_IDS["literature.search"]
    artifact_call = TOOL_IDS["artifact.read"]
    query = QUERIES[min(round_index, len(QUERIES)) - 1]
    out: list[Any] = []
    for call in all_calls():
        if call.tool_id == search_call:
            out.append(
                replace(
                    call,
                    arguments_from_input=(),
                    fixed_arguments={**dict(call.fixed_arguments), "query": query},
                )
            )
        elif call.tool_id == artifact_call and round_index > 1:
            # **多轮必需**：三轮起同一后缀会匹配多份（前几轮的产出都在）⇒ 收窄到
            # **上一轮**那一份（`artifact_from_previous_round`；执行期才知道是哪个任务）。
            out.append(replace(call, artifact_from_previous_round=True))
        else:
            out.append(call)
    return tuple(out)


def deps_with_loop(mock_relay_url: str, *, offline: RoundsOfflineNcbi, max_rounds: int = 3) -> Any:
    """装配面：run-ready deps + 循环声明（`calls_by_round` 按轮给出调用声明）。

    `max_rounds=3` ⇒ 三轮；`calls_by_round` 逐轮给出该轮的检索词 ⇒ 每轮有不同的检索
    响应 ⇒ 每轮有新标识（否则第 2 轮就「无新标识」而停 —— 那是判据在正确工作，
    测不到多轮）。
    """
    from packages.application.run_orchestration.service import RunOrchestrationService

    deps = assembled_deps(mock_relay_url, offline=offline)  # type: ignore[arg-type]
    service = deps.runs
    assert service is not None
    loop = RoundLoop(
        phases=(LOOPED_PHASE,),
        max_rounds=max_rounds,
        calls_by_round=tuple(looped_calls(index) for index in range(1, max_rounds + 1)),
    )
    base = service._deps
    return replace(
        deps,
        runs=RunOrchestrationService(
            replace(
                base,
                round_loops=(loop,),
                capabilities=replace(base.capabilities, calls=looped_calls(1)),
            )
        ),
    )


__all__ = [
    "CANONICAL_ID",
    "IDS_PATH",
    "LOOPED_PHASE",
    "NCBI_ID",
    "QUERIES",
    "ROUND_PMIDS",
    "SEARCH_ARTIFACT_SUFFIX",
    "TOOL_IDS",
    "RoundsOfflineNcbi",
    "deps_with_loop",
    "looped_calls",
    "round_specs",
]
