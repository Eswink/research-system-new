"""GOAL-20261008-035 EC-01 判据：两维覆盖判定与读面 claim↔evidence 关系**同一次实跑**成立。

靶子（EC-01 (c)）：实跑一条**两维都声明**的出厂合约（`real_retrieval_deliverable`：
`minimum_sources: 1` + `minimum_retrieved_sources: 1`，被 `real_retrieval_research_v1.yaml`
使用），要求两件事在同一次 run 上**同时成立**：

- 覆盖判据**判过**，且它的判词在**读面**逐字读出两条事实（计数维与性质维各自的数）
  ——「run 是 SUCCEEDED」是间接推断，不算读出判词；
- 读面（`GET /runs/{id}/claims`）能读到 claim↔evidence 的**关系**，且关系指向的证据里
  有**系统取得**（`RETRIEVED`）的那几条（承 `MEM: evidence-read-face-claim-relation`：
  只登记证据不挂 relation ⇒ 判据绿而读面空）。

为什么此前读不出：`GateOutcome.evaluations`（逐条判据 + 逐字判词）只在**被拒**时经失败
消息可见（`gate_rejection_reason`），通过的路径上判词**无处可读**（`ReviewFinding` /
`Decision` 也从不持久化）。本轮把它落成 canonical 记录（`ReviewFindingStore` +
`GET /runs/{id}/reviews`，EC-01 的产品面改动），通过与被拒**两种结局都记** —— 反证臂
因此读同一张面。

**为什么是独立读面而不是把判词塞进事件 payload**（实测的两处既有判据，两处都不放宽）：
`test_vertical_slice_happy_path.py` 的 `test_artifact_content_is_not_in_domain_json` 断言
事件 payload 里不得出现结构化输出的键（`analysis_report`），而 `ARTIFACT_EXISTS` 的判词
**逐字点名合约声明的制品名**；`test_idempotency.py` 又断言制品条数精确值。⇒ 判词进事件面
或进制品面都会撞既有断言。落库 + 只读路由两处都不动。

**记录，不是重算**：读面读的是**求值点落下的原文**。派生式读面（读取时按 canonical 事实
重跑判据）在一扇从未求值的门上照样会给出结论 —— 那无法区分「门判过」与「门根本没跑」。

反证两向（EC-01 (d)，**两维都要被单独触发**，不是只看总数）：

- ① 只抬**计数**维（`minimum_sources` 抬到实际值之上）⇒ 判负、判词点名计数，
  且**不提** retrieved；
- ② 只打掉**性质**维（不接检索能力步 ⇒ 检索来源数为 0；声明输入仍满足计数维）⇒
  判负、判词点名 retrieved，且**同时**读出计数维已满足；
- ②的补强（换阈值不换事实）：检索照跑、只抬性质维阈值 ⇒ 判负同样只由性质维给出。

第 ② 条与既有 `test_run_chain_retrieval_offline.py` 的反证臂**同机制、不同判据**：
那一条判「run 收敛 `FAILED` + 失败消息里有 retrieved」；本文件判**读面**上的逐条事实
（哪一维满足 / 哪一维不满足 / 被点名的维度名称）+ 读面关系里确实没有 `RETRIEVED` 来源。
"""

from __future__ import annotations

import re
from typing import Any

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.live_run_support import (
    ncbi_run_chain_provider,
    offline_ncbi_http,
    openhands_deps,
    run_failures,
    start_run,
    with_run_chain_capabilities,
)
from tests.e2e.test_ec03_real_runtime_offline_chain import (
    _RETRIEVAL_PROTOCOL,
    _read_chain,
    mock_relay,
)

__all__ = ["mock_relay"]

