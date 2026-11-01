"""EC-02 的**路由级**取证：两个补字段经真实 HTTP 读面回得来（GOAL-20261101-103）。

**它补哪一格**（收口复检指名的缺口）：EC-02 的判据此前只判**投影函数**（
`_artifact_dto(...)`）与**源码字面量**（`test_read_face_field_completeness.py`）——
两者都不证明「`GET /runs/{id}/artifacts` 的响应体里真的有这一格」。一个字段可以在
DTO 里、投影也写了，但**路由没接**或**响应模型把它滤掉**，单元判据照样绿。

本文件走**产品入口**（`TestClient` + `POST /projects/{id}/runs`）真跑一次，再从两条
**真实路由**取回 JSON 断言：

- `GET /runs/{id}/artifacts` ⇒ `ArtifactDto.supersedes` 在，且改稿制品的值**指回** v1；
- `GET /runs/{id}/reviews` ⇒ `ReviewFindingDto.reviewer_model` 在，且值是
  `endpoint/model` 形态的**真实**归因（不是空串、不是占位符）。

**为什么必须是真的值**：断言「键存在」会让 `reviewer_model=None` 也通过 —— 而那一格
存在的全部意义就是「这条判词是哪个模型判的」。所以判据同时要求
① 键在、② 至少一条非 `None`、③ 形态是 `a/b`（域层 `reviewer_model` 的稳定串形）。

**射程边界（如实登记）**：本文件要真容器实验（`requires_docker`）—— 它复用十一条产品
路径的既有夹具。windows CI 的 runner 没有 docker ⇒ 诚实 skip（既有契约）。
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.app import create_app
from tests.e2e.direction_to_manuscript_support import (
    PROTOCOL,
    VARIANT_A,
    ManuscriptRelayFixture,
    deps_for,
)

pytestmark = pytest.mark.requires_docker


def _run_once(key: str) -> dict[str, Any]:
    """经产品入口跑一次十一相 run，取回两条读面的 JSON（**经路由**，不调投影函数）。"""
    from fastapi.testclient import TestClient

    with ManuscriptRelayFixture() as relay:
        deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
        with TestClient(create_app(deps)) as client:
            created = client.post(
                "/projects/example-project/runs",
                json={"protocol_path": PROTOCOL},
                headers={"Idempotency-Key": key},
            )
            assert created.status_code == 200, created.text
            run_id = str(created.json()["id"])
            detail: dict[str, Any] = dict(client.get(f"/runs/{run_id}").json())
            artifacts_response = client.get(f"/runs/{run_id}/artifacts")
            reviews_response = client.get(f"/runs/{run_id}/reviews")
    return {
        "run": detail,
        "artifacts_status": artifacts_response.status_code,
        "artifacts": artifacts_response.json(),
        "reviews_status": reviews_response.status_code,
        "reviews": reviews_response.json(),
    }


class TestTheArtifactRouteCarriesSupersedes:
    """EC-02 (i)：`GET /runs/{id}/artifacts` 的响应体里**真的**有 `supersedes`。"""

    def test_every_artifact_response_carries_the_key(self) -> None:
        """**每一件**制品都带这一格（不是只有改稿那件 —— 响应模型必须整体带上）。"""
        got = _run_once("goal103-readface-artifacts")
        assert got["run"]["state"] == "SUCCEEDED", (got["run"]["state"], got["run"].get("message"))
        assert got["artifacts_status"] == 200, got["artifacts_status"]
        artifacts = got["artifacts"]
        assert artifacts, "本 run 必须至少落一件制品（否则这条判据没有对象）"
        missing = [item["id"] for item in artifacts if "supersedes" not in item]
        assert missing == [], (
            "`ArtifactDto` 必须在**每一件**制品上都带 `supersedes`（缺一格 = 响应模型漏字段）",
            missing[:5],
        )

    def test_the_revised_manuscript_points_back_at_the_original(self) -> None:
        """改稿制品的 `supersedes` **指回 v1**（不是 `None`、不是自指、不是别的 run）。"""
        got = _run_once("goal103-readface-supersedes")
        artifacts = got["artifacts"]
        revised = [item for item in artifacts if str(item["id"]).endswith(":manuscript_v2.md")]
        assert revised, "十一相 run 必须装出 `manuscript_v2.md`（改稿链的存在前提）"
        original = [item for item in artifacts if str(item["id"]).endswith(":manuscript.md")]
        assert original, "十一相 run 必须装出 `manuscript.md`"
        v1_ids = {str(item["id"]) for item in original}
        # 读面零问题地给回父指针，且它指向本 run 的 v1。
        for item in revised:
            pointer = item.get("supersedes")
            assert pointer is not None, (
                "改稿制品的 `supersedes` 不得为 None —— 它在域层已设置，读面必须披露",
                item["id"],
            )
            assert pointer in v1_ids, (
                "`supersedes` 必须指向**本 run 的** `manuscript.md`",
                pointer,
                sorted(v1_ids),
            )
            assert pointer != item["id"], "`supersedes` 不得自指（域层也会拒，但读面也要对）"


class TestTheReviewsRouteCarriesReviewerModel:
    """EC-02 (ii)：`GET /runs/{id}/reviews` 的响应体里**真的**有 `reviewer_model`。"""

    def test_every_review_finding_carries_the_key(self) -> None:
        """**每一条**判词都带这一格（响应模型整体带上，不是挑一条填）。"""
        got = _run_once("goal103-readface-reviews")
        assert got["reviews_status"] == 200, got["reviews_status"]
        reviews = got["reviews"]
        assert reviews, "十一相 run 必须留下评审判词（否则这条判据没有对象）"
        missing = [item["id"] for item in reviews if "reviewer_model" not in item]
        assert missing == [], (
            "`ReviewFindingDto` 必须在**每一条**判词上都带 `reviewer_model`",
            missing[:5],
        )

    def test_the_attribution_is_a_real_endpoint_model_pair(self) -> None:
        """值形态是 `endpoint/model`（域层的稳定串形），且**不是**占位符。

        判「键在」不够：`reviewer_model=None` 也能让上一条通过，而这一格存在的全部意义
        就是**归因**。这里要求至少一条非空、且形如 `a/b`。
        """
        got = _run_once("goal103-readface-attribution")
        reviews = got["reviews"]
        attributed = [item for item in reviews if item.get("reviewer_model")]
        assert attributed, (
            "至少一条判词必须带**非空**的 `reviewer_model`（全空 = 归因这一格没接上）",
            [item.get("reviewer_model") for item in reviews],
        )
        for item in attributed:
            value = str(item["reviewer_model"])
            assert "/" in value, (
                "`reviewer_model` 必须是 `endpoint/model` 形态（域层的稳定串形）",
                value,
            )
            endpoint, _, model = value.partition("/")
            assert endpoint and model, f"`reviewer_model` 两端都不得为空: {value!r}"
            assert " " not in value, f"`reviewer_model` 不得含空白: {value!r}"

    def test_each_verdict_is_attributable_to_a_distinct_reviewer_target(self) -> None:
        """**归因是逐条可读的**：多条判词时至少能看到两个不同的执行目标。

        十一相 run 的 `review` 相有两位评审（`direction_to_manuscript_v1.yaml` 的
        `multi_role_review`）⇒ 若读面把两条判词都归到同一个目标，那说明归因字段被写死
        或取了错的来源。**射程**：这一条只在真跑出 ≥2 条判词时才有对象，故用条件断言。
        """
        got = _run_once("goal103-readface-distinct")
        attributed = {
            str(item["reviewer_model"]) for item in got["reviews"] if item.get("reviewer_model")
        }
        review_count = len([item for item in got["reviews"] if item.get("review_type")])
        if review_count < 2:
            pytest.skip(f"本 run 只留下 {review_count} 条判词 ⇒ 本条无对象（不假绿）")
        assert len(attributed) >= 2, (
            "两位评审的判词必须归到 ≥2 个不同的 `endpoint/model`（写死 = 归因不可信）",
            sorted(attributed),
        )
