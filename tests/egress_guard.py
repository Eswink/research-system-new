"""默认门离线的**整轮**结构判据（GOAL-010 EC-05 / PLAN-20260922-131）。

**命题**：默认测试运行（不显式开门）里，任何一次通往**非环回**目的地的出站尝试，
都会让**发起它的用例**判红——判据不依赖人工观察，也**不依赖凭据是否可解析**。

**为什么需要它**（`RECHECK-121` W-7）：那次真实出站
（`GET https://apihub.agnes-ai.com/v1/models` ⇒ 200）由一个**谁也没 mock 的路径**发起
（litellm `load_dotenv()` 把 `.env` 凭据带进进程 ⇒ 某条路径真去调了端点）。既有的「零出站」
判据是**逐用例 mock `socket.socket`**（`tests/e2e/test_ec04_live_gate_offline.py`），判的是
**某条路径**——**没人想到的路径天然逃逸**。本模块把判据搬到**拦截点**：判「发生」，不判「形态」。

**放行面**：只有带 `requires_live_llm` marker 的用例可以出网——与既有 live 门语汇同源，
且**不依赖环境变量**（EC-05 明文禁止把判据弱化成依赖环境的形态）。没有当前用例
（收集期 / 导入期 / 用例之外）⇒ **默认拒**（fail-closed）。

**两条机制，缺一不可**：`judge` 在**任何数据包之前**抛 `PublicNetworkBlocked`（**拦**），
`blocking_failures()` 在会话收尾时按**记录**把整轮判红（**判**）。只有「拦」不够——异常会被
调用方当成普通连接失败吞掉，收集期/用例外更没有用例可判红。每条阻断都带**调用链摘要**
（`EgressAttempt.origin`），归因由判据给出，不靠人事后翻栈。

**为什么连私网也拒**：本机 DNS 走 fake-IP 代理，公网域名解析出的地址落在
`198.18.0.0/15`——`ipaddress` 把它归**私有**。若只拒 `public`，那条 W-7 的出站会**静默通过**。
所以放行面收窄到**环回**（`localhost` 类别，含 `127.0.0.0/8` 与 `::1`）：默认门里凡**不是**
本机自身的目的地都算「出站」。**这不是新造判据**——分类仍复用
`packages/application/model_relay/endpoint_policy.py` 的 `destination_kind`（全仓唯一）。

**射程（不假装覆盖）**：判两个面——**同步** `socket.socket.connect` / `connect_ex`，以及
**异步** **具体**事件循环类的 `sock_connect`（Windows 的 Proactor 循环走 `_overlapped.ConnectEx`，
**不经过**前者；抽象基类那份是 `NotImplementedError` 桩、对实际循环不可达，所以装的是
selector / proactor 两个**具体实现**——两条都是独立复检逼出来的）。都只判 `AF_INET` / `AF_INET6`。
**不在射程内**：DNS（`getaddrinfo`）、UDP（`sendto`）、子进程、非 python 作业、
**自实现 `sock_connect` 的第三方循环**（如 uvloop）；
**环回转发代理**同样看不见（目的地确实是本机，判决只有环回）。逐条登记在 PLAN-131 的残余表。

**这条判据管不到的那一次**（GOAL-011 EC-05 的同源句，逐字，由
`tests/tooling/test_m0_ci_coverage.py` 机器校验）：**CI 每轮至多有一次受控外部下载**——
它发生在**环境准备阶段**（`import litellm` 预热，在跑门之前），**不在本判据的进程内**。
**实测口径**（2026-09-22，用不可达代理探请求、冷 `TIKTOKEN_CACHE_DIR` 探下载）：
该步请求的是 litellm 的 **model cost map**（`raw.githubusercontent.com`，失败即回落本地副本）；
**没有**观察到词表 `cl100k_base` 被下载。门内这两条都被处理掉了——conftest 在任何测试模块
导入 litellm 之前置 `LITELLM_LOCAL_MODEL_COST_MAP=True`，非环回目的地在**任何数据包之前**
被本判据拦下。
所以「默认 CI 完全离线」**不声称成立**；要连这一次也消掉，得把上游数据固化进镜像或私有源。
"""

