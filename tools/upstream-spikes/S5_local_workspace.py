"""S5: LocalWorkspace 生命周期（无 Docker、无网络）。

验证：LocalWorkspace 创建、写文件、execute_command（无害命令）、close/清理。
注意：LocalWorkspace.execute_command 是 host shell（spike 仅执行无害只读命令）。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from openhands.sdk.workspace.local import LocalWorkspace


def main() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="s5-ws-"))
    try:
        ws = LocalWorkspace(working_dir=str(tmpdir))
        print(f"workspace: {type(ws).__name__} working_dir={ws.working_dir}")

        # 文件操作（upload/download 面：路径参数）
        src = tmpdir / "src-spike.txt"
        dst = tmpdir / "dst-spike.txt"
        src.write_text("hello from spike", encoding="utf-8")
        ws.file_upload(str(src), "spike.txt")
        ws.file_download("spike.txt", str(dst))
        print(f"file roundtrip: {dst.read_text(encoding='utf-8')!r}")

        # 无害命令（只读）
        out = ws.execute_command("echo spike-ok")
        print(f"execute_command output: {out!r}")

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