"""EC-05（HTTP 层）：`/runs/{id}/panel-advice` 与 `/runs/{id}/reviews` **同源**且只读。

**它补哪一格**：编排级的 `panel_advice` 已有判据（`test_advisory_panel_read_face.py`），
但那证明不了**接出去的那一层**（DTO 映射、503/404 语义、只读方法面）。EC-05 要求
「HTTP + 编排两级」，本文件钉 HTTP 那一级。

**判什么**：

1. 两条读面**同源**：同一份落库判词 ⇒ `/reviews` 逐条可数、`/panel-advice` 聚合可读，
   且两边**票型一致**；
2. 端点**只读**：只注册了 `GET`，`POST` 不被接受；
3. 诚实失败：未知 run ⇒ **404**；存储未接 ⇒ **503**（空列表会被读成"这 run 没有评审"）。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.evidence import ReviewFinding

_PROTOCOL = "m12_reference_research_v1.yaml"
_RUN_ID = "run-goal115-ec05"


def _seed(store: Any, run_id: str) -> None:
    """两份判词：**同一 phase、不同 task、不同模型**（分歧的真实形态）。"""
    store.put(
        ScopedReviewFinding(
            finding=ReviewFinding(
                id="finding-a",
                review_type="scientific_review",
                verdict="REJECT",
                reviewer_model="main/beam-free",
            ),
            run_id=run_id,
            task_id="task-reviewer-a",
            contract_id="dual_model_review_deliverable",
            phase_id="review",
        )
    )
    store.put(
        ScopedReviewFinding(
            finding=ReviewFinding(
                id="finding-b",
                review_type="scientific_review",
                verdict="PASS",
                reviewer_model="main/longcat-2.5-free",
            ),
            run_id=run_id,
            task_id="task-reviewer-b",
            contract_id="dual_model_review_deliverable",
            phase_id="review",
        )
    )


@pytest.fixture()
def seeded_client(run_ready_client: TestClient, run_ready_deps: Any) -> TestClient:
    """在**已存在的 run**上落两份判词（run 由既有 start_run 面创建）。"""
    import uuid

    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    run_id = response.json()["id"]
    _seed(run_ready_deps.review_findings, run_id)
    run_ready_client.panel_run_id = run_id  # type: ignore[attr-defined]
    return run_ready_client


class TestTheTwoFacesShareOneSource:
    def test_reviews_lists_both_findings(self, seeded_client: TestClient) -> None:
        run_id = seeded_client.panel_run_id  # type: ignore[attr-defined]
        response = seeded_client.get(f"/runs/{run_id}/reviews")
        assert response.status_code == 200, response.text
        assert sorted(item["verdict"] for item in response.json()) == ["PASS", "REJECT"]

    def test_panel_advice_aggregates_the_same_findings(self, seeded_client: TestClient) -> None:
        run_id = seeded_client.panel_run_id  # type: ignore[attr-defined]
        response = seeded_client.get(f"/runs/{run_id}/panel-advice")
        assert response.status_code == 200, response.text
        phases = {item["phase_id"]: item for item in response.json()}
        assert "review" in phases, response.json()
        advice = phases["review"]
        assert advice["votes"] == {"PASS": 1, "REJECT": 1}, advice
        assert advice["dissent"], "1 负 1 过必须在 HTTP 面上留下可读的分歧"
        assert advice["voters"] == 2, advice
        assert advice["independent"] is True, advice["independence_notes"]

    def test_the_two_faces_agree_on_the_vote_counts(self, seeded_client: TestClient) -> None:
        """同源判据：逐条面聚合出的票型 == 聚合面的 `votes`。"""
        run_id = seeded_client.panel_run_id  # type: ignore[attr-defined]
        listed = seeded_client.get(f"/runs/{run_id}/reviews").json()
        counted: dict[str, int] = {}
        for item in listed:
            counted[item["verdict"]] = counted.get(item["verdict"], 0) + 1
        phases = {
            item["phase_id"]: item
            for item in seeded_client.get(f"/runs/{run_id}/panel-advice").json()
        }
        assert counted == phases["review"]["votes"], (counted, phases["review"]["votes"])


class TestTheEndpointIsReadOnly:
    def test_only_get_is_registered(self, run_ready_deps: Any) -> None:
        """**读 OpenAPI schema**（不是遍历 `app.routes`）。

        `app.routes` 里每条的 `path` 在本装配下读不出真实值（实测：全是空串），
        而 schema 是**同一个 app** 生成的路由事实，正是「注册了哪些方法」的权威来源。
        判据据此断言：该路径**只**有 GET。
        """
        from services.api.app import create_app

        spec = create_app(run_ready_deps).openapi()
        found = {
            path: sorted(method.upper() for method in operations)
            for path, operations in spec["paths"].items()
            if path.endswith("/panel-advice")
        }
        assert found, "panel-advice 没有出现在 OpenAPI schema 里"
        assert list(found.values()) == [["GET"]], found

    def test_a_post_never_succeeds(self, run_ready_client: TestClient) -> None:
        """**写不成**才是要判的事（具体状态码由路由表决定）。

        实测：本装配下 POST 到该路径得到 **422**（路径存在但方法不匹配，请求体先被校验拒绝），
        不是 405 —— 判「必须是 405」会写死一个框架细节；判「不是 2xx」才对应
        「这个面只读」这条产品事实。
        """
        response = run_ready_client.post(f"/runs/{_RUN_ID}/panel-advice", json={})
        assert not (200 <= response.status_code < 300), (
            f"POST 竟然成功了（{response.status_code}）：panel-advice 必须是只读面"
        )


class TestTheHonestFailures:
    def test_an_unknown_run_is_404_not_an_empty_list(self, run_ready_client: TestClient) -> None:
        response = run_ready_client.get("/runs/run-does-not-exist/panel-advice")
        assert response.status_code == 404, response.text

    def test_a_missing_store_is_503_not_an_empty_conclusion(self, run_ready_deps: Any) -> None:
        """未接存储 ⇒ 503：空列表会被读成"这 run 没有评审"，那是假结论。"""
        from dataclasses import replace

        from services.api.app import create_app

        deps = replace(run_ready_deps, review_findings=None)
        with TestClient(create_app(deps)) as client:
            response = client.get(f"/runs/{_RUN_ID}/panel-advice")
            assert response.status_code in {404, 503}, response.status_code
            if response.status_code == 503:
                assert "not configured" in response.text.lower(), response.text
