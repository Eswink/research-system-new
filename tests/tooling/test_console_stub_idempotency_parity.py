"""替身 harness 的幂等词表必须与真中间件一致（GOAL-003 EC-05 / PLAN-20260915-068）。

`apps/web/tests/e2e/stub-idempotency.ts` 是 `services/api/middleware.py` 的**跨语言镜像**：
哪些方法要 key、哪些分析类 POST 免 key，两边必须逐项相同。镜像的价值全在"与真件一致"，
所以这里把词表钉死——漂移在 Python 套件里红，而不是让 stub 套件悄悄放行客户端漏发 key。

（同族守卫：`tests/tooling/test_console_toolpack_fixtures.py` 守 live fixture 与域代码同步。）
"""

from __future__ import annotations

import re
from pathlib import Path

from services.api.middleware import _ANALYSIS_ACTIONS, _MUTATING_METHODS

ROOT = Path(__file__).resolve().parents[2]
STUB = ROOT / "apps" / "web" / "tests" / "e2e" / "stub-idempotency.ts"


def _ts_string_array(source: str, name: str) -> set[str]:
    """取出 `export const NAME = ["a", "b"] as const;` 里的字符串项。"""
    match = re.search(rf"{name}\s*=\s*\[(.*?)\]", source, flags=re.DOTALL)
    assert match is not None, f"{name} not found in {STUB.name}"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def test_stub_method_and_action_vocabularies_match_the_real_middleware() -> None:
    source = STUB.read_text(encoding="utf-8")

    stub_methods = _ts_string_array(source, "MUTATING_METHODS")
    assert stub_methods == set(_MUTATING_METHODS), stub_methods

    stub_actions = _ts_string_array(source, "ANALYSIS_ACTIONS")
    assert stub_actions == set(_ANALYSIS_ACTIONS), stub_actions
    # 空集合会让"豁免"退化成"全部豁免"，两边都不该出现这种静默失效。
    assert stub_actions, "analysis exemption list must not be empty"


def test_stub_problem_body_matches_the_middleware_shape() -> None:
    """`_problem()` 的五个字段（含空 instance）是客户端解析契约的一部分。"""
    source = STUB.read_text(encoding="utf-8")
    for field in ("type", "title", "status", "detail", "instance"):
        assert f"{field}:" in source, field
    assert '"mutating requests require Idempotency-Key"' in source
    assert '"Idempotency-Key was used with a different request payload"' in source
