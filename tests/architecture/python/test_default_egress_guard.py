"""默认门离线的结构判据：**常驻证物 + 非空转正对照**（GOAL-010 EC-05 / PLAN-20260922-131）。

判据本体在 `tests/egress_guard.py`（由 `tests/conftest.py` 在导入期武装）。本文件判七件事：

1. **装配**：默认门里守卫**已武装**（不是「恰好没触发」）。
2. **拒的向（证物）**：对**非环回**目的地的**真实**连接尝试**先于任何数据包**被拦下——
   用的是 `198.51.100.1`（RFC 5737 TEST-NET-2 **文档地址，永不是真实服务**）。
   **别把「文档地址」读成「不可路由」**：本机 fake-IP 代理对任意 IP 都秒回（实测 0.02s CONNECTED），
   证物「不真出网」靠的是**判据在发 SYN 前拦下**，不是靠地址。
3. **放的向（正对照）**：对一个**真的在听**的环回端口发起连接**必须成功**——否则「全拦」
   也能让第 2 条变绿，判据就是空的。
4. **分类面**：公网 / 私网 / fake-IP 段都落在**拒**的一侧，环回落在**放**的一侧；
   只判分类，**不发连接**（避免证物依赖真实出网）。
5. **归因**：每条阻断自带**调用链摘要**——是判据指出「谁发起」，不是靠人翻栈。
6. **会话级红灯**：出现过**探针之外**的阻断 ⇒ 整轮 `TESTS_FAILED`，**哪怕调用方把异常吞了**
   （用新守卫 + 桩会话直接压 `tests/conftest.py::pytest_sessionfinish`，不发真实连接）。
7. **异步面**：Windows 的 Proactor 循环走 `_overlapped.ConnectEx`，**不经过**
   `socket.socket.connect`（独立复检实测过这条逃逸）——异步出站同样被拦、被归因，环回仍放行。

**不声称**：DNS / UDP / 子进程 / 非 python 作业 / 环回转发代理不在射程内（PLAN-131 残余表）。
"""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import socket
from collections.abc import Iterator
from contextlib import closing, contextmanager

import pytest

from packages.application.model_relay.endpoint_policy import destination_kind
from tests import conftest as root_conftest
from tests.egress_guard import _CONNECT as _TRUE_ORIGINAL_CONNECT
from tests.egress_guard import (
    ALLOW_MARKER,
    ALLOWED_KINDS,
    GUARD_PROBE_TARGET,
    EgressGuard,
    PublicNetworkBlocked,
    guard,
)
from tests.egress_guard import _connect as _SYNC_INTERCEPTION
from tests.egress_guard import _sock_connect as _ASYNC_INTERCEPTION

#: 真正会被实例化的循环类（`_loop_classes()` 装的是它们的基类；这里断言**有效解析**）。
_REAL_LOOP_CLASSES = tuple(
    loop_class
    for loop_class in (
        getattr(asyncio, "SelectorEventLoop", None),
        getattr(asyncio, "ProactorEventLoop", None),
    )
    if loop_class is not None
)

#: RFC 5737 TEST-NET-2 文档地址：**永不是真实服务**（本机 fake-IP 代理对任意 IP 都秒回，
#: 实测 0.02s CONNECTED ⇒ 「不真出网」靠判据先拦，不靠地址）。
_NON_ROUTABLE = "198.51.100.1"
#: 同一个文档网段里**不属于**判据探针（`GUARD_PROBE_TARGET`）的地址：用来证明豁免是**点名**的，
#: 不是「整段放过」。
_NOT_THE_PROBE = "198.51.100.2"


