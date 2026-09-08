"""Console 集成测试专用 FastAPI 装配（PLAN-20260908-034 T30）。

复用 tests/api/run_fixtures 的 Fake Port 装配（run_fixtures.make_run_ready_deps），
通过真实 uvicorn HTTP 服务驱动浏览器 e2e：API 层真实，外部模型/工具为确定性替身。
不依赖真实凭据或付费 LLM。

运行：uv run --frozen --no-sync python -m uvicorn tests.api.console_api_app:app \
      --host 127.0.0.1 --port 8011
"""

from __future__ import annotations

from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps

# 单一进程内装配：SQLite in-memory + Fake runtime/gateway/ledger。
app = create_app(make_run_ready_deps())