from __future__ import annotations

import asyncio.proactor_events
import asyncio.selector_events
import socket
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from packages.application.model_relay.endpoint_policy import destination_kind

#: 唯一放行的目的地类别：**本机自身**。其余类别（private / reserved / public / domain）都算出站。
ALLOWED_KINDS: Final[frozenset[str]] = frozenset({"localhost"})
#: 与 live 用例同源的开门口径（既有 marker，不新造开关）。
ALLOW_MARKER: Final = "requires_live_llm"
#: 没有当前用例时的署名（收集期 / 导入期 / 用例之外）。
_OUTSIDE_A_TEST: Final = "<outside-a-test>"
#: 本判据**自身测试探针**用的地址（RFC 5737 文档地址：**永不是真实服务**）：只有它上面的阻断
#: 不计入会话级红灯——它之外的任何非环回阻断（**含收集期/用例外**）都让整轮判红。
#: **不要把它读成「不可路由」**：本机 fake-IP 代理对任意 IP 都秒回连接（实测 `1.1.1.1` 与各文档
#: 地址全部 0.02s 内 CONNECTED），所以证物「不真出网」靠的是**判据在发 SYN 之前拦下**，不是靠地址。
#: 用 TEST-NET-2（`198.51.100.0/24`）而不是更常见的 TEST-NET-1：后者的字面量会被
#: `validate_bundle.py` 的「旧项目版本引用」正则读成一个旧版本号（实测误报），故避开。
GUARD_PROBE_TARGET: Final = "198.51.100.1"

_CONNECT = socket.socket.connect
_CONNECT_EX = socket.socket.connect_ex
#: 被替换掉的 `sock_connect`：`{类: (该类是否自带这个属性, 原件)}`——`disarm` 靠它**原样**复原
#: （自带 ⇒ 写回；继承来的 ⇒ 删掉，不把继承函数固化进子类的 `__dict__`）。
_ASYNC_ORIGINALS: dict[type[Any], tuple[bool, Any]] = {}
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
#: 虚拟环境根：那里的帧是**依赖**不是本项目源码，归因时让位给真正的发起者。
_DEPENDENCY_ROOT = _PROJECT_ROOT / ".venv"
_SELF_FILENAME = Path(__file__).name


class PublicNetworkBlocked(RuntimeError):
    """默认门里出现**非环回**目的地出站尝试时抛出（出站**先于任何数据包**被拦下）。"""


@dataclass(frozen=True, slots=True)
class EgressAttempt:
    """一次被裁决的连接尝试（放行也记账，便于 WP3 的报告）。"""

    nodeid: str
    target: str
    kind: str
    allowed: bool
    #: 阻断时的调用链摘要（**归因给判据本身**，不靠人去翻栈）；放行时为空串。
    origin: str = ""


def _origin(depth: int = 6) -> str:
    """被拦下时的调用链摘要：**归因可读**优先，`depth` 帧封顶。

    先取「项目源码帧」（仓库内、**但不在 `.venv`**：pytest / pluggy 的帧会把真正的发起者
    挤出摘要——实测过一次采集期出站的摘要全是 pytest 内部帧）；一个都没有时，退化到调用栈
    末端（那里通常是 httpcore/httpx 这类客户端库，仍能认出「是谁在出网」）。
    只在**阻断**时调用（罕见）——放行路径不付这个代价。
    """
    frames = [f for f in traceback.extract_stack()[:-1] if Path(f.filename).name != _SELF_FILENAME]
    project = [f for f in frames if _is_project_frame(f.filename)]
    picked = project[-depth:] or frames[-depth:]
    return (
        " <- ".join(f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in picked) or "<no frame>"
    )


