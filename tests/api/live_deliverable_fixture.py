"""Live e2e 受控**持久化交付物**夹具（GOAL-013 EC-02 第三批，`#/insights/reports`）。

拆成独立模块有两个理由：`console_api_app.py` 撞上 450 行硬上限
（`tests/tooling/test_python_source_limits.py`），且这份夹具的**诚实边界**值得单独写清。

live app 的 Fake 链**不跑 M12 参考链**，因此实测四条 run 的 `/runs/{id}/deliverable`
全部 `available: false` ⇒ 无法演示「非空读面 → 非空渲染」。这里按同一个夹具模式
（`Artifact` + `Digest.of_bytes`，digest 由**域代码**生成）为一条**既有** run 落一份
`"{run_id}:deliverable.json"`，让读面 `available: true`。

路径与域侧一致：`services/api/routers/deliverable.py` 按 `f"{run_id}:deliverable.json"`
查 store，`packages/application/m12_reference/persistence.py` 也用同名产物
⇒ 夹具只决定**内容**，不复制任何读写逻辑。

**诚实边界**：这份交付物是**受控夹具**，不是一次真实 M12 参考链的产出。消费它的
live 用例只判「读面 → DTO → 页面」这一段，**不声称**「页面上是真实研究运行产出的报告」。
"""

from __future__ import annotations

import json

from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from services.api.composition import ApiDeps

LIVE_DELIVERABLE_PAYLOAD: dict[str, object] = {
    "objective": "live deliverable fixture: confirm the report read face renders",
    "final_answer": "fixture summary line consumed by the report page",
    "citation_count": 2,
}


def with_deliverable(deps: ApiDeps, run_id: str) -> ApiDeps:
    """为**既有** run 落一份受控 `deliverable.json`，让 `/runs/{id}/deliverable` 非空。

    挂在既有 run 上（而不是新建 run）：新建 run 会改动 `run_count` 等既有读面数字，
    干扰别的 live 用例；挂既有 run 则读面只多一个字段。
    """
    store = deps.artifacts
    if store is None:
        return deps
    payload = json.dumps({"run_id": run_id, **LIVE_DELIVERABLE_PAYLOAD}, ensure_ascii=False).encode(
        "utf-8"
    )
    store.put(
        Artifact(
            id=f"{run_id}:deliverable.json",
            digest=Digest.of_bytes(payload),
            size_bytes=len(payload),
            media_type="application/json",
            source_refs=["task:live-fixture"],
            classification="research_deliverable",
        ),
        payload,
    )
    return deps
