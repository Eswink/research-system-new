"""Control Plane API settings。"""

from __future__ import annotations

import os

_DEFAULT_DB_PATH = "data/research-os-control.db"


class ApiSettings:
    """控制面配置；来自显式构造或环境变量。"""

    def __init__(
        self,
        *,
        db_path: str = _DEFAULT_DB_PATH,
        endpoint_timeout_seconds: float = 120.0,
    ) -> None:
        if not db_path:
            raise ValueError("db_path must not be empty")
        self.db_path = db_path
        self.endpoint_timeout_seconds = endpoint_timeout_seconds

    @classmethod
    def from_env(cls) -> ApiSettings:
        return cls(
            db_path=os.environ.get("RESEARCHOS_DB_PATH", _DEFAULT_DB_PATH),
            endpoint_timeout_seconds=float(os.environ.get("RESEARCHOS_ENDPOINT_TIMEOUT", "120")),
        )
