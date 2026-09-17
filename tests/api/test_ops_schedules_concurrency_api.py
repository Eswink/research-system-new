"""控制面 SQLite 共享连接的并发写回归（GOAL-004 cycle 5 = EC-05 的证据面）。

场景与 cycle 7 的实测同形：**12 线程 × 2 次 `POST /ops/schedules`（共 24 次）**，
每次都是新名字 ⇒ 期望 24×201。历史实测（live 控制面，同一脚本同一参数）：

```text
修复前（无串行化）  19×201 / 2×500 / 2×404 / 1×409   500 = sqlite3.InterfaceError
加锁后（语句级串行） 23×201 /        1×404     / 0×500
```

本文件钉住的是**这一类**：并发写不抛 `InterfaceError`（5xx）、不出现"刚登记就 404"
（写后立读读不到）、24 条定义真的都落库。失败时用状态码分布说话（`Counter`），
不让"是哪一类失败"含糊过去。

周期 5 的判据：本用例在**当前实现**下的实测分布决定后续动作——干净 ⇒ 只把它
固化成正例；有 404（或 500）⇒ 先定位写后立读的可见性根因，再决定锁粒度怎么落。
"""

from __future__ import annotations

import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.sqlite.pool import ThreadLocalConnection
from tests.api.conftest import make_app_deps

_THREADS = 12
_POSTS_PER_THREAD = 2
_TOTAL = _THREADS * _POSTS_PER_THREAD
_PREFIX = "concurrency"


def _post_schedule(client: TestClient, name: str) -> int:
    response = client.post(
        "/ops/schedules",
        json={"name": name, "job": "retention", "interval_seconds": 30.0},
        headers={"Idempotency-Key": f"{_PREFIX}_{name}"},
    )
    return cast(int, response.status_code)


def _run_twelve_threads(client: TestClient, prefix: str) -> Counter[int]:
    """12 线程 × 2 次登记（共 24 次），返回状态码分布。

    `Barrier(_THREADS)` 让第一轮 12 个请求尽量同时打进去（复制 live 探针的并发形态），
    第二轮紧接着发——24 次请求分布在 12 个线程上。
    """
    names = [f"{prefix}_{index:02d}" for index in range(_TOTAL)]
    first_wave = threading.Barrier(_THREADS)
    codes: dict[str, int] = {}
    lock = threading.Lock()

    def worker(thread_index: int) -> None:
        mine = names[thread_index::_THREADS]  # 每个线程两次，名字互不重叠
        first_wave.wait()
        for name in mine:
            status = _post_schedule(client, name)
            with lock:
                codes[name] = status

    with ThreadPoolExecutor(max_workers=_THREADS) as pool:
        list(pool.map(worker, range(_THREADS)))

    distribution = Counter(codes.values())
    assert not [code for code in distribution if code >= 500], (
        f"并发写不得出现 5xx（InterfaceError 类）：{distribution}"
    )
    assert 404 not in distribution, f"刚登记的定义不得读不到（写后立读）：{distribution}"
    assert distribution == {201: _TOTAL}, f"每次登记都应成功一次：{distribution}"

    listed = {item["name"] for item in cast(Any, client.get("/ops/schedules").json())["schedules"]}
    assert set(names) <= listed, "24 条定义必须都能从读面列出来（真的落库）"
    return distribution


def test_twelve_threads_register_twenty_four_schedules_without_lost_writes(
    client: TestClient,
) -> None:
    """共享连接路径（`:memory:` 夹具）的并发写：仍是全 201、无 5xx、无 404。

    这一条是**基线**：内存库只能共用一条连接（SQLite 语义），并发正确性靠
    `SerializedConnection` 的语句级串行化。
    """
    _run_twelve_threads(client, "concurrency")


def test_the_same_load_passes_with_per_thread_connections(tmp_path: Path) -> None:
    """文件库路径：控制面走**每线程一条连接**，同一负载仍全 201、无 5xx、无 404。

    与上一条只差连接布局（`:memory:` ⇒ 每线程一条），所以它同时是"代理面兼容"
    与"粒度换掉后正确性不掉"的证据。`connection_count() >= 2` 钉住机制真的生效：
    并发请求落在不同线程上时，各自开了自己的连接。
    """
    from services.api.app import create_app

    deps = make_app_deps(db_path=str(tmp_path / "control_plane.db"))
    with TestClient(create_app(deps)) as client:
        _run_twelve_threads(client, "concurrency_pt")

    pool = cast(ThreadLocalConnection, deps._connection)
    assert pool.connection_count() >= 2, "文件库下并发线程必须各开自己的连接"
    assert pool.connection_count() < _TOTAL, (
        "连接随**线程**数增长，不是每次请求一条（24 次请求 ⇒ 连接数远小于 24）"
    )
    assert pool.close_all() >= 2, "关闭时把登记过的连接全部关掉"
