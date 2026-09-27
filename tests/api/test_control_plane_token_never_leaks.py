"""**对抗性自检**：控制面 **token 不泄漏**（GOAL-20260927-021 EC-02；AGENTS.md §10）。

判据覆盖**控制面认证 token 这一条凭据**在六个出口上的行为：

1. **日志**（应用 log / access log / 异常消息）——带 token 发请求后用捕获 handler 收全部记录；
2. **遥测 / span 属性**——结构（闭集 allow-list）+ 对抗输入（把 token 塞进允许键）；
3. **错误响应体**（含 401 的两个点名文案）；
4. **事件 payload**（canonical 只记主体**标识**）；
5. **前端持久层**——既有 `tests/api/test_security_scan.py` 已覆盖，本文件**不重复**；
6. **记录面**（`.cursor/plans`）——只允许**变量名**。

**与既有判据的分工**：`test_secret_redaction.py` 判**中转站 API key** 在 DTO / error 出口；
`test_security_scan.py` 判 DTO / SSE / Export / error 四出口的 `sk-` 与前端持久层。
本文件判**控制面 token**在她**特有**的出口上的行为（401 两个点名文案、`sanitize_attributes`
的对抗输入、日志捕获）——**不重复、不顶替**。

**凭据纪律**：本文件的 token 是**本文件内构造的合成假值**（`fixture-` 前缀），
**不是**任何真实凭据，**不**从环境读取、**不**落盘、**不**进日志（AGENTS.md §10）。

**如实登记的边界（判据断的是真实行为，不是想象中的强脱敏）**：
`packages/domain/redaction.py::redact_text` 是**形态匹配**（`Bearer <x>` / `sk-…` / 各家
token 形态会被替换），**裸的不透明串**放在**允许清单内**的字符串键里**会留下**。
因此本文件对遥测面的断言分两档：**允许键 + bearer 形态 ⇒ 必被脱敏**（硬断言）；
**裸不透明串 ⇒ 如实断言其现状**（不假装更强）。
"""

from __future__ import annotations

import io
import logging
from collections.abc import Iterator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from packages.application.principal_context import current_principal
from packages.domain.redaction import redact_text
from services.api.app import create_app
from services.api.composition import ApiDeps
from services.api.middleware import (
    CONTROL_PLANE_PRINCIPAL_ID_ENV,
    CONTROL_PLANE_TOKEN_ENV,
)

# 合成夹具值（不是真实凭据；见模块 docstring）。
_FIXTURE_TOKEN = "fixture-" + "c" * 24
_FIXTURE_PRINCIPAL_ID = "leak-probe"
_EXPECTED_ACTOR = f"service:{_FIXTURE_PRINCIPAL_ID}"
_WRONG_TOKEN = "fixture-" + "d" * 24


@pytest.fixture
def authed_client(run_ready_deps: ApiDeps, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """认证**开启**的真实控制面（token 经环境变量注入，装配期快照）。"""
    monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, _FIXTURE_TOKEN)
    monkeypatch.setenv(CONTROL_PLANE_PRINCIPAL_ID_ENV, _FIXTURE_PRINCIPAL_ID)
    with TestClient(create_app(run_ready_deps)) as test_client:
        yield test_client


class TestTheTokenNeverReachesLogs:
    """出口 ①：日志。"""

    def test_no_log_record_contains_the_token(self, authed_client: TestClient) -> None:
        """带 token 发三类写请求 ⇒ **捕获到的全部日志记录**里 token 值零命中。

        三类请求各自会走到不同的判定分支（缺头 / 不匹配 / 通过），
        因此这条同时覆盖「拒绝时会不会把收到的凭据记下来」这个真实风险。
        """
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        root = logging.getLogger()
        previous = root.level
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
        try:
            authed_client.post("/projects", json={})
            authed_client.post(
                "/projects", json={}, headers={"Authorization": f"Bearer {_WRONG_TOKEN}"}
            )
            authed_client.post(
                "/projects", json={}, headers={"Authorization": f"Bearer {_FIXTURE_TOKEN}"}
            )
        finally:
            root.removeHandler(handler)
            root.setLevel(previous)

        captured = stream.getvalue()
        assert _FIXTURE_TOKEN not in captured, (
            "正确 token 出现在日志里（AGENTS.md §10：不得记录凭据）"
        )
        assert _WRONG_TOKEN not in captured, "被拒绝的 token 出现在日志里"

    def test_the_capture_mechanism_itself_works(self, authed_client: TestClient) -> None:
        """**判据自身的对照**：捕获装置**确实**能截到日志。

        否则上面的「零命中」可能只是「什么都没捕到」这类假绿——
        这条把「捕获有效」变成可观测事实（先证明探针能看见东西）。
        """
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        root.addHandler(handler)
        sentinel = "capture-sentinel-" + "e" * 12
        try:
            logging.getLogger("leak-probe").warning("sentinel %s", sentinel)
        finally:
            root.removeHandler(handler)
        assert sentinel in stream.getvalue(), (
            "捕获装置没截到任何东西 ⇒ 上面的「零命中」是假绿（判据自身失效）"
        )


