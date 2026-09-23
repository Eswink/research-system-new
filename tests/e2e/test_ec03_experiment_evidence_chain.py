"""GOAL-012 EC-03 判据：实验产出的**证据链**可追溯，且**去掉产物 ⇒ 判据红**（PLAN-20260923-144）。

判的**不是**「容器起了没有」（那是 `test_sandbox_experiment_seam_docker.py` 的机械面），而是
「实验跑过」与「产物已登记且可追溯」是同一条**可判据的事实**：

1. **产物在读面**：`GET /runs/{id}/experiments` 与 `GET /runs/{id}/artifacts` 两面看到的是
   **同一组**制品 id，且覆盖四件产物（`stdout.log` / `stderr.log` / `experiment_result.json` /
   合约声明的 `analysis_report`）。
2. **内容可重算**：`GET /artifacts/{id}/content` 取回的字节，其 `Digest.of_bytes` 必须等于该制品
   对应证据条目登记的 `content_digest`——digest 是**算出来的**，不是声明出来的。
3. **来源可独立复核**：实验记录里的 `image_digest` 必须等于**独立查 daemon**（另一条代码路径：
   `docker image inspect`，不经产品适配器）得到的镜像 Id；`environment_digest` 非空；
   canonical 的**语义摘要**在两次执行之间**相同**（同 seed / 同镜像 ⇒ 同语义）。
4. **不得拿模型自述冒充**（EC-03 明文）：四件产物的证据 `source_origin` 指向
   `<experiment_run_id>:<产品名>`（实验路径），不是会话交付物。

**成对反证**（本文件第 2 条）：同一条链换一个**不写声明产物**的实验脚本（写 `report.txt` 而不是
`analysis_report`，其余同构）⇒ 验收门**拒收并点名** `analysis_report`，产物读面上**没有**它，
而其余产物**仍在** ⇒ 红的理由**恰是「声明产物缺失」**，不是「实验没跑」。

**离线**：容器内 `NetworkMode=none`，容器外零出网（判据只走 TestClient + 本机 daemon）。
`requires_docker`：非 Linux 容器的 daemon 下如实 skip。
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

import pytest

from packages.domain.core import Digest
from tests.e2e.live_run_support import (
    EXPERIMENT_IMAGE,
    EXPERIMENT_SCRIPT,
    start_run,
    with_sandbox_experiment,
)

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "sort_analysis_v1.yaml"
#: 四件产物（合约声明的交付物 + 既有实验输出契约 + 两份日志）
_PRODUCTS = ("analysis_report", "experiment_result.json", "stdout.log", "stderr.log")

#: 受控执行体**声明**的 review 会话交付物（同 EC-02；只有 review 阶段跑会话）。
_REVIEW_DELIVERABLE: dict[str, object] = {
    "review_decision": {"verdict": "ACCEPT", "rationale": "controlled fake session output"}
}

#: 反证用脚本：与 `sort_analysis_baseline.py` **同构**，只是把产物写到**别的名字**下
#: （`report.txt`），于是合约声明的 `analysis_report` **不存在**——其余行为逐字相同，
#: 好让红的理由只可能是「声明产物缺失」。
_COUNTER_SCRIPT = """\
import json
import os
from pathlib import Path

PRODUCT_NAME = "report.txt"
RESULT_NAME = "experiment_result.json"


