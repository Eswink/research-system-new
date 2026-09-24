"""Root test configuration: environment-probe skips for environment-dependent suites.

`requires_docker` / `requires_gpu` 标记的用例只有在真实环境可用时才执行；缺失时
诚实 skip（skip 计数在 pytest 输出中可见），而不是以环境错误 fail。CI 上可用
`RESEARCHOS_REQUIRE_DOCKER=1` / `RESEARCHOS_REQUIRE_GPU=1` 把「本该跳过」重新变成
硬失败（fail-closed）。PostgreSQL 的守卫沿用 `tests/postgres/conftest.py`。

**默认门离线的结构判据**（GOAL-010 EC-05）也装在这里：`tests/egress_guard.py` 在**导入期**
武装（覆盖收集期），会话钩子维护「当前用例」并据此放行 live 用例。见该模块 docstring。
判据上线当天就点出了一条**收集期真实出站**（litellm 导入期拉 model cost map），源头
修复见下面的 `LITELLM_LOCAL_MODEL_COST_MAP`。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.default_gate_credentials import LIVE_CREDENTIAL_KEYS
from tests.egress_guard import ALLOW_MARKER, guard

#: litellm 在**导入期**就会去公网拉 model cost map（`httpx.get`，上游 URL 是
#: `raw.githubusercontent.com/.../model_prices_and_context_window.json`，默认 5s 超时），
#: 失败才回退到 wheel 里自带的本地副本。`import openhands.sdk` 会把 litellm 拖进来 ⇒
#: 默认门（以及 CI）在**收集期**就真的出网了——2026-09-22 由 `tests/egress_guard.py`
#: 点名实测（PLAN-20260922-131 WP3 的调用链）。上游为「要离线」的场景提供了这个开关，
#: 这里在**任何测试模块 import litellm 之前**置上；置不上（被显式设成别的值）也不会被
#: 默默放过：守卫会把那次出站拦下并让整轮判红。
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

guard.arm()


@pytest.fixture(autouse=True)
def _default_gate_hides_live_credentials(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """未标记 `requires_live_llm` 的用例不得看见出厂目录声明的凭据键（夹具隔离）。

    本机 gitignored `.env` 会被 litellm **导入期**的 `load_dotenv()` 注入进程环境；若凭据
    可解析，「未配置控制面」的诚实失败路径会变成**真的去探端点** ⇒ 默认门的出站结构判据
    判红整轮。隔离放在这里（而不是改某一个用例或放宽判据），名单与出厂目录的同步由
    `tests/architecture/python/test_default_gate_credential_isolation.py` 机器强制。
    """
    if request.node.get_closest_marker(ALLOW_MARKER) is not None:
        return
    for key in LIVE_CREDENTIAL_KEYS:
        monkeypatch.delenv(key, raising=False)


_DOCKER_SKIP_REASON = (
    "no Linux-capable docker daemon available — requires_docker tests skipped "
    "(set RESEARCHOS_REQUIRE_DOCKER=1 to fail instead)"
)
_GPU_SKIP_REASON = (
    "no NVIDIA GPU device detected — requires_gpu tests skipped "
    "(set RESEARCHOS_REQUIRE_GPU=1 to fail instead)"
)


def _env_requires(name: str) -> bool:
    return os.environ.get(name) == "1"


def _docker_available() -> bool:
    """A *Linux-capable* daemon is required: every requires_docker suite runs
    Linux sandbox images. A Windows-container daemon (default on windows-latest)
    pings fine but cannot run them, so it must skip rather than fail."""
    try:
        import docker
    except ImportError:
        return False
    client = None
    try:
        client = docker.from_env(timeout=3)
        client.ping()
        info = client.info()
        return str(info.get("OSType", "")).lower() == "linux"
    except Exception:  # noqa: BLE001 - any daemon/transport failure means "no docker"
        return False
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001 - close is best-effort cleanup
                pass


def _gpu_available() -> bool:
    # Linux 设备节点是权威信号；Windows/macOS 回退到 nvidia-smi 存在性探测。
    if Path("/dev/nvidiactl").exists() or Path("/dev/nvidia0").exists():
        return True
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return False
    try:
        probe = subprocess.run(
            [nvidia_smi, "-L"],
            capture_output=True,
            timeout=15,
            check=False,
        )
    except Exception:  # noqa: BLE001 - a broken/blocked nvidia-smi means "no gpu"
        return False
    return probe.returncode == 0 and b"GPU" in probe.stdout


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    need_docker = any(item.get_closest_marker("requires_docker") for item in items)
    need_gpu = any(item.get_closest_marker("requires_gpu") for item in items)
    docker_ok = _docker_available() if need_docker else True
    gpu_ok = _gpu_available() if need_gpu else True
    require_docker = _env_requires("RESEARCHOS_REQUIRE_DOCKER") or _docker_is_the_point(config)
    require_gpu = _env_requires("RESEARCHOS_REQUIRE_GPU")
    for item in items:
        if item.get_closest_marker("requires_docker") and not docker_ok and not require_docker:
            item.add_marker(pytest.mark.skip(reason=_DOCKER_SKIP_REASON))
        elif item.get_closest_marker("requires_gpu") and not gpu_ok and not require_gpu:
            item.add_marker(pytest.mark.skip(reason=_GPU_SKIP_REASON))


def _docker_is_the_point(config: pytest.Config) -> bool:
    """`pytest -m requires_docker` 是专门的容器门禁作业：此时 daemon 缺失必须
    硬失败（fail-closed），而不是把整轮 skip 成 vacuous pass（避免削弱门禁）。"""
    markexpr = (getattr(config.option, "markexpr", "") or "").replace(" ", "")
    return markexpr == "requires_docker"


# --------------------------------------------------------------- 默认门离线的结构判据


def pytest_runtest_setup(item: pytest.Item) -> None:
    """记下当前用例：只有带 `requires_live_llm` 的用例可以出网（其余一律拒）。"""
    guard.enter(item.nodeid, allows_egress=item.get_closest_marker(ALLOW_MARKER) is not None)


def pytest_runtest_teardown(item: pytest.Item) -> None:
    """用例结束即回到「没有当前用例」= 默认拒（fail-closed），**不是**回到放行。"""
    guard.leave()


def pytest_report_header(config: pytest.Config) -> str | None:
    """把「守卫已武装」写进门禁输出：没看到这一行就说明判据没装上。"""
    if not guard.armed:
        return "egress guard: NOT ARMED — the offline-gate judge is missing"
    return "egress guard: armed (non-loopback destinations are blocked unless marked live)"


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """收尾报数：**判了多少次**、**拦了多少次**、拦截点在哪、**是谁发起**的。

    这一行让「默认门离线」在日志里**可数**（而不是只能读作「没看到失败」）。
    注意**绿跑里 blocked 不必然为 0**：判据自证用的探针（`GUARD_PROBE_TARGET`）**故意**被拦。
    因此这里的正确读法是：**逐条列出被拦**，每条带调用链摘要——探针之外出现任何一条，
    都已经让整轮判红（见下面的 `pytest_sessionfinish`），不是「可以继续的警告」。
    """
    attempts = guard.attempts
    blocked = guard.blocked()
    terminalreporter.write_line(
        f"egress guard: judged {len(attempts)} connection attempt(s); blocked {len(blocked)}"
    )
    for item in blocked:
        terminalreporter.write_line(
            f"egress guard: BLOCKED {item.target} by {item.nodeid} :: {item.origin}"
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """按**记录**收口整轮：出现过探针之外的非环回阻断 ⇒ 整轮判红，**即使异常被吞掉**。

    收集期 / 导入期 / 用例之外的阻断没有用例可判红（`<outside-a-test>`），而库又常把
    「连接失败」当常规错误吞掉——W-7 的真实出站正是这样滑过整轮绿跑的。所以这里不看
    「有没有失败用例」，只看「有没有那条记录」。
    """
    failures = guard.blocking_failures()
    if not failures:
        return
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
    writer = session.config.pluginmanager.get_plugin("terminalreporter")
    lines = [
        "",
        f"egress guard: FAIL — the default gate attempted {len(failures)} non-loopback "
        "destination(s) that no live marker allows:",
    ]
    lines += [
        f"  {item.target} (kind={item.kind}) by {item.nodeid} :: {item.origin}" for item in failures
    ]
    if writer is not None:
        for line in lines:
            writer.write_line(line)
    else:  # pragma: no cover - 无终端插件时仍要让判定可见
        print("\n".join(lines))
