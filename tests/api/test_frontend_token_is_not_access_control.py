"""**对抗性自检**：前端 token 面**不是访问控制**（GOAL-20260927-021 EC-04）。

本文件与既有判据的分工（**不重复、不顶替**）：

- `tests/api/test_security_scan.py`：判 `apps/web/src/**` **零**浏览器持久层写入
  （无条件字面量断言）⇒ 本文件**引用**其结论，**不**重写它。
- `apps/web/tests/unit/control-plane-token.test.ts`：判前端**携带行为**
  （写请求带 / 读请求不带 / 关闭态不加空头）与 token 模块的持久化面零命中
  （含**剥注释**与两条反向对照）⇒ 本文件**不**重复。
- **本文件补的是后端这一侧**：证明**绕过前端**直接调 API 时，
  权限判定**完全在后端**、**与前端是否存在无关** —— 即「前端 token 面是便利面」。

三条：

- **(a) 仅内存**：token 模块**不暴露**任何持久化通道（结构：导出面里没有读写浏览器存储的入口）。
- **(b) 后端独立成立**：不带 token ⇒ 401；带对 token ⇒ 通过。**未经任何前端代码**。
- **(c) 前端不是判定点**：前端源码里没有「依据 token 存在与否决定是否放行某操作」的授权逻辑
  ——token 只影响**是否附上请求头**。

**凭据纪律**：token 为**本文件内构造的合成假值**，不从环境读取、不落盘、不进日志。
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.composition import ApiDeps
from services.api.middleware import (
    CONTROL_PLANE_PRINCIPAL_ID_ENV,
    CONTROL_PLANE_TOKEN_ENV,
)

# 合成夹具值（不是真实凭据；见模块 docstring）。
_FIXTURE_TOKEN = "fixture-" + "j" * 24
_FIXTURE_PRINCIPAL_ID = "convenience-probe"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOKEN_MODULE = _REPO_ROOT / "apps" / "web" / "src" / "api" / "controlPlaneToken.ts"
_WEB_SRC = _REPO_ROOT / "apps" / "web" / "src"


class TestTheBackendIsTheOnlyDecisionPoint:
    """(b) + (c)：判定在后端，前端状态不参与。"""

    def test_without_a_token_the_write_is_rejected(self, authed_client: TestClient) -> None:
        """**不经过前端**直接调 API：不带 token ⇒ 401。"""
        response = authed_client.post(
            "/projects",
            json={"id": "convenience-probe-a", "name": "probe"},
            headers={"Idempotency-Key": "convenience-probe-a"},
        )
        assert response.status_code == 401, response.text

    def test_with_a_token_the_same_write_succeeds(self, authed_client: TestClient) -> None:
        """**同一个请求**（不经过前端）带上 token ⇒ 通过。

        与上一条**成对**：两者都不经过任何前端代码，差别**只在**请求头
        ⇒ 判定点**只在后端**。
        """
        response = authed_client.post(
            "/projects",
            json={"id": "convenience-probe-b", "name": "probe"},
            headers={
                "Authorization": f"Bearer {_FIXTURE_TOKEN}",
                "Idempotency-Key": "convenience-probe-b",
            },
        )
        assert response.status_code == 201, response.text

    def test_the_backend_does_not_read_any_frontend_state(self) -> None:
        """**结构**：认证中间件**不引用**任何前端模块 / 浏览器存储概念。

        ⇒ 「前端有没有配 token」这件事**无法**影响后端判定（后端读的是环境变量快照）。
        """
        source = (_REPO_ROOT / "services" / "api" / "middleware.py").read_text(encoding="utf-8")
        for forbidden in ("localStorage", "sessionStorage", "apps/web", "window.", "document."):
            assert forbidden not in source, (
                f"认证中间件出现了前端概念 `{forbidden}` ⇒ 判定面与前端耦合了"
            )
        # 反向对照：确实读到了中间件源码（否则空内容也会「通过」）。
        assert CONTROL_PLANE_TOKEN_ENV in source, "读到了认证中间件的源码"

    def test_a_rejected_write_leaves_no_trace_in_canonical(self, authed_client: TestClient) -> None:
        """前端**能输入 token** 不等于有授权：被拒的写请求**什么都没写**。

        （这是「便利面 ≠ 访问控制」最实际的一条后果：没有凭据就是没有写能力。）
        """
        before = authed_client.get("/projects").json()
        rejected = authed_client.post(
            "/projects",
            json={"id": "convenience-probe-c", "name": "probe"},
            headers={"Idempotency-Key": "convenience-probe-c"},
        )
        assert rejected.status_code == 401
        after = authed_client.get("/projects").json()
        assert len(after) == len(before), "被拒的写请求改变了 canonical 状态"
        assert all(item["id"] != "convenience-probe-c" for item in after)


class TestTheFrontendTokenModuleHasNoPersistenceChannel:
    """(a) 仅内存：结构上**没有**持久化通道（不只是「没调用」）。"""

    def test_the_module_does_not_reference_browser_storage_apis(self) -> None:
        """token 模块的**代码**里不出现任何浏览器存储 API（剥注释后判）。

        **与既有前端判据的分工**：既有 `control-plane-token.test.ts` 也扫这个面。
        本文件**不替代**它 —— 本判据存在的理由是**后端侧**：
        EC-04 要能在**后端测试套件**里独立地发现「前端开始持久化」这一回归，
        而不必依赖 web 门是否被跑到。两处判据**同一方向、互为冗余**，不是重复实现：
        一处是前端门（含剥注释与两条反向对照），一处是后端门（本地口径）。
        """
        source = _TOKEN_MODULE.read_text(encoding="utf-8")
        code = _strip_comments(source)
        for forbidden in (
            "localStorage",
            "sessionStorage",
            "indexedDB",
            "document.cookie",
            "window.name",
        ):
            assert forbidden not in code, f"token 模块的代码触碰了持久化面：{forbidden}"
        # 反向对照：剥注释**确实**在起作用，且读到了可执行代码。
        assert "浏览器存储" in source, "决策说明应提到被否决的方案"
        assert "浏览器存储" not in code, "剥注释后不该再含注释里的措辞"
        assert "subscribeControlPlaneToken" in code, "读到了模块的可执行代码"

    def test_the_module_is_the_only_place_that_holds_the_token(self) -> None:
        """**单一持有者**：`apps/web/src` 里除该模块外，没有别处保存 token 值。

        （若别处也存，就会有多份副本 ⇒ 「仅内存且随页面消失」这条保证不成立。）
        """
        holders = []
        for path in _WEB_SRC.rglob("*.ts*"):
            if path == _TOKEN_MODULE:
                continue
            text = path.read_text(encoding="utf-8")
            if re.search(r"let\s+\w*[Tt]oken\w*\s*:\s*string", text):
                holders.append(str(path.relative_to(_REPO_ROOT)))
        assert holders == [], f"token 值在别处也有副本（破坏「仅内存单一持有」）：{holders}"


def _strip_comments(text: str) -> str:
    """剥掉块注释与行注释（与前端判据同纪律：只判**代码**，不判注释里的决策说明）。"""
    without_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", without_block)


@pytest.fixture
def authed_client(run_ready_deps: ApiDeps, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """认证**开启**的真实控制面（token 经环境变量注入，装配期快照）。

    注意：这里**没有**任何前端参与——正是本 EC 要证明的「判定在后端」。
    """
    monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, _FIXTURE_TOKEN)
    monkeypatch.setenv(CONTROL_PLANE_PRINCIPAL_ID_ENV, _FIXTURE_PRINCIPAL_ID)
    with TestClient(create_app(run_ready_deps)) as test_client:
        yield test_client
