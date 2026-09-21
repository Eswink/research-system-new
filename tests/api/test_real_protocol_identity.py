"""GOAL-010 EC-03：run 的 canonical 协议身份必须**就是**操作者点名的那份文件。

为什么这条判据存在：EC-03 的起点形态（PLAN-129 的 E-1/E-2 实测）是**声明面与执行面分家**——
登记面/测试常量指向一份协议，而 run 真正装配的是另一份。本判据把三个面钉在一起：

1. **文件自己**（YAML 里的 `id:`，从正文里读出来，不 import 被测实现）；
2. **canonical run**（`Run.protocol_id`，经**持久化读面**回读）；
3. **被解析的那份字节**（`protocol_body` 的 sha256，读面 `protocol_body_digest` + 库里的冻结正文）。

两个面分开判，各在**能测到它的装配**上判：

- **身份**（前两条用例）：用 `runs_store` 优先的读面（`services/api/run_access.py`）——只读内存
  注册表会把「能不能从库里恢复」这一半悄悄放过。
- **可达性**（第三条用例）：新合约在产品路径上真的被满足（终态 `SUCCEEDED` + 交付物按声明名
  登记）。这一条需要默认装配（`client`）——`run_ready` 装配按设计只冻结 Manifest、不跑到达成，
  两者混在一处会让其中一半悄悄失效（实测过：混着写时该装配恒 `FAILED`）。

**成对**：两份协议各起一次 run，两条身份必须互不相同，且各自的正文里**不得**出现对方的名字。
只返回常量 id、忽略入参 `protocol_path`、把两份文件当一份——任一形态都会红。

**不声称**（本判据的射程）：这里跑的是 **Fake 执行体、离线**，只证明**身份对齐**与
**合约可达**；「真实模型真的执行了这份协议」由 live 分支单独取样（PLAN-129 WP4），
不由本文件声称。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from packages.domain.core import Digest
from services.api.catalog import read_protocol_text
from services.api.composition import ApiDeps

#: 两份**不同**的协议：EC-03 新增的真实协议，与它并存（不是取代）的 demo 协议。
_REAL = "real_research_task_v1.yaml"
_DEMO = "console_demo_research_v1.yaml"
#: 新合约 `real_research_deliverable` 声明的 artifact 名（字面量：判据不 import 被测实现）。
_DECLARED = "analysis_report"
#: 该协议声明的输入制品 id（协议文件里的 `inputs:` 逐字值）。
_INPUT_BRIEF = "input-brief:real_research_v1"


def _declared_id(path: str) -> str:
    """文件自己声明的 id（判据从正文里**读**，不 import 被测实现的常量）。"""
    for line in read_protocol_text(path).splitlines():
        if line.startswith("id:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"{path} 没有声明 id")


def _identity(client: TestClient, protocol: str) -> tuple[dict[str, Any], str, str]:
    """起一次 run 并回读它的 canonical 身份 ⇒ (run 详情, 文件声明的 id, 协议正文)。"""
    started = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": protocol},
        headers={"Idempotency-Key": f"protocol-identity-{uuid.uuid4()}"},
    )
    assert started.status_code == 200, started.text
    detail = cast(dict[str, Any], client.get(f"/runs/{started.json()['id']}").json())
    return detail, _declared_id(protocol), read_protocol_text(protocol)


@pytest.mark.parametrize("protocol", [_REAL, _DEMO])
def test_the_run_identity_is_the_file_the_operator_named(
    run_ready_client: TestClient, run_ready_deps: ApiDeps, credentials: Any, protocol: str
) -> None:
    """点名哪份文件，canonical run 就得是哪份——身份 + 字节摘要 + 库里的冻结正文三面一致。

    **不判终态**：这一条判的是「run 装配的是哪份协议」，与它跑到哪一步无关——
    可达性由 `test_the_real_protocol_reaches_succeeded_on_the_product_path` 单独判。
    """
    credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    detail, declared, text = _identity(run_ready_client, protocol)
    assert detail["protocol_id"] == declared, detail
    assert detail["protocol_body_digest"] == str(Digest.of_bytes(text.encode("utf-8"))), detail
    store = run_ready_deps.runs_store
    assert store is not None, "本判据要求 canonical run store 在场"
    frozen = store.get_run(detail["id"]).protocol_body
    assert frozen is not None, "run 必须冻结被解析的那份正文（重启续跑要用它）"
    assert declared in frozen.text, "冻结正文必须含它自己声明的 id"


def test_the_two_protocols_do_not_collapse_to_one_identity(
    run_ready_client: TestClient, credentials: Any
) -> None:
    """反证（常驻）：两条身份互不相同、正文互不出现对方的名字——判据因此不可能是常量。"""
    credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    real, real_id, real_text = _identity(run_ready_client, _REAL)
    demo, demo_id, demo_text = _identity(run_ready_client, _DEMO)
    assert real_id != demo_id
    assert real["protocol_id"] != demo["protocol_id"], (real, demo)
    assert real["protocol_body_digest"] != demo["protocol_body_digest"], (real, demo)
    assert demo_id not in real_text, "真实协议的正文里不得出现 demo 协议的名字"
    assert real_id not in demo_text, "demo 协议的正文里不得出现真实协议的名字"


def test_the_real_protocol_reaches_succeeded_on_the_product_path(
    client: TestClient, credentials: Any
) -> None:
    """新合约在**产品路径**（默认装配）上真的可达：终态 `SUCCEEDED` + 交付物按声明名登记。

    读面用 `/runs/{id}/evidence`：本装配**没有** artifact store（`/artifacts` 如实 503），
    而 evidence 的 `source_ref` 就是产物/来源的名字，够判「交付物用了合约声明的名字」
    与「覆盖门由**声明输入**满足」。

    这是 live 分支的**前置事实**：把「协议 / 合约 / 能力面是否走得通」先离线测掉，
    live 调用就只花在「真实执行体」这一步上（承 PLAN-129 的调用纪律）。
    """
    credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    detail, _, _ = _identity(client, _REAL)
    assert detail["state"] == "SUCCEEDED", detail
    refs = [str(item["source_ref"]) for item in client.get(f"/runs/{detail['id']}/evidence").json()]
    assert any(ref.endswith(f":{_DECLARED}") for ref in refs), refs
    assert _INPUT_BRIEF in refs, refs