class TestTheTokenNeverReachesTelemetryAttributes:
    """出口 ②：遥测 / span 属性。"""

    def test_unknown_attribute_keys_are_dropped_entirely(self) -> None:
        """**结构**：属性词汇是**闭集 allow-list**，未知键**整个丢弃**。

        ⇒ `authorization` / `raw_headers` 这类键在**词汇层**就进不去 span，
        不需要依赖值脱敏（多一层保证）。
        """
        from packages.application.observability.attributes import sanitize_attributes

        sanitized = sanitize_attributes({
            "provider": "relay-a",
            "authorization": f"Bearer {_FIXTURE_TOKEN}",
            "raw_headers": f"Authorization: Bearer {_FIXTURE_TOKEN}",
            "request_body": f'{{"token": "{_FIXTURE_TOKEN}"}}',
        })
        assert "provider" in sanitized, "允许清单内的键必须留下（否则判据把一切都丢了）"
        for forbidden in ("authorization", "raw_headers", "request_body"):
            assert forbidden not in sanitized, f"未知键 `{forbidden}` 必须被整个丢弃"

    def test_a_bearer_shaped_value_in_an_allowed_key_is_redacted(self) -> None:
        """**对抗输入**：把 token 以 **bearer 形态**塞进**允许清单内**的字符串键 ⇒ 必被脱敏。"""
        from packages.application.observability.attributes import sanitize_attributes

        sanitized = sanitize_attributes({"model_id": f"Bearer {_FIXTURE_TOKEN}"})
        exported = str(sanitized["model_id"])
        assert _FIXTURE_TOKEN not in exported, "bearer 形态的凭据未被脱敏"
        assert "REDACTED" in exported

    def test_a_bare_opaque_value_in_an_allowed_key_is_reported_as_it_is(self) -> None:
        """**如实断言现状**：裸不透明串不是被脱敏的形态 ⇒ 判据**不假装**它会被拦住。

        这条**存在**的意义：把边的位置写下来。若将来强化为「允许键一律不得承载凭据」，
        本判据会红并提示更新——它防的是**以为已经覆盖而其实没有**。
        """
        from packages.application.observability.attributes import sanitize_attributes

        bare = "opaque-" + "f" * 20
        exported = str(sanitize_attributes({"model_id": bare})["model_id"])
        assert bare in exported, (
            "行为已改变（裸值也被脱敏）⇒ 请复核本文件声明的适用边界并更新该断言"
        )

    def test_the_redaction_is_shape_based_not_value_based(self) -> None:
        """机制说明：脱敏按**形态**匹配。这条把上文两档断言的**原因**钉住。"""
        assert _FIXTURE_TOKEN not in redact_text(f"Authorization: Bearer {_FIXTURE_TOKEN}")
        assert f"sk-{_FIXTURE_TOKEN}" not in redact_text(f"key=sk-{_FIXTURE_TOKEN}")


class TestTheTokenNeverReachesResponses:
    """出口 ③：错误响应体（含 401 的两个点名文案）。"""

    def test_neither_401_body_echoes_a_credential(self, authed_client: TestClient) -> None:
        """两个 401（缺头 / 不匹配）的**整个 body** 都不含凭据。

        同时断言两个成因**各自被点名**——这条把「不泄漏」与「可诊断」一起判住：
        拒绝文案必须说清缺什么，但**不得**把收到的凭据回显出来。
        """
        missing = authed_client.post("/projects", json={})
        wrong = authed_client.post(
            "/projects", json={}, headers={"Authorization": f"Bearer {_WRONG_TOKEN}"}
        )
        assert missing.status_code == 401 and wrong.status_code == 401
        for response in (missing, wrong):
            assert _FIXTURE_TOKEN not in response.text
            assert _WRONG_TOKEN not in response.text
        assert "Bearer" in missing.json()["detail"], "必须点名缺的是哪种头"
        assert "does not match" in wrong.json()["detail"], "必须点名成因是不匹配"

    def test_a_successful_write_does_not_reflect_the_credential(
        self, authed_client: TestClient
    ) -> None:
        """**成功**响应同样不回显凭据（换一种提交路径复验）。"""
        response = authed_client.post(
            "/projects",
            json={"id": "leak-probe-project", "name": "leak probe"},
            headers={
                "Authorization": f"Bearer {_FIXTURE_TOKEN}",
                "Idempotency-Key": "leak-probe-create",
            },
        )
        assert response.status_code == 201, response.text
        assert _FIXTURE_TOKEN not in response.text