#: 两维都声明的出厂合约（`minimum_sources` + `minimum_retrieved_sources` 各一条）。
_TWO_DIMENSIONAL_CONTRACT = "real_retrieval_deliverable"
_COVERAGE = "EVIDENCE_COVERAGE"
_RETRIEVED = "RETRIEVED"
#: 判过的两维判词形态（域函数 `_evaluate_evidence_coverage` 的原文）。
_COVERAGE_PASS = re.compile(r"(\d+) >= (\d+) sources; (\d+) >= (\d+) retrieved")
#: 性质维判负的判词形态：**两个维度的数都在**（计数维已满足，性质维不满足）。
_COVERAGE_NATURE = re.compile(r"(\d+) < (\d+) retrieved sources \((\d+) >= (\d+) sources\)")
#: 计数维判负的判词形态（先判计数 ⇒ 判词里不出现 retrieved）。
_COVERAGE_COUNT = re.compile(r"(\d+) < (\d+) sources")


def _reviews(client: TestClient, run_id: str) -> list[dict[str, Any]]:
    """该 run 的验收结论（经**产品读面** `GET /runs/{id}/reviews` 取，不经内部对象）。"""
    response = client.get(f"/runs/{run_id}/reviews")
    assert response.status_code == 200, response.text
    return list(response.json())


_COVERAGE_PREFIX = f"{_COVERAGE}: "


def _coverage_reason(review: dict[str, Any]) -> str:
    """结论里**那一条**覆盖判据的判词（读面原文去掉判据名前缀；本合约只判一条 ⇒ 恰一条）。

    前缀断言是载重的：没有它，读者从读面看不出「这句话是哪条判据说的」。
    """
    lines = [line for line in review["findings"] if line.startswith(_COVERAGE_PREFIX)]
    assert len(lines) == 1, review
    return str(lines[0][len(_COVERAGE_PREFIX) :])


def _retrieved_ids(reads: Any) -> set[str]:
    """读面上**系统取得**的证据 id（`source_trust_label` 是既有读面字段）。"""
    return _by_trust(reads, _RETRIEVED)


def _by_trust(reads: Any, label: str) -> set[str]:
    """读面上某一类性质（`USER_PROVIDED` / `GENERATED` …）的证据 id。"""
    return {item["id"] for item in reads.evidence if item["source_trust_label"] == label}


def _related_evidence(claims: dict[str, Any]) -> set[str]:
    """读面 claim 图里**被关系指向**的证据 id（没有 relation 的 claim 不归属任何 run）。"""
    return {
        relation["evidence_id"] for claim in claims["claims"] for relation in claim["relations"]
    }


def _assert_count_reads_the_sources(count: int, reads: Any) -> None:
    """计数维读的是**非自产来源**：读面每条证据要么是检索来源、要么是声明输入，要么是
    本任务自产的制品 —— 判词里的 `count` 恰等于前两类之和（自产那一类**不**计入）。

    这条把「计数维」的语义钉在读面上（不是重算一遍判据）：一个把自产制品也算进去的实现
    会让 `count` 比这里大 1；一个把检索来源漏掉的实现会让它小若干。
    """
    retrieved = _retrieved_ids(reads)
    provided = _by_trust(reads, "USER_PROVIDED")
    self_produced = {item["id"] for item in reads.evidence} - retrieved - provided
    assert len(self_produced) == 1, (sorted(self_produced), reads.evidence)
    assert count == len(retrieved) + len(provided), (count, sorted(retrieved), sorted(provided))


def _raise_minimum(deps: Any, field: str, value: int) -> None:
    """反证预置：把两维合约某一维的阈值抬到实际值之上。

    只动 `preflight_override` 的目录快照（与 `live_run_support.declare_second_artifact`
    同一手法）：不写配置文件、不改产品代码，反证臂与主干共用同一份合约的**其余部分**。
    """
    from dataclasses import replace

    from packages.domain.enums import AcceptanceCriterionType

    context = deps.preflight_override
    assert context is not None
    catalog = context.catalog
    contracts = dict(catalog.task_contracts)
    contract = contracts[_TWO_DIMENSIONAL_CONTRACT]
    crit_type = AcceptanceCriterionType.EVIDENCE_COVERAGE
    raised = False
    criteria = []
    for criterion in contract.acceptance_criteria:
        if criterion.type is crit_type and not raised:
            criteria.append(replace(criterion, **{field: value}))
            raised = True
        else:
            criteria.append(criterion)
    assert raised, [item.type for item in contract.acceptance_criteria]
    contracts[_TWO_DIMENSIONAL_CONTRACT] = replace(contract, acceptance_criteria=criteria)
    deps.preflight_override = replace(context, catalog=replace(catalog, task_contracts=contracts))


