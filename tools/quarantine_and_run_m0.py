"""代管 → 跑 m0 → 还原（+ 逐字节复核）：把「as-is 不可达时如何取证」脚本化。

**用途**（`docs/architecture/LOCAL_GATE_PROTOCOL.md` 第 4 节）：当本机 m0 的唯一红项由
**仓库外**文件造成（分类 (ii) 环境专属 / (iii) 门禁 scoping）时，取证需要一条「临时移出该文件
跑完整门、再原样归还」的动作。本脚本把这条动作脚本化，并把三条纪律做成**硬检查**：

1. **写者检查**：代管前记录 `size` / `mtime` / `sha256`；`--settle-seconds` 内 `mtime` 变化
   即**拒跑**（并发写者仍活跃 ⇒ 不要动别人的在制品）。
2. **逐字节复核**：归还后重新核对三者，任一不符 ⇒ 非零退出并打印差异（脚本**从不删除**文件）。
3. **口径如实**：输出明确标注「本终态行取自**代管后的树**」——不得读成「as-is 本机全绿」。

**边界**：只接受**未跟踪**（gitignored 或仓库外）的路径；对已跟踪文件直接拒跑（那属于改仓库）。
零出网、只读工作树（除代管/归还本身）、不 import 仓库代码。

用法：
  python -B tools/quarantine_and_run_m0.py --path scratch/self-governance-bootstrap-prompt.md
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNNER = ".cursor/skills/cursor-framework-check/scripts/run_all_checks.py"
TEST_DSN = "postgresql://research_os:research_os_m14_test@localhost:15432/research_os"
_GREEN = "PASS: profile=m0; 23 deterministic checks"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": _sha256(path)}


def _is_tracked(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def _m0_command() -> list[str]:
    return [
        sys.executable,
        "-B",
        RUNNER,
        "--profile",
        "m0",
        "--keep-going",
    ]


def _run_m0(log_path: Path) -> tuple[int, str]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["RESEARCHOS_POSTGRES_DSN"] = TEST_DSN
    env["DATABASE_URL"] = ""
    env["POSTGRES_DSN"] = ""
    lines: list[str] = []
    process = subprocess.Popen(
        _m0_command(),
        cwd=REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert process.stdout is not None
    with log_path.open("w", encoding="utf-8") as handle:
        for line in process.stdout:
            handle.write(line)
            lines.append(line)
    code = process.wait()
    terminal = lines[-1].strip() if lines else "<no output>"
    return code, terminal


def _quarantine(path: Path, quarantine_dir: Path) -> Path:
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target = quarantine_dir / path.name
    if target.exists():
        raise SystemExit(f"拒跑：代管目标已存在，先人工清理：{target}")
    shutil.move(str(path), str(target))
    return target


def _restore(quarantined: Path, original: Path) -> bool:
    if original.exists():
        raise SystemExit(f"拒跑：原路径已被占用，不会覆盖：{original}")
    shutil.move(str(quarantined), str(original))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Quarantine a repo-external file, run m0, restore."
    )
    parser.add_argument("--path", required=True, help="要代管的路径（必须**未被 git 跟踪**）")
    parser.add_argument("--settle-seconds", type=float, default=3.0, help="写者静置窗口（默认 3s）")
    parser.add_argument("--log", default="", help="m0 日志落盘路径（默认：临时目录）")
    args = parser.parse_args(argv)

    path = (REPO / args.path).resolve() if not Path(args.path).is_absolute() else Path(args.path)
    if not path.exists():
        print(f"拒跑：路径不存在：{path}", file=sys.stderr)
        return 2
    if _is_tracked(path):
        print(
            f"拒跑：{path} 是**已跟踪**文件——代管只用于仓库外/未跟踪的判红文件。",
            file=sys.stderr,
        )
        return 2

    before = _snapshot(path)
    print(f"代管前：{path}")
    print(f"  size={before['size']} mtime_ns={before['mtime_ns']} sha256={before['sha256']}")
    time.sleep(max(0.0, args.settle_seconds))
    settled = _snapshot(path)
    if settled != before:
        print("拒跑：静置窗口内文件发生变化（并发写者仍活跃）——不动别人的在制品。", file=sys.stderr)
        return 3

    quarantine_dir = Path(tempfile.mkdtemp(prefix="m0-quarantine-"))
    log_path = Path(args.log) if args.log else Path(tempfile.gettempdir()) / "m0-quarantine-run.log"
    quarantined: Path | None = None
    try:
        quarantined = _quarantine(path, quarantine_dir)
        print(f"已代管到：{quarantined}")
        code, terminal = _run_m0(log_path)
    finally:
        if quarantined is not None:
            _restore(quarantined, path)

    after = _snapshot(path)
    print(f"归还后：{path}")
    print(f"  size={after['size']} mtime_ns={after['mtime_ns']} sha256={after['sha256']}")
    if after != before:
        print("!! 逐字节复核不一致：文件内容/大小已变，请人工核查。", file=sys.stderr)
        print(f"   代管目录保留：{quarantine_dir}", file=sys.stderr)
        return 4

    print("逐字节复核：一致（size / mtime_ns / sha256 全等）")
    print(f"m0 退出码 = {code}；终态行 = {terminal}")
    print(f"日志：{log_path}")
    print(f"全绿判据（逐字）：{'命中' if terminal == _GREEN else '未命中'}")
    print("口径：本终态行取自**代管后的树**（该文件临时移出）——**不得**读成「as-is 本机全绿」。")
    shutil.rmtree(quarantine_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
