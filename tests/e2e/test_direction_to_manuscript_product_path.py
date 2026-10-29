"""GOAL-20261028-099 EC-04：**手稿从产品入口产出**（不是从单元缝里）。

**它补哪一格**（本轮的核心教训，承 GOAL-097 EC-02）：「测试全绿」与「产品能用」是两件事。
`deliverable/manuscript.py` 与 `references.py` 的实现完备、24+22 条单元判据全绿 ——
但那条装配路径若**只被测试调用**，产品上就仍然只产四节中文报告。本文件因此**只经产品入口**
取证：`TestClient(create_app(deps))` → `POST /projects/{id}/runs` → 读面取回
`manuscript.md` 的**内容字节**。

**判什么**（每条独立取证）：

1. **八相全落库、run 收敛 `SUCCEEDED`**：八件产物分属不同任务；
2. **`manuscript.md` 真的在 canonical 里**，且它的字节是 IMRaD 形状（Abstract + 六个
   编号节 + References），References 是**真的** Vancouver 行（作者 / 刊名 / 年份都来自
   本 run 落盘的工具结果字节）；
3. **正文无数字**（引用标记与汇编器写的抬头/标题除外）—— 模型那块面的结构事实；
4. **未开手稿 ⇒ 报告逐字节不变**（本条是零回归夹具）：同一个装配关掉 `manuscript`
   开关 ⇒ 只有 `research_report.md`，且它与开着手稿那次**逐字节相同**（报告不因手稿
   而改变），同时 `manuscript.md` **不在**库里。

**如实边界**：mock 中转站 + 离线 Europe PMC + 真容器实验。它证的是**产品装配与判据**；
真实模型条件下的八相由后续 live 判据承担（本 GOAL 的 EC-02 只要求结构面）。
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from services.api.app import create_app
from tests.e2e.direction_to_manuscript_support import (
    OUTPUT_NAMES,
    PHASES,
    PROTOCOL,
    VARIANT_A,
    ManuscriptRelayFixture,
    deps_for,
)

pytestmark = pytest.mark.requires_docker

_MANUSCRIPT_HEADINGS = (
    "## Abstract",
    "## 1. Introduction",
    "## 2. Related Work",
    "## 3. Methods",
    "## 4. Results",
    "## 5. Discussion",
    "## 6. Conclusion",
)


def _run_once(deps: Any, key: str) -> dict[str, Any]:
    """经**产品入口**跑一次 run，并把读面上的事实取回来（只经既有路由）。"""
    from fastapi.testclient import TestClient

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": PROTOCOL},
            headers={"Idempotency-Key": key},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        # `client.get(...).json()` 是 `Any` ⇒ 显式收成 dict（strict mypy 下 returning Any 是错）
        run: dict[str, Any] = dict(client.get(f"/runs/{run_id}").json())
        run["artifact_ids"] = [
            str(item["id"]) for item in client.get(f"/runs/{run_id}/artifacts").json()
        ]
        run["experiments"] = client.get(f"/runs/{run_id}/experiments").json()
        for name in (
            "manuscript.md",
            "research_report.md",
            "manuscript_narrative",
            # GOAL-20261029-100 EC-02：编辑决定的正文也要读回来（判据要解它、不是只看 id）。
            "editorial_decision",
            # GOAL-20261029-100 EC-03：应答信由汇编器写；要判它就得读它的字节。
            "response_letter.md",
        ):
            run[f"body:{name}"] = _content_of(client, run["artifact_ids"], name)
    return run


def _content_of(client: Any, artifact_ids: list[str], name: str) -> str | None:
    """按产物名后缀取内容字节（读面不在场 ⇒ `None`，不猜）。"""
    for artifact_id in artifact_ids:
        if artifact_id.endswith(f":{name}"):
            response = client.get(f"/artifacts/{artifact_id}/content")
            assert response.status_code == 200, response.text
            return str(response.content.decode("utf-8", errors="replace"))
    return None


class TestTheManuscriptComesOutOfTheProductEntry:
    def test_the_run_succeeds_and_every_declared_artifact_exists(self) -> None:
        """(1) 九相全落库 + `SUCCEEDED`（手稿相与编辑相真的被派发过，不是被跳过）。"""
        with ManuscriptRelayFixture() as relay:
            deps, offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal099-manuscript-arc")
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        suffixes = {item.rsplit(":", 1)[-1] for item in run["artifact_ids"]}
        for name in OUTPUT_NAMES:
            assert name in suffixes, (name, sorted(suffixes))
        assert run["experiments"]["experiments"], run["experiments"]
        assert offline.requests, "检索必须真的发生过（否则 References 无从谈起）"
        # GOAL-20261029-100：八相 → **十**相（EC-02 新增 `editorial`，EC-03 新增 `revision`）。
        assert len(PHASES) == 10
        assert "editorial" in PHASES and "revision" in PHASES

    def test_the_editorial_decision_comes_out_of_the_product_entry(self) -> None:
        """GOAL-20261029-100 EC-02：编辑决定**经产品入口**产出且四值之一可判。

        判三件（都是结构事实）：
        ① 制品在场（`editorial_decision` 落 canonical）；
        ② 它的字节能解成已校验的决定 —— 取值在四值闭集内、理由非空、
           非 `accept` 时 `required_changes` 非空（解析器**自己**会拒绝违者）；
        ③ 被测的那份决定不是 `accept` —— 这样「要求返修要说改什么」那条判据在
           **产品路径**上真的被走到过（夹具默认给 `minor_revision`）。
        """
        from packages.application.deliverable.editorial_decision import (
            parse_editorial_decision,
        )
        from packages.domain.enums import EditorialDecision

        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal100-editorial-decision")
        body = run["body:editorial_decision"]
        assert body, "产品入口跑完必须有 editorial_decision 制品"
        outcome = parse_editorial_decision(body)
        assert isinstance(outcome.decision, EditorialDecision)
        assert outcome.decision is not EditorialDecision.ACCEPT, (
            "夹具必须给一个**要求返修**的决定：accept 会让 required_changes 那条判据"
            "在产品路径上从未被走到",
            outcome.decision,
        )
        assert outcome.required_changes, outcome
        assert outcome.rationale.strip(), outcome

    def test_the_response_letter_answers_every_review_point(self) -> None:
        """GOAL-20261029-100 EC-03：应答信**经产品入口**产出，且逐条对应评审点。

        判四件（都是结构事实）：
        ① `response_letter.md` 在库里；
        ② 它按 `### P<n>` 逐条成段，条数 == 评审点条数；
        ③ 每个点位都带着它对应的原意见（`> …` 引用行）；
        ④ 应答信里**没有**任何未应答的编号 —— 漏答会让汇编器**拒绝**产出这封信
           （所以「信在」这一件事本身已经蕴含「没有漏答」）。
        """
        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal100-response-letter")
        letter = run["body:response_letter.md"]
        assert letter, "产品入口跑完必须有 response_letter.md"
        sections = [line for line in letter.splitlines() if line.startswith("### P")]
        assert sections, letter[:400]
        # 逐条成段且编号连续（P1…Pn，一个不跳）。
        expected = [f"### P{index} (" for index in range(1, len(sections) + 1)]
        assert all(section.startswith(marker) for section, marker in zip(sections, expected)), (
            sections,
        )
        # 每个点位都引用出它对应的原意见（应答信必须能对着评审读）。
        quotes = [line for line in letter.splitlines() if line.startswith("> ")]
        assert len(quotes) == len(sections), (len(quotes), len(sections))

    def test_the_manuscript_is_imrad_with_a_real_reference_list(self) -> None:
        """(2) `manuscript.md` 是 IMRaD，且 References 是**真**Vancouver 行。

        「真」判三件：每行有作者、有刊名、有年份 —— 而这三件**只能**来自本 run 落盘的
        工具结果字节（`references.py` 不联网、不猜）。本夹具的离线记录集里那条记录的
        作者是 `Hoffmann C, Djerroud S, et al.`、刊名 `Nat Commun`、年份 `2024`。
        """
        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal099-manuscript-shape")
        body = run["body:manuscript.md"]
        assert body, "产品入口跑完必须有 manuscript.md"
        positions = [body.index(heading) for heading in _MANUSCRIPT_HEADINGS]
        assert positions == sorted(positions), positions
        assert body.index("## References") > positions[-1]
        assert body.startswith("# "), body[:80]
        # References 的行是真元数据（不是 dict repr、不是占位符）。
        assert "Hoffmann C" in body, body[-800:]
        assert "Nat Commun" in body and "2024" in body
        assert "{" not in body.split("## References", 1)[1]
        for placeholder in ("Unknown", "N/A", "n.d."):
            assert placeholder not in body, placeholder

    def test_the_model_body_carries_no_digits(self) -> None:
        """(3) 模型那块面（Abstract … Conclusion）里没有任何数字（引用标记除外）。

        扫的面要排除**汇编器写的字**：抬头（run id / digest 是数字）与**节标题**
        （`## 1. Introduction` 的编号是汇编器加的）。判据判的是产品产物里的那个分界 ——
        与 `validate_manuscript` 判的八键值同一条口径。
        """
        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal099-manuscript-digits")
        body = run["body:manuscript.md"]
        assert body
        start = body.index(_MANUSCRIPT_HEADINGS[0])
        end = body.index("### Table 1.")
        prose = "\n".join(
            line
            for line in body[start:end].splitlines()
            if line.strip() and not line.startswith("## ")
        )
        assert re.search(r"\d", re.sub(r"\[\d+\]", "", prose)) is None, prose

    def test_the_assembled_table_carries_the_numbers(self) -> None:
        """(3) 数字在汇编器写的数据表里（且带来源列）—— 与「正文无数字」是同一条分界。"""
        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal099-manuscript-table")
        body = run["body:manuscript.md"]
        assert body
        tail = body[body.index("### Table 1.") :]
        assert "| 类别 | 名称 | 值 | 来源 |" in tail
        # 实验真跑过 ⇒ 表里有指标行（名字与值都由汇编器写）。
        assert "| 指标 |" in tail, tail[:600]

    def test_the_narrative_artifact_is_the_models_own_face(self) -> None:
        """归属可读：`manuscript_narrative` 是**模型会话**的产物，`manuscript.md` 记它的来源。"""
        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal099-manuscript-narrative")
        narrative = run["body:manuscript_narrative"]
        assert narrative, "手稿相的产物必须落库"
        assert VARIANT_A[0] in narrative or "manuscript_narrative" in narrative
        body = run["body:manuscript.md"]
        assert body
        assert "**narrative author**: model_assisted:" in body
        assert "**assembly state**: `" in body


class TestTurningTheManuscriptOffIsByteIdentical:
    def test_with_the_switch_off_only_the_report_is_assembled(self) -> None:
        """(4) 关掉开关 ⇒ 只有报告；`manuscript.md` **不在**库里（不是被静默降级）。"""
        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0], manuscript=False)
            run = _run_once(deps, "goal099-manuscript-off")
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        suffixes = {item.rsplit(":", 1)[-1] for item in run["artifact_ids"]}
        assert "research_report.md" in suffixes, sorted(suffixes)
        assert "manuscript.md" not in suffixes, sorted(suffixes)
        assert run["body:research_report.md"], "报告仍然必须产出"

    def test_the_report_does_not_depend_on_the_manuscript_switch(self) -> None:
        """(4) **零回归**（产品入口）：开着与关掉手稿，报告的**结构、指标集与判词**相同。

        为什么产品入口这一格不能字面比较字节（本轮实测，如实登记为**既有性质**，
        不是本轮引入的回归）：

        1. 抬头有 `- **run**: <uuid>`，来源行有 `evidence:<uuid>:<task-uuid>:…` ——
           每次 run 的 uuid 都不同；
        2. **多臂指标的行序**由 `experiment_run_id`（随机 uuid）的字典序决定
           （`report_facts.metrics_of` → `_metric_rows` 按 `sorted(per_run)`），
           因此同一份夹具的两次 run 会**交替**出现 `178.5` 与 `7990.0` 两种行序。

        两类事实都与手稿开关无关。⇒ 本格判**内容面**：四节标题齐备、指标名集合相同、
        每条指标的两次读数都在、判词相同；而**字面逐字节**相同那一臂在**同一个 run id**
        上判：`tests/application/test_manuscript_assembly.py::
        test_the_report_is_byte_identical_with_and_without_the_manuscript`（同一份事实、
        同一个 run ⇒ 那里可以且必须字面相同）。
        """
        with ManuscriptRelayFixture() as relay:
            deps_on, _ = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0], manuscript=True)
            on = _run_once(deps_on, "goal099-manuscript-bytes-on")
        with ManuscriptRelayFixture() as relay:
            deps_off, _ = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0], manuscript=False)
            off = _run_once(deps_off, "goal099-manuscript-bytes-off")
        assert on["state"] == "SUCCEEDED", (on["state"], on.get("message"))
        assert off["state"] == "SUCCEEDED", (off["state"], off.get("message"))
        assert on["body:manuscript.md"], "开着那次必须有手稿"
        assert off["body:manuscript.md"] is None, "关掉那次不得有手稿"
        on_report = on["body:research_report.md"]
        off_report = off["body:research_report.md"]
        assert on_report and off_report
        signature = _report_signature(on_report)
        assert signature == _report_signature(off_report), (
            "报告的结构/指标集/判词因手稿开关而变 ⇒ 既有产物发生了回归"
        )
        # 归一化不许把内容抹成空壳（否则上一条是空真）。
        assert signature["headings"] == list(_REPORT_HEADINGS), signature["headings"]
        assert signature["metric_names"], "报告里必须有指标行（本夹具的实验真跑过）"
        assert signature["decision"], signature["decision"]


_REPORT_HEADINGS = (
    "## 1. 问题与动机",
    "## 2. 检索与证据",
    "## 3. 实验与指标",
    "## 4. 评审与结论",
)
_METRIC_NAME = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
_DECISION = re.compile(r"^- \*\*决定\*\*: `([^`]+)`$", re.MULTILINE)


def _report_signature(body: str | None) -> dict[str, Any]:
    """报告**内容面**的签名（与 uuid / 行序无关：集合与判词，不是字节）。

    指标行按 markdown 表格行取：`| \\`<name>\\` | [\\`<arm>\\` |] <value> | <unit> |`
    —— 名字用**集合**（行序是 uuid 的函数，见上面那条 docstring），值用**排序后的多重集**
    （两臂各一个读数，哪一臂在前不影响「两个读数都在」）。
    """
    assert body is not None
    headings = [heading for heading in _REPORT_HEADINGS if heading in body]
    names = sorted(set(_METRIC_NAME.findall(body)))
    values = sorted(re.findall(r"\| (\d+(?:\.\d+)?) \| —? ?\|", body))
    decisions = sorted(set(_DECISION.findall(body)))
    return {
        "headings": headings,
        "metric_names": names,
        "metric_values": values,
        "decision": decisions,
    }
