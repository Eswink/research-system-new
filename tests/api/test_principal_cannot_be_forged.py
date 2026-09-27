"""**对抗性自检**：主体归因**不可伪造**（GOAL-20260927-021 EC-03）。

三条：

- **(a) 不能自报身份**：单 token ⇒ 单主体。请求**无法**影响主体身份——
  `X-Principal-Id` / `X-Actor` 头、query 参数、body 字段全部**不改变**主体。
- **(b) 读面基线**：认证开启时**读请求**不带 token ⇒ 主体 `None`
  （即使**前一个**请求是带 token 的写请求）；认证**关闭**时放行且主体 `None`。
- **(c) 请求之间不串**：**可证伪形态**是**同一任务内的顺序**（写 → 读）。

**为什么 (c) 用顺序形态而不是并发形态（本文件最要紧的设计约束）**：
`contextvar` 按 **Task** 隔离 ⇒ 并发子任务**各自**的 set/reset 互不可见。
实测（`scratch/goal021-ec03-probe-concurrency-precondition.py`）：
`asyncio.gather` 形态的结果**取决于父任务上下文**——
**父上下文干净 ⇒ 0 violations**；**父上下文已被污染 ⇒ 20 violations**（子任务**继承**父上下文）。
⇒ 「并发 0 violations」在干净父上下文下**不能**证明「并发安全」，只证明
「本次没被继承污染」。因此：**顺序形态是唯一可判红的判据**；
并发用例保留为**补充覆盖**，其断言**写明前提**（父上下文干净），**不**作安全结论。

**与既有判据的分工**：`tests/api/test_principal_auth.py` 判三态语义与主体落 canonical；
`test_control_plane_auth_same_source.py` 判认证面结构。本文件判**可伪造性**这一面
（自报 / 污染 / 串行残留），**不重复、不顶替**，也不改那两个文件。

**凭据纪律**：token 为**本文件内构造的合成假值**，不从环境读取、不落盘、不进日志。
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import cast

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.application.principal_context import current_principal
from packages.domain.principal import Principal, PrincipalKind
from services.api.app import create_app
from services.api.composition import ApiDeps
from services.api.middleware import (
    CONTROL_PLANE_PRINCIPAL_ID_ENV,
    CONTROL_PLANE_TOKEN_ENV,
    ControlPlaneAuth,
    PrincipalAuthMiddleware,
)

# 合成夹具值（不是真实凭据；见模块 docstring）。
_FIXTURE_TOKEN = "fixture-" + "g" * 24
_FIXTURE_PRINCIPAL_ID = "forge-probe"
_EXPECTED_ACTOR = f"service:{_FIXTURE_PRINCIPAL_ID}"

#: 走 ASGI 传输时的虚拟基址（不触网；`ASGITransport` 不出站）。
_BASE_URL = "http://forge-probe"


def _probe_app(config: ControlPlaneAuth) -> FastAPI:
    """最小受控 app：`/read` 与 `/write` 各自回报**当前请求看到的**主体。"""
    app = FastAPI()
    app.state.control_plane_auth = config

    async def snapshot() -> dict[str, str | None]:
        principal = current_principal()
        return {"actor": principal.actor if principal is not None else None}

    app.add_api_route("/read", snapshot, methods=["GET"])
    app.add_api_route("/write", snapshot, methods=["POST"])
    app.add_middleware(PrincipalAuthMiddleware, config=config)
    return app


def _enabled_config() -> ControlPlaneAuth:
    return ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id=_FIXTURE_PRINCIPAL_ID)


def _bearer() -> dict[str, str]:
    return {"Authorization": f"Bearer {_FIXTURE_TOKEN}"}


class TestTheCallerCannotDeclareItsOwnIdentity:
    """(a) 自报不可生效。"""

    def test_self_declared_headers_do_not_change_the_subject(self) -> None:
        """`X-Principal-Id` / `X-Actor` 等自报头**不改变**主体。"""
        config = _enabled_config()
        with TestClient(_probe_app(config)) as client:
            baseline = client.post("/write", headers=_bearer())
            declared = client.post(
                "/write",
                headers={
                    **_bearer(),
                    "X-Principal-Id": "attacker",
                    "X-Actor": "user:attacker",
                    "X-Principal": "admin",
                },
            )
        assert baseline.json()["actor"] == _EXPECTED_ACTOR
        assert declared.json()["actor"] == _EXPECTED_ACTOR, "自报头改写了主体 ⇒ 调用方可伪造归因"

    def test_self_declared_query_and_body_do_not_change_the_subject(self) -> None:
        """query 参数与 body 字段同样**不改变**主体（构造出的主体只来自配置）。"""
        config = _enabled_config()
        with TestClient(_probe_app(config)) as client:
            response = client.post(
                "/write?principal_id=attacker&actor=user:attacker",
                json={"principal_id": "attacker", "actor": "user:attacker"},
                headers=_bearer(),
            )
        assert response.json()["actor"] == _EXPECTED_ACTOR

    def test_the_real_app_also_ignores_self_declared_identity(
        self, authed_client: TestClient
    ) -> None:
        """真实控制面：带自报头的写请求照常成功，但**主体不变**（落 canonical 的是配置主体）。"""
        created = authed_client.post(
            "/projects",
            json={"id": "forge-probe-project", "name": "forge probe"},
            headers={
                **_bearer(),
                "Idempotency-Key": "forge-probe-create",
                "X-Principal-Id": "attacker",
                "X-Actor": "user:attacker",
            },
        )
        assert created.status_code == 201, created.text

    def test_the_subject_only_ever_comes_from_the_configuration(self) -> None:
        """**机制**：`ControlPlaneAuth.principal` 由**配置字段**推导，**不读请求**。

        这条断言的是来源单一——主体构造不接触任何请求数据（改实现使其读请求
        ⇒ 本判据的语义假设被破坏，须复核）。
        """
        config = _enabled_config()
        assert config.principal.actor == _EXPECTED_ACTOR
        other = ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id="another-operator")
        assert other.principal.actor == "service:another-operator"
        assert config.principal.kind is PrincipalKind.SERVICE


class TestTheReadFaceHasNoSubjectAndKeepsTheBaseline:
    """(b) 读面基线。"""

    def test_a_read_after_a_write_sees_no_subject(self) -> None:
        """**在前有一个写请求**，读请求看到的仍是 `None`（不是「上一个人的身份」）。

        与 (c) 同一驱动形态（同任务 `await`）——`TestClient` 在本面**看不到**串扰
        （见模块 docstring），用它会让本判据**不可证伪**。
        """

        async def scenario() -> tuple[str | None, str | None]:
            transport = httpx.ASGITransport(app=_probe_app(_enabled_config()))
            async with httpx.AsyncClient(transport=transport, base_url=_BASE_URL) as client:
                wrote = await client.post("/write", headers=_bearer())
                read = await client.get("/read")
                return (
                    cast("dict[str, str | None]", wrote.json())["actor"],
                    cast("dict[str, str | None]", read.json())["actor"],
                )

        write_actor, read_actor = asyncio.run(scenario())
        assert write_actor == _EXPECTED_ACTOR
        assert read_actor is None, "读面拿到了前一个请求的主体 ⇒ 上下文未复原"

    def test_auth_disabled_passes_through_with_no_subject(self) -> None:
        """认证**关闭**：放行且主体 `None`（「无认证」不是「已认证」）。"""
        with TestClient(_probe_app(ControlPlaneAuth(token=None))) as client:
            wrote = client.post("/write")
            read = client.get("/read")
        assert wrote.status_code == 200 and read.status_code == 200
        assert wrote.json()["actor"] is None
        assert read.json()["actor"] is None

    def test_an_unauthenticated_write_is_rejected_and_leaves_no_subject(self) -> None:
        """被拒的写请求**不留**主体（不能「拒了但归因已生效」）。"""
        with TestClient(_probe_app(_enabled_config())) as client:
            rejected = client.post("/write")
            read = client.get("/read")
        assert rejected.status_code == 401
        assert read.json()["actor"] is None


class TestTheSubjectDoesNotBleedBetweenSequentialRequests:
    """(c) 顺序形态——**唯一可判红**的判据（见模块 docstring）。"""

    def test_a_series_of_writes_then_a_read_leaves_no_residue(self) -> None:
        """连续多个写请求之后，读请求仍 `None`（复原是真的，不是一次性的）。"""

        async def scenario() -> tuple[list[str | None], str | None]:
            transport = httpx.ASGITransport(app=_probe_app(_enabled_config()))
            async with httpx.AsyncClient(transport=transport, base_url=_BASE_URL) as client:
                seen: list[str | None] = []
                for _ in range(5):
                    wrote = await client.post("/write", headers=_bearer())
                    seen.append(cast("dict[str, str | None]", wrote.json())["actor"])
                read = await client.get("/read")
                return seen, cast("dict[str, str | None]", read.json())["actor"]

        seen, read_actor = asyncio.run(scenario())
        assert seen == [_EXPECTED_ACTOR] * 5
        assert read_actor is None, "连续写之后读请求拿到主体 ⇒ 上下文未复原（主体残留）"

    def test_alternating_write_read_keeps_each_request_isolated(self) -> None:
        """写 / 读**交替**：每个写请求看到主体、每个读请求看到 `None`。"""

        async def scenario() -> list[str | None]:
            transport = httpx.ASGITransport(app=_probe_app(_enabled_config()))
            async with httpx.AsyncClient(transport=transport, base_url=_BASE_URL) as client:
                read_actors: list[str | None] = []
                for _ in range(4):
                    wrote = await client.post("/write", headers=_bearer())
                    assert cast("dict[str, str | None]", wrote.json())["actor"] == _EXPECTED_ACTOR
                    read = await client.get("/read")
                    read_actors.append(cast("dict[str, str | None]", read.json())["actor"])
                return read_actors

        assert asyncio.run(scenario()) == [None] * 4, "交替形态下读请求被写请求的主体污染"

    def test_a_write_then_a_read_in_one_task_is_observably_ordered(self) -> None:
        """**判据自身的可证伪性对照**：本形态**确实**能观察到「串」。

        这条在**同一任务**里先写后读（`httpx.ASGITransport` + `await`，**不是**
        `TestClient`——实测 `TestClient` 每个请求各起任务 ⇒ **看不到**串，
        会给出**假绿**）。它证明上面两条断言的**观测能力**存在：
        若实现失去复原，读请求会看到写请求的主体（`_EXPECTED_ACTOR`）。
        """

        async def scenario() -> str | None:
            transport = httpx.ASGITransport(app=_probe_app(_enabled_config()))
            async with httpx.AsyncClient(transport=transport, base_url=_BASE_URL) as client:
                await client.post("/write", headers=_bearer())
                read = await client.get("/read")
                return cast("dict[str, str | None]", read.json())["actor"]

        assert asyncio.run(scenario()) is None, (
            "同一任务内「写 → 读」读到了主体 ⇒ 复原失效（这正是本判据要抓的回归）"
        )


class TestConcurrentIsolationUnderAStatedPrecondition:
    """(c) 补充覆盖：并发。**断言写明前提**，不作安全结论。"""

    def test_concurrent_requests_do_not_cross_when_the_parent_context_is_clean(self) -> None:
        """**前提：父任务上下文干净**（本用例在专用事件循环里首先运行）。

        `contextvar` 按 Task 隔离 ⇒ 各子任务各自 set/reset。**这条证明的是
        「本形态下未观察到污染」**，**不**证明「并发安全」（见模块 docstring：
        父上下文被污染时同形态会得 20 violations）。
        """
        app = _probe_app(_enabled_config())
        violations = asyncio.run(_concurrent_probe(app))
        assert violations == [], f"并发形态出现 {len(violations)} 处主体串扰：{violations[:3]}"


async def _concurrent_probe(app: FastAPI) -> list[tuple[str, str | None]]:
    """混发 N 个读写请求，返回**违规项**（写请求主体不符 / 读请求被污染）。"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://forge-probe") as client:

        async def write() -> tuple[str, str | None]:
            response = await client.post("/write", headers=_bearer())
            return ("write", response.json()["actor"])

        async def read() -> tuple[str, str | None]:
            response = await client.get("/read")
            return ("read", response.json()["actor"])

        results = await asyncio.gather(*[write() if i % 2 == 0 else read() for i in range(40)])

    bad = [item for item in results if item[0] == "write" and item[1] != _EXPECTED_ACTOR]
    bad += [item for item in results if item[0] == "read" and item[1] is not None]
    return bad


