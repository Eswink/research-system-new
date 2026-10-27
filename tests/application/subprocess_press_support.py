"""子进程按压的**共用形态**（GOAL-20261027-098 EC-03；自判据文件分列）。

**为什么单列**：`test_experiment_script_comes_from_the_plan.py` 卡在 450 行硬上限上，而它的
按压臂需要在**子进程**里跑一条行为用例（子进程读到的是**磁盘上的真字节**，
`importlib.reload` 会把新的类对象塞进共享模块、污染同会话的其它判据文件）。

**为什么按压必须这么写**（本轮两次实测的坑，逐条）：

1. **不能 `monkeypatch`**：改一个**已导入**的模块的函数，对它的字节码毫无影响 ⇒ 按压假绿
   （判据照旧通过，而实现其实没被改动）。
2. **`pytest` 目标必须带类名**：用例在类里时 `file.py::test_name` 是 **exit 4**
   （usage error），而 `4 != 0` 会被读成「按压成功」⇒ 又一次假绿。本模块的 `press_run`
   把这两种形态都收进一处：`target` 由调用方给**完整**目标名。
3. **复原按 raw 字节**：不是「改回来就行」，而是同一个 `sha256`。

**本模块不做任何断言**：它只改字节、跑子进程、复原。判什么由调用方决定。
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

#: 仓库根（`tests/application/` 的上两级）。子进程的 `cwd` 用它。
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class PressResult:
    """一次按压的读数：按压后的退出码、复原后的退出码、复原是否逐字节相同。"""

    pressed_code: int
    restored_code: int
    restored_digest_matches: bool

    @property
    def bit(self) -> bool:
        """按压**真的会响**（按压时红、复原后绿、复原逐字节相同）。"""
        return self.pressed_code != 0 and self.restored_code == 0 and self.restored_digest_matches


def run_target(target: str, *, timeout: int = 300) -> int:
    """在子进程里跑一个**完整**的 pytest 目标（含 `::Class`，若有），返回退出码。"""
    return subprocess.run(  # noqa: S603 - 固定 argv，无 shell
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            target,
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    ).returncode


def press_run(relative: str, needle: str, target: str) -> PressResult:
    """删掉 `relative` 里的 `needle` ⇒ 跑 `target` ⇒ **按 raw 字节**复原 ⇒ 再跑一次。"""
    path = ROOT.joinpath(*relative.split("/"))
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    if needle not in text:
        raise AssertionError(f"按压锚点不在 {relative}（实现已经换形 ⇒ 判据需要跟着改）")
    pressed = text.replace(needle, "", 1).encode("utf-8")
    if hashlib.sha256(pressed).hexdigest() == digest:
        raise AssertionError(f"按压没有改变 {relative} 的字节")
    try:
        path.write_bytes(pressed)
        pressed_code = run_target(target)
    finally:
        path.write_bytes(original)
    restored_matches = hashlib.sha256(path.read_bytes()).hexdigest() == digest
    return PressResult(
        pressed_code=pressed_code,
        restored_code=run_target(target),
        restored_digest_matches=restored_matches,
    )


__all__ = ["ROOT", "PressResult", "press_run", "run_target"]