@contextmanager
def _listening_loopback() -> Iterator[socket.socket]:
    """一个**真的在听**的环回服务端 socket（正对照需要一个会成功的连接）。"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        yield server


class TestTheGuardIsArmedInTheDefaultRun:
    def test_the_guard_is_armed(self) -> None:
        assert guard.armed is True, (
            "the offline-gate judge must be armed by tests/conftest.py at import time; "
            "if this is False the default gate has no structural offline guarantee"
        )

    def test_the_guard_is_armed_for_this_test_too(self) -> None:
        """当前用例的署名必须是我自己：判据知道**是谁**在出网（不是「有人出网」）。"""
        with pytest.raises(PublicNetworkBlocked) as blocked:
            socket.create_connection((_NON_ROUTABLE, 443), timeout=2)
        assert "test_the_guard_is_armed_for_this_test_too" in guard.attempts[-1].nodeid
        assert "test_the_guard_is_armed_for_this_test_too" in str(blocked.value)


class TestTheBlockedDirection:
    """证物：非环回目的地**先于任何数据包**被拦下。"""

    def test_a_non_loopback_destination_is_blocked_before_any_packet(self) -> None:
        with pytest.raises(PublicNetworkBlocked) as blocked:
            socket.create_connection((_NON_ROUTABLE, 443), timeout=2)
        assert _NON_ROUTABLE in str(blocked.value)

    def test_the_blocked_attempt_is_recorded_with_its_cause(self) -> None:
        """被拦下的尝试必须**可数、可归因**（不是「反正红了」）。"""
        before = len(guard.blocked())
        with pytest.raises(PublicNetworkBlocked):
            socket.create_connection((_NON_ROUTABLE, 8080), timeout=2)
        recorded = guard.blocked()[before:]
        assert len(recorded) == 1, recorded
        assert recorded[0].target == f"{_NON_ROUTABLE}:8080"
        assert recorded[0].kind not in ALLOWED_KINDS
        assert recorded[0].allowed is False


class TestTheAllowedDirection:
    """正对照：环回**不**被拦（否则「全拦」也能让上面的证物变绿）。"""

    def test_a_listening_loopback_port_is_still_reachable(self) -> None:
        with _listening_loopback() as server:
            host, port = server.getsockname()[:2]
            with closing(socket.create_connection((host, port), timeout=2)) as client:
                client.sendall(b"ping")
                assert server.accept()[0].recv(4) == b"ping"

    def test_the_allowed_attempt_is_recorded_as_allowed(self) -> None:
        with _listening_loopback() as server:
            host, port = server.getsockname()[:2]
            with closing(socket.create_connection((host, port), timeout=2)):
                pass
        recorded = guard.attempts[-1]
        assert (recorded.target, recorded.kind, recorded.allowed) == (
            f"{host}:{port}",
            "localhost",
            True,
        )
        assert recorded.origin == "", "only a blocked attempt needs an attribution"


class TestTheAttribution:
    """每条阻断自带调用链摘要：归因由判据给出，不靠人事后翻栈。"""

    def _blocked_probe(self, port: int = 443) -> None:
        with pytest.raises(PublicNetworkBlocked):
            socket.create_connection((_NON_ROUTABLE, port), timeout=2)

    def test_a_blocked_attempt_names_the_calling_code(self) -> None:
        self._blocked_probe()
        origin = guard.attempts[-1].origin
        assert origin, "a blocked attempt must carry the call chain that made it"
        assert "_blocked_probe" in origin, (
            "the innermost project frame is the caller; if it is missing the attribution "
            f"is useless for finding an unforeseen egress path: {origin!r}"
        )

    def test_the_attribution_stays_out_of_the_guard_internals(self) -> None:
        """摘要里**不该**出现判据自己的帧（否则每次阻断的摘要都是同一行废话）。"""
        self._blocked_probe(8443)
        segments = guard.attempts[-1].origin.split(" <- ")
        assert not any(seg.startswith("egress_guard.py:") for seg in segments), segments
        assert not any(seg.startswith("<") for seg in segments), segments


class _StubWriter:
    """接住 `write_line`：让「判定可见」这件事本身可断言。"""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def write_line(self, line: str) -> None:
        self.lines.append(line)


class _StubPluginManager:
    def __init__(self, plugin: object | None) -> None:
        self._plugin = plugin

    def get_plugin(self, name: str) -> object | None:
        return self._plugin


class _StubConfig:
    def __init__(self, writer: object | None) -> None:
        self.pluginmanager = _StubPluginManager(writer)


class _StubSession:
    """`pytest_sessionfinish` 只需要 `exitstatus` 与 `config.pluginmanager`。"""

    def __init__(self, writer: object | None = None) -> None:
        self.exitstatus = pytest.ExitCode.OK
        self.config = _StubConfig(writer)


def _guard_with_recorded_attempts(*targets: str) -> EgressGuard:
    """在新守卫上**离线**录下若干条尝试：不发真实连接（只喂 `judge` 一个未连接的 socket）。"""
    fresh = EgressGuard()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        for target in targets:
            host, _, port = target.partition(":")
            with contextlib.suppress(PublicNetworkBlocked):
                fresh.judge(sock, (host, int(port)))
    finally:
        sock.close()
    return fresh


class TestTheSessionLevelRed:
    """`judge` 抛的异常**可能被调用方吞掉**（库把连接失败当常规错误）：判据不能只靠那一下。

    这里压的是**真**钩子（`tests/conftest.py::pytest_sessionfinish`），只把守卫换成新实例、
    把会话换成桩——不发真实连接、也不污染本轮的记录。
    """

    def _finish(
        self, monkeypatch: pytest.MonkeyPatch, targets: str
    ) -> tuple[_StubSession, list[str]]:
        fresh = _guard_with_recorded_attempts(*targets.split(","))
        monkeypatch.setattr(root_conftest, "guard", fresh)
        writer = _StubWriter()
        session = _StubSession(writer)
        root_conftest.pytest_sessionfinish(session, pytest.ExitCode.OK)  # type: ignore[arg-type]
        return session, writer.lines

    def test_a_swallowed_block_fails_the_session_anyway(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session, lines = self._finish(monkeypatch, f"{_NOT_THE_PROBE}:443")
        assert session.exitstatus == pytest.ExitCode.TESTS_FAILED, (
            "a swallowed egress attempt must still turn the whole run red — otherwise it "
            "passes exactly like it did before GOAL-010 EC-05"
        )
        assert any(_NOT_THE_PROBE in line for line in lines), lines

    def test_the_red_names_the_call_chain_it_came_from(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _session, lines = self._finish(monkeypatch, f"{_NOT_THE_PROBE}:443")
        assert any("test_default_egress_guard.py" in line for line in lines), lines

    def test_a_block_inside_a_live_marked_test_does_not_fail_the_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """开门的用例（`requires_live_llm`）出网是**允许**的：它的尝试不该进红灯名单。"""
        fresh = EgressGuard()
        fresh.enter("tests/e2e/test_live_run.py::test_real", allows_egress=True)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            fresh.judge(sock, ("1.1.1.1", 443))
        finally:
            sock.close()
        monkeypatch.setattr(root_conftest, "guard", fresh)
        session = _StubSession(_StubWriter())
        root_conftest.pytest_sessionfinish(session, pytest.ExitCode.OK)  # type: ignore[arg-type]
        assert session.exitstatus == pytest.ExitCode.OK
        assert fresh.blocking_failures() == ()

    def test_only_the_named_probe_is_exempt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """豁免是**点名**的：探针地址放过，同网段的另一个地址照样判红。"""
        probe, _lines = self._finish(monkeypatch, f"{GUARD_PROBE_TARGET}:443")
        assert probe.exitstatus == pytest.ExitCode.OK, (
            "the judge's own probe must not turn its own suite red"
        )
        with_extra, _lines2 = self._finish(
            monkeypatch, f"{GUARD_PROBE_TARGET}:443,{_NOT_THE_PROBE}:443"
        )
        assert with_extra.exitstatus == pytest.ExitCode.TESTS_FAILED, (
            "the probe exemption must not become a general exemption"
        )

    def test_the_probe_constant_is_a_test_net_address(self) -> None:
        """探针地址必须是**永不路由**的文档网段地址，且**避开 TEST-NET-1**。

        避开 TEST-NET-1 的理由不是安全而是门禁：它的字面量会被 `validate_bundle.py` 的
        「旧项目版本引用」正则读成一个旧版本号（实测误报），所以探针落在 TEST-NET-2。
        """
        assert ipaddress.ip_address(GUARD_PROBE_TARGET) in ipaddress.ip_network("198.51.100.0/24")
        assert destination_kind(GUARD_PROBE_TARGET) not in ALLOWED_KINDS


class TestTheAsyncPathIsJudgedToo:
    """**异步面**（独立复检 W-1）：Windows 的 Proactor 循环用 `_overlapped.ConnectEx` 直接发起
    连接，一次都不经过 `socket.socket.connect`——复检实测过「异步连到非环回地址**成功**且判据
    零记录」。本组用例把那个洞钉住：异步出站必须同样被拦、被归因，且环回仍放行。

    证物用**探针地址**（`_NON_ROUTABLE`）而不是同网段的另一个地址：这里要证的是「异步面被拦」，
    不是「会话级红灯」——后者已由 `TestTheSessionLevelRed` 用新守卫单独压过。
    """

    def test_an_async_connection_to_a_non_loopback_destination_is_blocked(self) -> None:
        with pytest.raises(PublicNetworkBlocked) as blocked:
            asyncio.run(asyncio.open_connection(_NON_ROUTABLE, 443))
        assert _NON_ROUTABLE in str(blocked.value)

    def test_the_blocked_async_attempt_is_recorded_with_its_cause(self) -> None:
        before = len(guard.blocked())
        with pytest.raises(PublicNetworkBlocked):
            asyncio.run(asyncio.open_connection(_NON_ROUTABLE, 8443))
        recorded = guard.blocked()[before:]
        assert len(recorded) == 1, recorded
        assert recorded[0].target == f"{_NON_ROUTABLE}:8443"
        assert recorded[0].kind not in ALLOWED_KINDS
        assert recorded[0].origin, "the async path must be attributed like the sync one"

    def test_an_async_loopback_connection_still_succeeds(self) -> None:
        """正对照：异步连**真的在听**的环回端口必须成功（异步面没有被整体拦死）。"""
        with _listening_loopback() as server:
            host, port = server.getsockname()[:2]

            async def _connect_and_close() -> None:
                _reader, writer = await asyncio.open_connection(host, port)
                writer.close()

            asyncio.run(_connect_and_close())
            assert server.accept()[0] is not None

    def test_a_selector_loop_is_judged_by_the_async_face(self) -> None:
        """**具体类**必须真的装上（复检 W-8）：`AbstractEventLoop.sock_connect` 是
        `NotImplementedError` 桩、对实际循环**不可达**；只装它会让这条判据变成错话。
        这里用**行为**压：一个 selector 循环上的异步连接必须被拦下。
        """
        selector = getattr(asyncio, "SelectorEventLoop", None)
        if selector is None:  # pragma: no cover - 该构建没有 selector 实现时不假装判过
            pytest.skip("this build has no asyncio.SelectorEventLoop")
        assert selector.sock_connect is _ASYNC_INTERCEPTION, (
            "the concrete selector loop owns its own sock_connect; patching the abstract base "
            "would leave it to the sync face alone (RECHECK-131 W-8)"
        )
        loop = selector()
        try:
            with pytest.raises(PublicNetworkBlocked):
                loop.run_until_complete(asyncio.open_connection(_NON_ROUTABLE, 443))
        finally:
            loop.close()

    def test_the_interception_is_installed_on_both_faces_and_removable(self) -> None:
        """两个面都装着、且 `disarm()` 能**原样**复原（按压靠它，不能把事件循环改坏）。"""
        assert socket.socket.connect is _SYNC_INTERCEPTION
        for loop_class in _REAL_LOOP_CLASSES:
            assert loop_class.sock_connect is _ASYNC_INTERCEPTION, (
                f"{loop_class.__name__} must carry the interception point while armed"
            )
        guard.disarm()
        try:
            assert socket.socket.connect is _TRUE_ORIGINAL_CONNECT, (
                "disarm() must put the original socket.socket.connect back"
            )
            for loop_class in _REAL_LOOP_CLASSES:
                assert loop_class.sock_connect is not _ASYNC_INTERCEPTION, (
                    f"disarm() must restore {loop_class.__name__}.sock_connect"
                )
                assert loop_class.sock_connect.__name__ == "sock_connect"
        finally:
            guard.arm()
        assert socket.socket.connect is _SYNC_INTERCEPTION, "arm() must re-install the sync face"
        for loop_class in _REAL_LOOP_CLASSES:
            assert loop_class.sock_connect is _ASYNC_INTERCEPTION, (
                "arm() must re-install the async face"
            )


class TestTheClassificationItself:
    """分类面：**只判分类，不发连接**（射程声明见模块 docstring）。"""

    @pytest.mark.parametrize(
        ("host", "kind"),
        [
            ("127.0.0.1", "localhost"),
            ("::1", "localhost"),
            ("1.1.1.1", "public"),
            ("10.1.2.3", "private"),
            ("100.64.0.1", "reserved"),
            ("198.18.0.5", "private"),
            (_NON_ROUTABLE, "private"),
        ],
    )
    def test_the_single_source_classifier_has_not_moved(self, host: str, kind: str) -> None:
        assert destination_kind(host) == kind, (
            "the guard reuses endpoint_policy's classifier; if a kind moved, the deny set "
            "(loopback only) may now be wrong"
        )

    def test_the_deny_side_covers_everything_but_loopback(self) -> None:
        denied = {"public", "private", "reserved", "domain"}
        assert ALLOWED_KINDS == frozenset({"localhost"})
        assert ALLOWED_KINDS.isdisjoint(denied)

    def test_the_fake_ip_proxy_range_is_on_the_deny_side(self) -> None:
        """本机 DNS 走 fake-IP 代理（公网域名会解析到 `198.18.0.0/15`）：

        若只拒 `public`，**W-7 那次真实出站会静默通过**——这一条钉住「它落在拒的一侧」。
        """
        assert destination_kind("198.18.0.5") not in ALLOWED_KINDS

    def test_the_live_marker_is_the_only_way_to_open_the_gate(self) -> None:
        assert ALLOW_MARKER == "requires_live_llm", (
            "the guard's opt-out must stay the existing live marker (not an env switch)"
        )
