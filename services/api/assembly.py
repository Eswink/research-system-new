"""Composition helpers: DSN detection, sqlite opening, pricing loading, policy.

Kept out of composition.py to honor the Python 300-line source limit while
remaining inside the allowed composition boundary.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from adapters.contracts.pricing_loaders import load_pricing_table
from adapters.sqlite.pool import ThreadLocalConnection
from packages.application.cost.pricing import unpriced_table
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from services.api.settings import ApiSettings

# 最近一次定价表加载的降级原因;None = 正常加载(见 `_load_pricing`)。
_LAST_PRICING_ERROR: str | None = None


def _is_postgres_dsn(dsn: str | None) -> bool:
    return bool(dsn and dsn.strip().startswith("postgresql"))


def _open_sqlite(db_path: str) -> Any:
    """控制面的 SQLite 入口：**每线程一条连接**（GOAL-004 cycle 5 = EC-05）。

    文件库不再把一条连接发给所有线程（含守护线程）；`:memory:` 仍共用一条
    （SQLite 语义：内存库属于连接），见 `adapters/sqlite/pool.py`。
    """
    path = Path(db_path)
    if str(path) != ":memory:":
        os.makedirs(path.parent, exist_ok=True)
    return ThreadLocalConnection(db_path)


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
    """localhost/private/link-local 同开关（显式开发放行，默认 fail-closed）。"""
    return EndpointUrlPolicy(
        allow_localhost=effective.allow_localhost_endpoints,
        allow_private=effective.allow_localhost_endpoints,
        allow_link_local=effective.allow_localhost_endpoints,
    )


def sqlite_artifact_blob_dir(effective: ApiSettings) -> str:
    """内容寻址 blob 目录：显式配置优先；默认落在 dev DB 同级的
    `artifact-blobs/`（`data/research-os-control.db` → `data/artifact-blobs`），
    与 DB 文件同级意味着重启后 artifact 内容仍可下载（PLAN-040 WP-A）。"""
    if effective.artifact_blob_dir:
        return effective.artifact_blob_dir
    db = Path(effective.db_path)
    base = db.parent if str(db) != ":memory:" else Path(".")
    return str(base / "artifact-blobs")


def build_sqlite_draft_service(connection: Any) -> Any:
    """构建协议草稿服务（SQLite 开发路径；PG 路径见 pg_composition）。"""
    from adapters.contracts.protocol_text_loader import load_protocol_from_text
    from adapters.sqlite.protocol_draft_store import SqliteProtocolDraftStore
    from packages.application.protocol_authoring.service import DraftService, DraftTemplates
    from services.api.routers.protocol_drafts import default_templates

    store = SqliteProtocolDraftStore(connection=connection)
    templates: DraftTemplates = default_templates()
    return DraftService(store, templates, text_loader=load_protocol_from_text)


def policy_bindings() -> dict[str, Any]:
    """策略面装配 kwargs（policy + 求值器同源；SQLite/PG/夹具三处共用）。

    policy.yaml 缺失/不可解析 → 两者都是 None（调用方按诚实缺口处理，不伪造
    默认策略）。
    """
    from packages.application.policy.native import NativePolicyEvaluator
    from services.api.catalog import load_policy_definition

    policy = load_policy_definition()
    return {
        "policy": policy,
        "policy_evaluator": NativePolicyEvaluator(policy) if policy is not None else None,
    }
