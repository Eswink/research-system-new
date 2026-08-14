"""stdio 子进程入口：`python -B -m tests.mcp_server.run_stdio [fault]`。"""

from __future__ import annotations

import sys

from tests.mcp_server.server import FAULTS, build_test_server


def main() -> None:
    fault = sys.argv[1] if len(sys.argv) > 1 else "none"
    if fault not in FAULTS:
        raise SystemExit(f"unknown fault: {fault}")
    build_test_server(fault).run(transport="stdio")


if __name__ == "__main__":
    main()
