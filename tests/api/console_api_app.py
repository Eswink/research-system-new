"""Console 集成测试专用 FastAPI 装配（PLAN-20260908-034 T30）。

复用 tests/api/run_fixtures 的 Fake Port 装配（run_fixtures.make_run_ready_deps），
通过真实 uvicorn HTTP 服务驱动浏览器 e2e：API 层真实，外部模型/工具为确定性替身。
不依赖真实凭据或付费 LLM。

运行：uv run --frozen --no-sync python -m uvicorn tests.api.console_api_app:app \
      --host 127.0.0.1 --port 8011
"""

from __future__ import annotations

from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from services.api.app import create_app
from services.api.composition import ApiDeps
from tests.api.run_fixtures import make_run_ready_deps

# live 制品 diff 正向链需要 store 里有真实内容：两份受控 JSON（执行前/后），
# 只服务 PLAN-047 的 live e2e，不进入任何生产路径。
LIVE_DIFF_ARTIFACTS: tuple[tuple[str, bytes], ...] = (
    ("live-fixture:before.json", b'{\n  "status": "running",\n  "attempts": 1\n}\n'),
    ("live-fixture:after.json", b'{\n  "status": "succeeded",\n  "attempts": 1\n}\n'),
)


def _seed_artifact(artifact_id: str, payload: bytes) -> Artifact:
    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(payload),
        size_bytes=len(payload),
        media_type="application/json",
        source_refs=["task:live-fixture"],
        classification="execution_result",
    )


def _with_artifacts(deps: ApiDeps) -> ApiDeps:
    """控制面只读链与 Fake store 共享实例：放入 live diff 的两份受控内容。"""
    store = deps.artifacts
    if store is None:
        return deps
    for artifact_id, payload in LIVE_DIFF_ARTIFACTS:
        store.put(_seed_artifact(artifact_id, payload), payload)
    return deps


# 单一进程内装配：SQLite in-memory + Fake runtime/gateway/ledger。
app = create_app(_with_artifacts(make_run_ready_deps()))