def _is_project_frame(filename: str) -> bool:
    """**项目源码**帧：仓库内的真实文件，且**不在虚拟环境里**（`.venv` 是依赖，不是本项目）。

    伪文件名（`<frozen runpy>` 之类）会被 `Path.resolve()` 当成 cwd 下的相对路径 ⇒
    看起来「在项目里」，摘要就会被 `<frozen runpy>` 填满（实测过）。
    """
    if not filename or filename.startswith("<"):
        return False
    path = Path(filename)
    if not path.is_absolute():
        return False
    try:
        resolved = path.resolve()
        if resolved.is_relative_to(_DEPENDENCY_ROOT):
            return False
        return resolved.is_relative_to(_PROJECT_ROOT)
    except OSError:  # pragma: no cover - 路径解析失败时按「非项目帧」处理
        return False


def _tcp_target(sock: socket.socket, address: Any) -> tuple[str, int] | None:
    """取 IP 目的地的 (host, port)；非 IP socket / 形状不符 ⇒ `None`（不归本判据管）。"""
    if getattr(sock, "family", None) not in (socket.AF_INET, socket.AF_INET6):
        return None
    if not isinstance(address, tuple) or len(address) < 2 or not isinstance(address[0], str):
        return None
    port = address[1]
    return address[0], port if isinstance(port, int) else 0


def _refusal(host: str, port: int, kind: str, nodeid: str) -> PublicNetworkBlocked:
    return PublicNetworkBlocked(
        f"the default gate is offline: blocked a {kind} destination {host}:{port} "
        f"attempted by {nodeid}. Live tests declare the {ALLOW_MARKER!r} marker; "
        "anything else must not reach the network (GOAL-010 EC-05)"
    )


class EgressGuard:
    """进程级 socket 守卫；`judge` 是唯一的判定入口。"""

    def __init__(self) -> None:
        self._attempts: list[EgressAttempt] = []
        self._nodeid: str | None = None
        self._allows_egress = False
        self._armed = False

    # --- 装配 ---------------------------------------------------------------

    def arm(self) -> None:
        """装上拦截点（幂等）；装上后**默认门里没有一次非环回连接能发生**。

                装的是**模块级函数**（不是本对象的方法）：函数是描述符，`sock.connect(addr)` 才会把
                `sock` 绑到第一个参数上；装一个**已绑定方法**会少一个参数（实测过）。

        两个面都装：**同步**（`socket.socket.connect` / `connect_ex`）与**异步**
        （**具体**事件循环类的 `sock_connect`——Windows 的 Proactor 循环走 `_overlapped.ConnectEx`，
        **不经过**前者，复检实测过一次「异步连到非环回地址成功且判据零记录」）。
        """
        if self._armed:
            return
        socket.socket.connect = _connect  # type: ignore[assignment]
        socket.socket.connect_ex = _connect_ex  # type: ignore[assignment]
        for loop_class in _loop_classes():
            _ASYNC_ORIGINALS[loop_class] = (
                "sock_connect" in loop_class.__dict__,
                loop_class.sock_connect,
            )
            loop_class.sock_connect = _sock_connect
        self._armed = True

    def disarm(self) -> None:
        """卸下拦截点（幂等）——只给**按压**用：真出站会在这里发生。"""
        if not self._armed:
            return
        socket.socket.connect = _CONNECT  # type: ignore[method-assign]
        socket.socket.connect_ex = _CONNECT_EX  # type: ignore[method-assign]
        for loop_class, (had_own, original) in _ASYNC_ORIGINALS.items():
            if had_own:
                loop_class.sock_connect = original
            else:
                delattr(loop_class, "sock_connect")
        _ASYNC_ORIGINALS.clear()
        self._armed = False

    @property
    def armed(self) -> bool:
        return self._armed

    @property
    def attempts(self) -> tuple[EgressAttempt, ...]:
        return tuple(self._attempts)

    def blocked(self) -> tuple[EgressAttempt, ...]:
        """被判红的尝试（`allowed=False`）——WP3 报告用。"""
        return tuple(item for item in self._attempts if not item.allowed)

    def blocking_failures(self) -> tuple[EgressAttempt, ...]:
        """会让**整轮**判红的阻断：除判据自身探针地址（`GUARD_PROBE_TARGET`）外的任何阻断。

        为什么要这一层：`judge` 的异常可能被调用方**吞掉**（库把连接失败当常规错误），
        收集期/用例外更没有用例可判红——W-7 的真实出站正是这样滑过去的。所以判定不止于
        「抛异常」，还要在会话收尾时**按记录**把整轮判红（`tests/conftest.py` 的 sessionfinish）。
        """
        prefix = f"{GUARD_PROBE_TARGET}:"
        return tuple(item for item in self.blocked() if not item.target.startswith(prefix))

    # --- 会话接线 -----------------------------------------------------------

    def enter(self, nodeid: str, *, allows_egress: bool) -> None:
        self._nodeid = nodeid
        self._allows_egress = allows_egress

    def leave(self) -> None:
        """回到「没有当前用例」= 默认拒（fail-closed），不是回到放行。"""
        self._nodeid = None
        self._allows_egress = False

    # --- 判定 ---------------------------------------------------------------

    def judge(self, sock: socket.socket, address: Any) -> None:
        """裁决一次连接尝试；非环回目的地且未开门 ⇒ 抛 `PublicNetworkBlocked`。"""
        target = _tcp_target(sock, address)
        if target is None:
            return
        host, port = target
        kind = destination_kind(host)
        nodeid = self._nodeid or _OUTSIDE_A_TEST
        allowed = kind in ALLOWED_KINDS or self._allows_egress
        self._attempts.append(
            EgressAttempt(
                nodeid=nodeid,
                target=f"{host}:{port}",
                kind=kind,
                allowed=allowed,
                origin="" if allowed else _origin(),
            )
        )
        if not allowed:
            raise _refusal(host, port, kind, nodeid)