def _wired_deps(mock_relay: str, calls: list[str]) -> Any:
    """能力步**接上**的装配（离线 mock NCBI 响应；检索真的执行两步）。"""
    deps = openhands_deps(mock_relay, map_tools=False)
    provider = ncbi_run_chain_provider(deps, http_client=offline_ncbi_http(calls))
    with_run_chain_capabilities(deps, provider)
    return deps


def test_two_dimensional_coverage_passes_and_both_facts_are_readable(mock_relay: str) -> None:
    """EC-01 (c) 主干：两维判过 + 判词逐字可读 + 读面 claim↔evidence 关系成立。"""
    http_calls: list[str] = []
    with TestClient(create_app(_wired_deps(mock_relay, http_calls))) as client:
        run = start_run(client, _RETRIEVAL_PROTOCOL)
        reads = _read_chain(client, run)
        reviews = _reviews(client, run["id"])
        claims = client.get(f"/runs/{run['id']}/claims").json()

    assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
    assert http_calls == ["esearch.fcgi", "efetch.fcgi"], http_calls
    assert len(reviews) == 1, reviews
    review = reviews[0]
    assert review["review_type"] == "acceptance_gate", review
    assert review["contract_id"] == _TWO_DIMENSIONAL_CONTRACT, review
    assert review["verdict"] == "PASS", review
    assert str(review["reviewed_by"]).startswith("gate:"), review
    assert review["task_id"] and review["reviewed_at"], review

    # 判词在**读面**逐字读出两条事实（不重算判据、不用 run 终态反推）。
    matched = _COVERAGE_PASS.fullmatch(_coverage_reason(review))
    assert matched is not None, review
    count, minimum, retrieved, min_retrieved = (int(g) for g in matched.groups())
    assert (minimum, min_retrieved) == (1, 1), review
    assert count >= minimum and retrieved >= min_retrieved, review
    # 读面自洽（两条缺一不可）：判词里的性质维读数 = 读面上 `RETRIEVED` 的证据条数；
    # 且它是**正数** —— 否则下面那条子集断言会在空集上恒真（「登记过」冒充「有关系」）。
    assert retrieved == len(_retrieved_ids(reads)), (review, reads.evidence)
    assert retrieved >= 1, review
    _assert_count_reads_the_sources(count, reads)

    # 读面关系：claim↔evidence 真的挂上了，且指向关系里的证据含检索来源。
    assert claims["degraded"] is False, claims
    related = _related_evidence(claims)
    assert _retrieved_ids(reads) <= related, (sorted(_retrieved_ids(reads)), sorted(related))
    verified = [claim for claim in claims["claims"] if claim["status"] == "VERIFIED"]
    assert verified, claims
    assert "claim.verified" in reads.types, reads.types


def test_count_dimension_alone_rejects_and_never_names_retrieved(mock_relay: str) -> None:
    """EC-01 (d)①：只抬计数维 ⇒ 判负点名计数，且判词里**不提** retrieved（维不互相顶替）。"""
    http_calls: list[str] = []
    deps = _wired_deps(mock_relay, http_calls)
    _raise_minimum(deps, "minimum_sources", 99)
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _RETRIEVAL_PROTOCOL)
        failures = run_failures(client, run["id"])
        reviews = _reviews(client, run["id"])

    assert run["state"] == "FAILED", (run, failures)
    assert http_calls == ["esearch.fcgi", "efetch.fcgi"], http_calls
    assert len(reviews) == 1, reviews
    assert reviews[0]["verdict"] == "REJECT", reviews[0]
    line = _coverage_reason(reviews[0])
    matched = _COVERAGE_COUNT.fullmatch(line)
    assert matched is not None, line
    assert int(matched.group(2)) == 99, line
    # 计数维单独成立：判词里没有性质维的字样（性质维此时是**满足**的）。
    assert "retrieved" not in line, line
    # 同一份判词也在失败消息里（被拒路径的既有读法与新增读面同源，不各说一套）。
    assert any("< 99 sources" in message for message in failures), failures


