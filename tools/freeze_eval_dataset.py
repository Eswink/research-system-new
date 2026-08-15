"""重算 EvalDataset 的 freeze digest 并写回 YAML 文件。

用法（PowerShell）：
    $env:PYTHONUTF8="1"
    uv run --frozen --no-sync python -B tools/freeze_eval_dataset.py ^
        examples/eval/datasets/unit_v1.yaml
维护规则：dataset case 内容变更后必须重跑本工具更新 digest；
未更新的文件会在加载时被 DatasetFreezeError 拒绝（fail-closed）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from packages.application.evaluation.registry import build_dataset


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python tools/freeze_eval_dataset.py <dataset.yaml>")
        return 2
    path = Path(sys.argv[1])
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print(f"{path}: must be a mapping")
        return 1
    payload = {**data, "id": path.stem}
    payload.pop("digest", None)
    dataset = build_dataset(payload)
    data["digest"] = str(dataset.digest())
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"{path}: digest updated to {data['digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