#: 进程级单例：`tests/conftest.py` 在导入期 `arm()`，会话钩子维护「当前用例」。
guard = EgressGuard()


def _connect(sock: socket.socket, address: Any) -> Any:
    """装在 `socket.socket.connect` 上的拦截点（模块级函数 ⇒ 描述符绑定才正确）。"""
    guard.judge(sock, address)
    return _CONNECT(sock, address)


def _connect_ex(sock: socket.socket, address: Any) -> int:
    """装在 `socket.socket.connect_ex` 上的拦截点（同上）。"""
    guard.judge(sock, address)
    return _CONNECT_EX(sock, address)


async def _sock_connect(loop: Any, sock: socket.socket, address: Any) -> Any:
    """装在事件循环 `sock_connect` 上的拦截点（**异步面**的唯一出口）。

    为什么必须单独装：Windows 的 Proactor 循环用 `_overlapped.ConnectEx` 直接发起连接，
    一次都不经过 `socket.socket.connect`（复检实测：`asyncio.open_connection` 连到 LAN 地址
    **成功**且 `judged 0`）。异步栈——anyio / httpcore / `httpx.AsyncClient` / aiohttp——
    都从这里过；本仓 `adapters/mcp/transport.py` 就在这条线上。
    """
    guard.judge(sock, address)
    return await _async_original(loop)(loop, sock, address)


def _async_original(loop: Any) -> Any:
    """找回被替换掉的原 `sock_connect`：按实例的 MRO 找（拦截点可能装在基类上）。"""
    for klass in type(loop).__mro__:
        entry = _ASYNC_ORIGINALS.get(klass)
        if entry is not None:
            return entry[1]
    raise RuntimeError("the egress guard lost the original loop.sock_connect")  # pragma: no cover


def _loop_classes() -> tuple[type[Any], ...]:
    """要装拦截点的事件循环类：**两个具体实现**——selector 循环与 Proactor 循环的基类。

    为什么不是抽象基类：`asyncio.events.AbstractEventLoop.sock_connect` 是个
    `raise NotImplementedError` 桩，两个具体循环**各自持有**自己的实现——复检测过
    「抽象基类上那份
    对实际循环**不可达**」。只装抽象基类会让「异步面已覆盖」变成一句**错话**（selector 循环实际靠
    同步面兜底），装具体类才是真的拦住。
    """
    return (
        asyncio.selector_events.BaseSelectorEventLoop,
        asyncio.proactor_events.BaseProactorEventLoop,
    )