def test_nature_threshold_alone_rejects_with_count_read_as_satisfied(mock_relay: str) -> None:
    """EC-01 (d)②的**同源补强**：检索照跑、计数维不变，**只**抬性质维阈值 ⇒ 判负点名它。

    与下一条的分工：下一条打掉的是**检索来源本身**（0 条）；这一条把**接线留住**、只抬
    性质维阈值 ⇒ 读面关系里检索来源仍在，判负却只由性质维给出。两条一起把「性质维是
    独立判据（不是总数换了个说法）」钉死：一条换掉事实、一条换掉阈值，结论必须是同一个。
    """
    calls: list[str] = []
    deps = _wired_deps(mock_relay, calls)
    _raise_minimum(deps, "minimum_retrieved_sources", 99)
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _RETRIEVAL_PROTOCOL)
        reads = _read_chain(client, run)
        reviews = _reviews(client, run["id"])
        claims = client.get(f"/runs/{run['id']}/claims").json()

    assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
    assert calls == ["esearch.fcgi", "efetch.fcgi"], calls
    assert _retrieved_ids(reads), reads.evidence  # 检索真的发生过，来源仍在读面上
    assert _retrieved_ids(reads) <= _related_evidence(claims), claims
    line = _coverage_reason(reviews[0])
    matched = _COVERAGE_NATURE.fullmatch(line)
    assert matched is not None, line
    retrieved, min_retrieved, count, minimum = (int(g) for g in matched.groups())
    assert min_retrieved == 99 and retrieved < min_retrieved, line
    assert count >= minimum, line  # 计数维同一句里读出已满足（两维不互相顶替）


def test_nature_dimension_alone_rejects_while_count_stays_satisfied(mock_relay: str) -> None:
    """EC-01 (d)②：只打掉性质维 ⇒ 判负点名 retrieved，计数维在同一判词里读出已满足。"""
    deps = openhands_deps(mock_relay, map_tools=False)  # 不接能力步 ⇒ 检索来源数为 0
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _RETRIEVAL_PROTOCOL)
        reads = _read_chain(client, run)
        reviews = _reviews(client, run["id"])
        claims = client.get(f"/runs/{run['id']}/claims").json()

    assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
    assert _retrieved_ids(reads) == set(), reads.evidence
    assert len(reviews) == 1, reviews
    assert reviews[0]["verdict"] == "REJECT", reviews[0]
    line = _coverage_reason(reviews[0])
    matched = _COVERAGE_NATURE.fullmatch(line)
    assert matched is not None, line
    retrieved, min_retrieved, count, minimum = (int(g) for g in matched.groups())
    assert retrieved == 0, line
    # 判负**只**可能来自性质维：计数维在同一句判词里读出已满足。
    assert count >= minimum, line
    # 读面关系：声明输入的来源仍挂在 claim 上（少的是**检索**那一类，不是关系本身）。
    assert _related_evidence(claims), claims


def test_unconfigured_store_and_unknown_run_are_named_not_silently_empty() -> None:
    """读面边界（EC-01 的诚实口径）：**没接存储 ≠ 没有结论**，未知 run ≠ 空结论。

    没有这一条，一个「读不到就回 `[]`」的实现会与「门真的没判过」在读面上长得一样 ——
    而这两个事实的处置完全相反（前者是装配缺失、后者是研究没跑）。
    """
    from dataclasses import replace

    from services.api.composition import assemble
    from services.api.settings import ApiSettings

    deps = assemble(ApiSettings(db_path=":memory:"))
    try:
        # 生产组合根：写面（编排）与读面（API）**同一实例**（否则写进去的读不到）。
        assert deps.review_findings is not None
        assert deps.runs is not None
        assert deps.runs._deps.review_findings is deps.review_findings
        with TestClient(create_app(deps)) as client:
            assert client.get("/runs/does-not-exist/reviews").status_code == 404
        bare = replace(deps, review_findings=None)
        with TestClient(create_app(bare)) as client:
            response = client.get("/runs/any-run/reviews")
        assert response.status_code == 503, response.text
        assert "not configured" in response.text, response.text
    finally:
        deps.close()
