"""live run 的**显式开关**（D-11 / GOAL-017 EC-02）——单独一个模块的理由是**行数门禁**。

`tests/e2e/live_run_support.py` 贴着 450 行硬上限（448/450），开关这两件小东西放进去会越界；
判据与门禁的实际约束是「**环境读取点全仓唯一**」，所以这里做成一个**单一职责**的小模块：

- `live_e2e_switch_enabled()`：**全仓唯一**的环境读取点（`tests/architecture/python/`
  的 `test_live_switch_is_single_source.py` 按 **AST** 断言这一点）；
- `live_run_switch_off_reason()`：开关关着时的**唯一一份**拒跑文案（措辞与
  `evaluate_live_run_gate` 里那条未满足条件**同源**：同一个常量名）。

**边界**：产品层不读这个开关（`packages/application/**` 零 `os.environ`）——门的 `live_switch`
是**必填**参数，值由调用方从这里取一次后传入。开关只决定「**进不进 run**」，
**不**参与 `tests/egress_guard.py` 的出网放行面（放行面仍是 `requires_live_llm` 一个 marker）。
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from packages.application.model_relay.live_run_gate import LIVE_RUN_SWITCH


def live_e2e_switch_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """live run 的**显式开关**：值必须**恰为** `1`（与 `RESEARCHOS_REQUIRE_DOCKER` 同形态）。

    其余取值（含 `"true"` / `"yes"` / `"0"` / `" 1"`）一律算**关**——开关的语义要能一眼判，
    不做真值解析。`environ` 可注入（判据用），缺省读进程环境。
    `LIVE_RUN_SWITCH` 从产品侧常量导入 ⇒ **名字只有一个声明点**。
    """
    source = os.environ if environ is None else environ
    return source.get(LIVE_RUN_SWITCH) == "1"


def live_run_switch_off_reason() -> str:
    """开关关着时的拒跑理由（**唯一一份文案**：走门与不走门的 live 模块共用）。

    `skip` 不是 PASS：理由必须**点名缺的东西**。
    """
    return f"live run skipped: live run switch is not on (set {LIVE_RUN_SWITCH}=1 to open)"


__all__ = ["live_e2e_switch_enabled", "live_run_switch_off_reason"]
