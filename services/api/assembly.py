"""Composition helpers: DSN detection, sqlite opening, pricing loading, policy.

Kept out of composition.py to honor the Python 300-line source limit while
remaining inside the allowed composition boundary.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from adapters.contracts.pricing_loaders import load_pricing_table
from adapters.sqlite.db import connect as sqlite_connect
from packages.application.cost.pricing import unpriced_table
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from services.api.settings import ApiSettings

# 最近一次定价表加载的降级原因;None = 正常加载(见 `_load_pricing`)。
_LAST_PRICING_ERROR: str | None = None


def _is_postgres_dsn(dsn: str | None) -> bool:
    return bool(dsn and dsn.strip().startswith("postgresql"))


def _open_sqlite(db_path: str) -> Any:
    path = Path(db_path)
    if str(path) != ":memory:":
        os.makedirs(path.parent, exist_ok=True)
    return sqlite_connect(db_path)


def _load_pricing() -> Any:
    """版本化定价表(composition root;缺失/损坏 → unpriced fail-open)。

    降级是**可观测**的:回落时 `unpriced_table()` 与文件版
    `unpriced_v1` 现在有相同 digest,所以"配置缺失"与"显式无价格"在摘要上
    不可区分——这是有意的(两者语义相同:没有任何价格)。真正需要区分的是
    "配置损坏"这一运维事实,因此这里保留异常类型信息到 `last_pricing_error`
    供 composition root 上报,而不是静默丢弃(M15 复审:裸 except 使
    pricing.yaml 里的一个拼写错误可以零信号地抹掉全部成本报告)。
    """
    global _LAST_PRICING_ERROR
    try:
        table = load_pricing_table("examples/config/pricing.yaml")
    except Exception as error:
        _LAST_PRICING_ERROR = f"{type(error).__name__}: pricing config unusable, using unpriced_v1"
        return unpriced_table()
    _LAST_PRICING_ERROR = None
    return table


def last_pricing_error() -> str | None:
    """最近一次定价表加载的降级原因(None = 正常加载)。"""
    return _LAST_PRICING_ERROR


def _endpoint_url_policy(effective: ApiSettings) -> EndpointUrlPolicy:
    """localhost/private/link-local 同开关(显式开发放行,默认 fail-closed)。"""
    return EndpointUrlPolicy(
        allow_localhost=effective.allow_localhost_endpoints,
        allow_private=effective.allow_localhost_endpoints,
        allow_link_local=effective.allow_localhost_endpoints,
    )
