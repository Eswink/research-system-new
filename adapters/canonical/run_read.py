"""`run.read` 的**执行实现**（GOAL-20261005-030 EC-02；与 `read_provider.py` 分列）。

**为什么单列**：`read_provider.py` 有 **450 行硬上限**（规模门），本轮再往它上面接一条
读能力就越界。拆分的切法与 `read_surface.py` 同一思路：本模块只放 `run.read` 这一条
的实现，`read_provider.py` 只保留一行委派。

**它读什么**：`RunStore`（既有 Port：`packages/application/ports/run_store.py`；
SQLite / PG 两个组合根都持有实例）。**不新造第二套查询口径** —— 与 HTTP 读面
`GET /runs/{id}` 走同一个 `get_run`。

**边界**（与既有读面同一条纪律）：

- `RunStore` 缺失 ⇒ **点名拒绝**（不返回空壳冒充「没有这个 run」）；
- run id 未知 ⇒ 点名拒绝（`InvalidInputError`），由 `RunStore` 自己抛；
- **只读**：本模块不写任何 store。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.errors import InvalidInputError


def run_read(runs: Any | None, args: dict[str, object]) -> dict[str, object]:
    """读一个 canonical run（状态 / 协议 / manifest digest）。

    字段取自 `ResearchRun` 的**既有**属性，不新造投影：`state` 是域状态机的取值，
    两个 digest 是冻结事实（`manifest_digest` 为空表示尚未冻结 —— 如实回 `null`，
    **不**回落成别的值）。
    """
    if runs is None:
        raise InvalidInputError("run_read requires a RunStore, which is not in this assembly")
    run_id = str(args.get("run_id") or "").strip()
    if not run_id:
        raise InvalidInputError("run_read requires a non-empty run_id")
    run = runs.get_run(run_id)
    return {
        "run_id": run.id.value,
        "project_id": run.project_id,
        "protocol_id": run.protocol_id,
        "state": str(run.state),
        "manifest_digest": str(run.manifest_digest) if run.manifest_digest else None,
        "manifest_semantic_digest": (
            str(run.manifest_semantic_digest) if run.manifest_semantic_digest else None
        ),
    }


__all__ = ["run_read"]
