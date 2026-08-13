"""S5: LocalWorkspace 生命周期（无 Docker、无网络）。

验证：LocalWorkspace 创建、写文件、execute_command（无害命令）、close/清理。
注意：LocalWorkspace.execute_command 是 host shell（spike 仅执行无害只读命令）。

已核实的 SDK 行为（v1.42.0）：
- file_upload/file_download 的路径是**裸 Path**（相对进程 CWD），
  不基于 working_dir 解析；git_changes/git_diff 才基于 working_dir。
  spike 因此使用绝对路径，并显式验证 CWD 无残留（防止污染仓库树）。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from openhands.sdk.workspace.local import LocalWorkspace


def main() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="s5-ws-"))
    cwd_before = {p.name for p in Path.cwd().iterdir()}
    try:
        ws = LocalWorkspace(working_dir=str(tmpdir))
        print(f"workspace: {type(ws).__name__} working_dir={ws.working_dir}")

        # 文件操作（upload/download 面：**绝对路径**，避免 CWD 相对解析假象）
        src = tmpdir / "src-spike.txt"
        dst = tmpdir / "dst-spike.txt"
        src.write_text("hello from spike", encoding="utf-8")
        ws.file_upload(str(src), str(tmpdir / "spike.txt"))
        ws.file_download(str(tmpdir / "spike.txt"), str(dst))
        print(f"file roundtrip: {dst.read_text(encoding='utf-8')!r}")
        assert dst.read_text(encoding="utf-8") == "hello from spike"

        # 无害命令（只读）
        out = ws.execute_command("echo spike-ok")
        print(f"execute_command output: {out!r}")

        # 确认 CWD 无文件副作用（LocalWorkspace file API 不基于 working_dir 解析）
        cwd_after = {p.name for p in Path.cwd().iterdir()}
        leaked = cwd_after - cwd_before
        print(f"cwd leak check: {sorted(leaked) if leaked else 'none'}")
        assert not leaked, f"CWD 泄漏文件: {sorted(leaked)}"

        print("S5 PASS")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"S5 FAILED: {type(exc).__name__}: {exc}")
        return 1
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())