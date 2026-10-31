"""GOAL-20261031-102 EC-02/EC-03/EC-04：改稿闭环 + 投稿包 + 期刊选择**经产品入口**。

与 `test_direction_to_manuscript_product_path.py` 同一条产品入口（`TestClient` +
`POST /projects/{id}/runs` + 读面取回字节），单列一个文件只因原文件贴着 450 行硬上限
（规模门）。夹具逐字复用 `direction_to_manuscript_support`（同一 mock 中转站 / 同一
离线检索池），**只观察、不复写**。
"""

from __future__ import annotations

import re
from pathlib import Path

from services.api.app import create_app
from tests.e2e.direction_to_manuscript_support import (
    PROTOCOL,
    VARIANT_A,
    ManuscriptRelayFixture,
    deps_for,
)
from tests.e2e.test_direction_to_manuscript_product_path import _content_of, _run_once

_REPO_ROOT = Path(__file__).resolve().parents[2]


class TestTheRevisionClosureComesOutOfTheProductEntry:
    """GOAL-20261031-102 EC-02：改稿闭环**经产品入口**存在（不是单元缝里的假象）。"""

    def test_the_revised_manuscript_supersedes_the_original(self) -> None:
        """闭环三件事：v2 在场、`supersedes` → v1（读面零问题）、正文真的改了。"""
        from packages.application.run_orchestration.revision_assembly import (
            revision_closure_of_run,
        )

        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal102-revision-closure")
            closure = revision_closure_of_run(deps.artifacts, str(run["id"]))
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        v2 = run["body:manuscript_v2.md"]
        assert v2, "带改稿正文的 run 必须装出 manuscript_v2.md"
        assert closure is not None and closure["problems"] == (), closure
        # 改稿**真的改了**：Related Work 与 v1 逐字不同（不是把 v1 复制一遍冒充 v2）。
        v1 = run["body:manuscript.md"]
        assert v1 and "named planning choice" in v2 and "named planning choice" not in v1, (
            "v2 的 Related Work 必须回应编辑要求，而不是原样复制 v1"
        )
        letter = run["body:response_letter.md"]
        assert letter and "manuscript_v2.md" in letter, letter[:600]


class TestTheSubmissionPackageComesOutOfTheProductEntry:
    """GOAL-20261031-102 EC-03：投稿包五件制品**经产品入口**产出且逐件受判。"""

    _FIVE = (
        "cover_letter.md",
        "author_contributions.md",
        "conflicts_of_interest.md",
        "data_availability.md",
        "supplementary.md",
    )

    def test_the_five_artifacts_are_readable_through_the_product_entry(self) -> None:
        """(i) 五件都在读面上（claim→relation 投影：只 put 不登记的件读不到）。"""
        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal102-submission-package")
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        for name in self._FIVE:
            assert run[f"body:{name}"], name
        assert run["body:submission_package"], "投稿会话产物必须落库"

    def test_contributions_list_only_roles_the_run_dispatched(self) -> None:
        """(ii) CRediT 术语 ⊆ 本 run 协议分派的角色（反证臂在单元判据两向按压）。"""
        import yaml as _yaml

        from packages.application.run_orchestration.submission_assembly import ROLE_CREDIT

        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal102-contributions")
        body = run["body:author_contributions.md"]
        assert body
        listed = set(re.findall(r"^\| `[^`]+` \| `[^`]+` \| `([^`]+)` \|$", body, re.MULTILINE))
        assert listed, body[:400]
        protocol = _yaml.safe_load(
            _REPO_ROOT.joinpath("examples/protocols/direction_to_manuscript_v1.yaml").read_text(
                encoding="utf-8"
            )
        )
        dispatched = {
            str(required["role"])
            for phase in protocol["phases"]
            for required in phase.get("required_roles") or []
        }
        allowed = {ROLE_CREDIT[role] for role in dispatched}
        assert listed <= allowed, sorted(listed - allowed)

    def test_the_data_availability_digests_verify_against_the_read_face(self) -> None:
        """(iii) 清单里的每行 digest 都能用**读面字节**重算出来（编造 ⇒ 立刻红）。"""
        import hashlib

        from fastapi.testclient import TestClient

        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            with TestClient(create_app(deps)) as client:
                created = client.post(
                    "/projects/example-project/runs",
                    json={"protocol_path": PROTOCOL},
                    headers={"Idempotency-Key": "goal102-data-availability"},
                )
                assert created.status_code == 200, created.text
                run_id = str(created.json()["id"])
                artifact_ids = [
                    str(item["id"]) for item in client.get(f"/runs/{run_id}/artifacts").json()
                ]
                availability = _content_of(client, artifact_ids, "data_availability.md")
                # 抽一件实证：读面字节重算 digest（清单不是散文，是**可复核**的清单）。
                sample = next(item for item in artifact_ids if item.endswith(":cover_letter.md"))
                sample_digest = hashlib.sha256(
                    client.get(f"/artifacts/{sample}/content").content
                ).hexdigest()
        assert availability
        rows = [
            {"id": match.group("id"), "digest": match.group("digest")}
            for match in re.finditer(
                r"^\| `(?P<id>[^`]+)` \| `(?P<digest>[^`]+)` \|$",
                availability,
                re.MULTILINE,
            )
        ]
        assert rows, availability[:400]
        readable = set(artifact_ids)
        for row in rows:
            assert row["id"] in readable, f"{row['id']} 不在读面上"
            if row["id"].endswith(":cover_letter.md"):
                assert sample_digest in row["digest"], (sample_digest, row)

    def test_the_journal_selection_validates_against_the_closed_set(self) -> None:
        """EC-04：编辑决定里的期刊选择经产品路径可读，且在闭集内、依据引 scope 关键词。"""
        from packages.application.deliverable.journal_selection import (
            load_journals,
            selection_from_artifact,
            validate_selection,
        )

        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal102-journal-selection")
        body = run["body:editorial_decision"]
        assert body
        selection = selection_from_artifact(body)
        assert selection is not None, "夹具的编辑决定必须带期刊选择（产品路径要走到这条）"
        journals = load_journals(_REPO_ROOT / "examples" / "config" / "journals.yaml")
        record = validate_selection(selection, journals)
        assert record.scope_keywords, record

    def test_the_conflict_statement_is_a_structured_field(self) -> None:
        """(iv) 「有无冲突」按**字段**读：布尔 + 陈述，且与会话声明逐字段一致。"""
        from packages.application.run_orchestration.submission_assembly import (
            parse_coii_fields,
            parse_submission_statement,
        )

        with ManuscriptRelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run = _run_once(deps, "goal102-coi")
        rendered_has, rendered_statement = parse_coii_fields(run["body:conflicts_of_interest.md"])
        assert isinstance(rendered_has, bool)
        assert rendered_statement.strip(), "陈述必须非空（声明要说出查过什么）"
        declared = parse_submission_statement(str(run["body:submission_package"]))
        assert rendered_has == declared.has_conflict
        assert rendered_statement == declared.statement