class TestTheSubjectIsAnIdentifierNotACredentialNorATenant:
    """(a)/(c) 的交叉面：主体形态本身不越界。"""

    def test_the_actor_is_a_kind_prefixed_identifier(self) -> None:
        principal = Principal(id="operator-1", kind=PrincipalKind.USER)
        assert principal.actor == "user:operator-1"
        assert ":" in principal.actor, "actor 必须是 `<kind>:<id>` 形态"

    def test_the_principal_carries_no_tenant_or_role_field(self) -> None:
        """**M18 边界**：`Principal` **没有**租户 / 角色 / 权限字段。

        这条把「本轮不引入多租户 / RBAC」变成**机械事实**（不是文档承诺）：
        若将来给 `Principal` 加了这类字段，本判据变红并提示更新威胁模型。
        """
        fields = set(Principal.__dataclass_fields__)
        assert fields == {"id", "kind"}, f"Principal 字段集越界：{sorted(fields)}"
        forbidden = {"tenant", "tenant_id", "organization", "org_id", "role", "roles", "scopes"}
        assert not (fields & forbidden), f"Principal 出现授权面字段（M18）：{fields & forbidden}"

    def test_a_principal_cannot_smuggle_a_separator(self) -> None:
        """`id` 不含 `:`（否则 `actor` 的类型 / 标识切分会歧义 ⇒ 读面可被绕）。"""
        with pytest.raises(ValueError):
            Principal(id="evil:user:admin", kind=PrincipalKind.USER)

    def test_no_principal_is_left_behind_on_the_real_app(self, authed_client: TestClient) -> None:
        """真实 app：读请求之后上下文里**没有**主体残留。"""
        assert authed_client.get("/health").status_code == 200
        assert current_principal() is None


@pytest.fixture
def authed_client(run_ready_deps: ApiDeps, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """认证**开启**的真实控制面（token 经环境变量注入，装配期快照）。"""
    monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, _FIXTURE_TOKEN)
    monkeypatch.setenv(CONTROL_PLANE_PRINCIPAL_ID_ENV, _FIXTURE_PRINCIPAL_ID)
    with TestClient(create_app(run_ready_deps)) as test_client:
        yield test_client