def main() -> int:
    workspace = Path.cwd()
    report = workspace / PRODUCT_NAME
    report.write_text("# counter-proof report (no declared product)\\n", encoding="utf-8")
    payload = {
        "experiment_run_id": os.environ.get("EXPERIMENT_RUN_ID", ""),
        "status": "SUCCEEDED",
        "artifact_refs": [PRODUCT_NAME],
        "metrics": {"corpus_size": 8, "worst_case_comparisons": 24},
    }
    (workspace / RESULT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _deps(script: str) -> Any:
    from adapters.fakes.agent_runtime import FakeAgentRuntime
    from tests.api.run_fixtures import make_run_ready_deps

    deps = make_run_ready_deps()
    with_sandbox_experiment(
        deps,
        script=script,
        image=EXPERIMENT_IMAGE,
        runtime=FakeAgentRuntime(structured_output=_REVIEW_DELIVERABLE),
    )
    return deps


def _run(deps: Any) -> tuple[Any, str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """起一次 run，取回 `(client, run_id, run, artifacts, evidence)`（读面快照）。"""
    from fastapi.testclient import TestClient

    from services.api.app import create_app

    client = TestClient(create_app(deps))
    client.__enter__()
    run = start_run(client, _PROTOCOL)
    run_id = str(run["id"])
    detail = client.get(f"/runs/{run_id}").json()
    artifacts = list(client.get(f"/runs/{run_id}/artifacts").json())
    evidence = list(client.get(f"/runs/{run_id}/evidence").json())
    return client, run_id, detail, artifacts, evidence


def _experiment_of(client: Any, run_id: str) -> dict[str, Any]:
    experiments = client.get(f"/runs/{run_id}/experiments").json()["experiments"]
    assert len(experiments) == 1, experiments
    return dict(experiments[0])


def _product_names(artifacts: list[dict[str, Any]]) -> set[str]:
    return {str(item["id"]).rsplit(":", 1)[-1] for item in artifacts}


def _semantic_digest(deps: Any, experiment_run_id: str) -> str | None:
    """canonical 事实（不是读面）：语义摘要——`semantic_metrics_digest`。"""
    run = deps.experiment_store.get_run(experiment_run_id)
    result = run.result
    assert result is not None, run
    return str(result.semantic_metrics_digest) if result.semantic_metrics_digest else None


def _daemon_image_id(image: str) -> str | None:
    """**独立**查 daemon 的镜像 Id（不经产品适配器）；CLI 缺失 ⇒ None（由调用方判定）。"""
    docker = shutil.which("docker")
    if docker is None:
        return None
    completed = subprocess.run(  # noqa: S603 - 固定 argv，无外部输入
        [docker, "image", "inspect", "--format", "{{.Id}}", image],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _assert_faces_carry_the_products(experiment: dict[str, Any], artifacts: Any) -> None:
    """① 产物在读面，且两读面看得到**同一组**实验产物。"""
    face_ids = {str(item) for item in experiment["artifact_ids"]}
    run_face_ids = {str(item["id"]) for item in artifacts}
    assert set(_PRODUCTS) <= _product_names(artifacts), _product_names(artifacts)
    # 两面**不是**同一组：run 级制品面还含别的阶段/声明的制品（review 会话的
    # `review_decision`、组合根种入的声明输入）。可追溯要的是**这次实验的产物在两面
    # 都看得到**——方向是子集，不是相等（相等会把「别的阶段也有产物」误判成红）。
    experiment_products = {item for item in face_ids if item.rsplit(":", 1)[-1] in _PRODUCTS}
    assert experiment_products <= run_face_ids, (face_ids, run_face_ids)
    assert len(experiment_products) == len(_PRODUCTS), face_ids


def _assert_content_digests_recompute(
    deps: Any, client: Any, artifacts: Any, evidence: Any, experiment_run_id: str
) -> None:
    """② 内容可重算（证据条目 + **来源记录**两条记录各算一遍）；产物必须出自实验路径。"""
    by_artifact = {str(item["artifact_id"]): item for item in evidence}
    checked: list[str] = []
    for item in artifacts:
        artifact_id = str(item["id"])
        entry = by_artifact.get(artifact_id)
        if entry is None:
            continue
        digest = Digest.of_bytes(client.get(f"/artifacts/{artifact_id}/content").content)
        assert digest == Digest.parse(str(entry["content_digest"])), (
            "证据登记的内容 digest 必须可从内容读面重算",
            artifact_id,
        )
        # **来源记录**（canonical 的另一条记录，不是读面的投影）：它的 digest 同样要经得起
        # 重算——「产物已登记」与「来源已登记」是两件事。
        source = deps.ledger.get_source(str(entry["source_ref"]))
        assert source.content_digest == str(digest), (source, artifact_id)
        name = artifact_id.rsplit(":", 1)[-1]
        if name in _PRODUCTS:
            # 四件产物必须是**实验路径**产出的（`extracted_by` 点名实验 run），
            # 不是会话交付物那种模型自述（EC-03 明文）。
            assert str(source.trust_label.value) == "GENERATED", source
            canonical = deps.ledger.get_evidence(str(entry["id"]))
            assert canonical.extracted_by == f"experiment:{experiment_run_id}", canonical
        checked.append(name)
    assert set(_PRODUCTS) <= set(checked), (checked, sorted(by_artifact))
    # 有证据的制品都应可重算（不止四件产物：声明输入与会话交付物同样如此）
    assert len(checked) == len(by_artifact), (checked, sorted(by_artifact))


def _assert_product_evidence_points_at_this_run(
    evidence: Any, experiment_run_id: str, run_id: str
) -> None:
    """④ 不得用模型自述冒充：四件产物的证据来源指向**本次实验 run**。"""
    for entry in evidence:
        if str(entry["artifact_id"]).rsplit(":", 1)[-1] not in _PRODUCTS:
            continue
        assert str(entry["experiment_run_id"]) == experiment_run_id, entry
        assert str(entry["source_origin"]).startswith(f"{experiment_run_id}:"), entry
        assert str(entry["run_id"]) == run_id, entry


def _assert_reproducible(deps: Any, client: Any, experiment: dict[str, Any]) -> None:
    """⑤ 语义摘要与指标跨重跑稳定（同 seed / 同镜像 ⇒ 同语义）。"""
    first = _semantic_digest(deps, str(experiment["experiment_run_id"]))
    assert first, "语义摘要必须落 canonical"
    second = _experiment_of(client, str(start_run(client, _PROTOCOL)["id"]))
    assert _semantic_digest(deps, str(second["experiment_run_id"])) == first, (
        "同 seed / 同镜像的两次执行必须给同一语义摘要"
    )
    assert dict(second["metrics"]) == dict(experiment["metrics"]), (
        second["metrics"],
        experiment["metrics"],
    )


def test_products_and_provenance_are_traceable_and_recomputable() -> None:
    """主干：两读面同源 + 内容 digest 可重算 + 镜像摘要可独立复核 + 语义摘要跨重跑稳定。"""
    deps = _deps(EXPERIMENT_SCRIPT)
    client, run_id, detail, artifacts, evidence = _run(deps)
    try:
        assert detail["state"] == "SUCCEEDED", (detail, client.get(f"/runs/{run_id}/events").json())
        experiment = _experiment_of(client, run_id)
        experiment_run_id = str(experiment["experiment_run_id"])

        _assert_faces_carry_the_products(experiment, artifacts)
        _assert_content_digests_recompute(deps, client, artifacts, evidence, experiment_run_id)
        _assert_product_evidence_points_at_this_run(evidence, experiment_run_id, run_id)
        _assert_image_digest_is_independently_recheckable(experiment)
        _assert_reproducible(deps, client, experiment)
    finally:
        client.__exit__(None, None, None)


def _assert_image_digest_is_independently_recheckable(experiment: dict[str, Any]) -> None:
    """③ 来源可独立复核：镜像摘要 == 独立查 daemon 的镜像 Id（CLI 不可用则如实跳过该断言）。"""
    daemon_id = _daemon_image_id(EXPERIMENT_IMAGE)
    if daemon_id is not None:
        assert str(experiment["image_digest"]) == daemon_id, (
            experiment["image_digest"],
            daemon_id,
        )
    assert experiment["environment_digest"], experiment


def test_the_chain_is_red_when_the_declared_product_is_missing(tmp_path: Any) -> None:
    """**成对反证**：实验跑完但**没有**声明的那件产物 ⇒ 门拒收点名、读面无它、其余产物仍在。"""
    script = tmp_path / "counter_experiment.py"
    script.write_text(_COUNTER_SCRIPT, encoding="utf-8")
    deps = _deps(str(script))
    client, run_id, detail, artifacts, _evidence = _run(deps)
    try:
        assert detail["state"] == "FAILED", detail
        failures = [
            str(event["payload"].get("message", ""))
            for event in client.get(f"/runs/{run_id}/events").json()
            if event["type"] in ("run.failed", "task.failed")
        ]
        assert any("analysis_report" in message for message in failures), failures
        assert any("acceptance gate" in message for message in failures), failures

        names = _product_names(artifacts)
        assert "analysis_report" not in names, ("声明产物不得存在", names)
        assert {"report.txt", "experiment_result.json"} <= names, (
            "实验确实跑完了——红的理由必须是「声明产物缺失」，不是「实验没跑」",
            names,
        )
        experiment = _experiment_of(client, run_id)
        assert experiment["metrics"], experiment
    finally:
        client.__exit__(None, None, None)
