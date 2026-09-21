"""GOAL-010 EC-03：run 的 canonical 协议身份必须**就是**操作者点名的那份文件。

为什么这条判据存在：EC-03 的起点形态（PLAN-129 的 E-1/E-2 实测）是**声明面与执行面分家**——
登记面/测试常量指向一份协议，而 run 真正装配的是另一份。本判据把三个面钉在一起：

1. **文件自己**（YAML 里的 `id:`，从正文里读出来，不 import 被测实现）；
2. **canonical run**（`Run.protocol_id`，经 API 读面回读）；
3. **被解析的那份字节**（`Run.protocol_body` 的 sha256，读面 `protocol_body_digest`）。

**成对**：两份协议各起一次 run，两条身份必须互不相同，且各自的正文里**不得**出现对方的名字。
只返回常量 id、忽略入参 `protocol_path`、把两份文件当一份——任一形态都会红。

**不声称**（本判据的射程）：这里跑的是**默认（Fake）执行体、离线**，只证明**身份对齐**
与「新协议在控制面真的可达 `SUCCEEDED`」；「真实模型真的执行了这份协议」由 live 分支
单独取样（PLAN-129 WP4），不由本文件声称。
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
    client: TestClient, app_deps: ApiDeps, credentials: Any, protocol: str
) -> None:
    """点名哪份文件，canonical run 就得是哪份——身份 + 字节摘要 + 冻结正文三面一致。"""
    credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    detail, declared, text = _identity(client, protocol)
    assert detail["protocol_id"] == declared, detail
    assert detail["protocol_body_digest"] == str(Digest.of_bytes(text.encode("utf-8"))), detail
    frozen = app_deps.run_registry[detail["id"]].protocol_body
    assert frozen is not None, "run 必须冻结被解析的那份正文"
    assert declared in frozen.text, "冻结正文必须含它自己声明的 id"
    assert detail["state"] == "SUCCEEDED", detail


def test_the_two_protocols_do_not_collapse_to_one_identity(
    client: TestClient, credentials: Any
) -> None:
    """反证（常驻）：两条身份互不相同、正文互不出现对方的名字——判据因此不可能是常量。"""
    credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    real, real_id, real_text = _identity(client, _REAL)
    demo, demo_id, demo_text = _identity(client, _DEMO)
    assert real_id != demo_id
    assert real["protocol_id"] != demo["protocol_id"], (real, demo)
    assert real["protocol_body_digest"] != demo["protocol_body_digest"], (real, demo)
    assert demo_id not in real_text, "真实协议的正文里不得出现 demo 协议的名字"
    assert real_id not in demo_text, "demo 协议的正文里不得出现真实协议的名字"