class TestTheTokenNeverReachesEventPayloads:
    """出口 ④：canonical 事件 payload。"""

    def test_the_decision_event_records_the_actor_not_a_credential(
        self, authed_client: TestClient
    ) -> None:
        """带 token 的决定事件：payload **不含**凭据，`actor` 是**主体标识**。"""
        import uuid

        from packages.domain.core import ID
        from packages.domain.run import ResearchRun
        from packages.domain.run_state import ResearchRunState
        from services.api.approvals import ApprovalSpec

        deps = cast(Any, authed_client.app).state.deps
        run_id = str(ID.generate().value)
        deps.run_registry[run_id] = ResearchRun(
            id=ID(run_id),
            project_id="example-project",
            protocol_id="test_protocol",
            state=ResearchRunState.State.RUNNING,
        ).transition(ResearchRunState.Transition.REQUEST_APPROVAL)
        approval = deps.approvals.register(
            ApprovalSpec(
                run_id=run_id,
                action="high-risk-tool",
                risk="HIGH",
                context="needs human approval",
                policy_source="project-policy:require_approval",
                requested_event_id=f"evt-{uuid.uuid4().hex}",
            )
        )
        decided = authed_client.post(
            f"/approvals/{approval.id}/decide",
            json={"decision": "deny"},
            headers={
                "If-Match": approval.version,
                "Authorization": f"Bearer {_FIXTURE_TOKEN}",
                "Idempotency-Key": f"leak-{uuid.uuid4()}",
            },
        )
        assert decided.status_code == 200, decided.text

        events = authed_client.get(f"/runs/{run_id}/events").json()
        raw = str(events)
        assert _FIXTURE_TOKEN not in raw, "凭据出现在事件出口"
        decided_events = [item for item in events if item["type"] == "approval.decided"]
        assert decided_events, "应当有一条 approval.decided"
        envelope = decided_events[0]
        assert envelope["actor"] == _EXPECTED_ACTOR
        assert _FIXTURE_TOKEN not in str(envelope["payload"])
        for value in envelope["payload"].values():
            assert _FIXTURE_TOKEN not in str(value)


class TestTheTokenIsAbsentFromTheRecordFace:
    """出口 ⑥：记录面（`.cursor/plans` / `.cursor/memory`）。"""

    def test_no_record_file_contains_a_credential_looking_value(self) -> None:
        """记录面只允许**变量名**，不得留 token 值。

        判据扫的是记录面的**实际文件内容**（不是文档话术）；它同时是
        「本 GOAL 自己有没有把凭据写进记录」的自检。
        """
        from pathlib import Path

        repo = Path(__file__).resolve().parents[2]
        roots = [repo / ".cursor" / "plans", repo / ".cursor" / "memory"]
        files = [path for root in roots for path in root.rglob("*.md")]
        assert files, "记录面扫描面为空 ⇒ 判据选错了根（先修扫描面再谈零命中）"

        offenders: list[str] = []
        names_only = 0
        for path in files:
            text = path.read_text(encoding="utf-8")
            for needle in (_FIXTURE_TOKEN, _WRONG_TOKEN):
                if needle in text:
                    offenders.append(str(path.relative_to(repo)))
            if CONTROL_PLANE_TOKEN_ENV in text:
                names_only += 1

        assert offenders == [], f"记录面出现凭据值：{offenders}"
        # 变量名**应当**在记录面出现（否则说明扫描面可能选错了 ⇒ 零命中没意义）。
        assert names_only > 0, (
            f"记录面（{len(files)} 个文件）里连**变量名** `{CONTROL_PLANE_TOKEN_ENV}` 都没出现 "
            "⇒ 扫描面可疑，零命中不能作为结论"
        )


class TestThePrincipalContextCarriesNoCredential:
    """出口 ②/④ 的交叉面：主体上下文本身只承载**标识**。"""

    def test_the_context_principal_holds_an_identifier_not_a_credential(
        self, authed_client: TestClient
    ) -> None:
        """主体是「类型 + 标识」，**不是**凭据 ⇒ 即使被日志打出来也不泄漏 token。"""
        with authed_client:
            pass
        # 直接构造配置主体，断言其 actor 形态不含凭据成分。
        from services.api.middleware import ControlPlaneAuth

        config = ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id=_FIXTURE_PRINCIPAL_ID)
        assert _FIXTURE_TOKEN not in config.principal.actor
        assert config.principal.actor == _EXPECTED_ACTOR

    def test_no_principal_is_set_on_an_unauthenticated_read(
        self, authed_client: TestClient
    ) -> None:
        """读面不设主体 ⇒ 读路径上没有可泄漏的凭据载体。"""
        assert authed_client.get("/health").status_code == 200
        assert current_principal() is None
