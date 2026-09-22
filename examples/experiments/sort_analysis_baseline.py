"""`sort_analysis_v1` 的执行阶段实验（真实容器内执行；GOAL-011 EC-03）。

实验内容：对输入语料做一次**确定性**的排序算法基线分析（stdlib only，
无第三方依赖、无 package install——沙箱镜像 `python:3.12-slim` 里也没有）。

产物（都写在容器工作区里，由既有 `ExperimentExecutor` 采集）：

- `analysis_report`（**文件名的字面量**）：合约声明的交付物名。制品 id 形如
  `<experiment_run_id>:analysis_report`，验收门的 `ARTIFACT_EXISTS(analysis_report)`
  按 `:` 之后的最后一段匹配，因此文件名必须**逐字**是它。
- `experiment_result.json`：既有实验输出契约（`experiment_run_id` / `status` /
  `artifact_refs` / `metrics`）。`experiment_run_id` 由执行器经环境变量
  `EXPERIMENT_RUN_ID` 交进来——解析器逐字比对，猜不得。

确定性：语料由固定种子生成；同一 seed/镜像 ⇒ 同一 metrics（M9/M12 的复现口径）。
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

SEED = 20260922
SIZES = (128, 512, 2048)
REPORT_NAME = "analysis_report"
RESULT_NAME = "experiment_result.json"


def _corpus(size: int) -> list[int]:
    # 固定种子是**可复现性**要求（同 seed/镜像 ⇒ 同 metrics），与"安全随机"无关：
    # 这里生成的是实验语料，不是密钥、令牌或任何安全材料。
    rng = random.Random(SEED + size)
    return [rng.randrange(0, 10 * size) for _ in range(size)]


def _measure(size: int) -> dict[str, object]:
    """一次排序的确定性测量：比较次数与耗时（耗时只作附注，不进判据）。"""
    data = _corpus(size)
    comparisons = 0

    def merge_sort(items: list[int]) -> list[int]:
        nonlocal comparisons
        if len(items) <= 1:
            return items
        middle = len(items) // 2
        left, right = merge_sort(items[:middle]), merge_sort(items[middle:])
        merged: list[int] = []
        i = j = 0
        while i < len(left) and j < len(right):
            comparisons += 1
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    started = time.perf_counter()
    ordered = merge_sort(data)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert ordered == sorted(data), "merge sort must agree with the reference ordering"
    return {"size": size, "comparisons": comparisons, "elapsed_ms": round(elapsed_ms, 3)}


def _write_report(workspace: Path, measurements: list[dict[str, object]]) -> None:
    lines = [
        "# Sort analysis baseline (sandboxed experiment)",
        "",
        f"seed: {SEED}",
        "",
        "| size | comparisons | elapsed_ms |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| {item['size']} | {item['comparisons']} | {item['elapsed_ms']} |"
        for item in measurements
    ]
    lines += ["", "Deterministic corpus; comparison counts are the judged quantity.", ""]
    (workspace / REPORT_NAME).write_text("\n".join(lines), encoding="utf-8")


def _write_result(workspace: Path, measurements: list[dict[str, object]]) -> None:
    run_id = os.environ.get("EXPERIMENT_RUN_ID", "")
    payload = {
        "experiment_run_id": run_id,
        "status": "SUCCEEDED",
        "artifact_refs": [REPORT_NAME],
        "metrics": {
            "worst_case_comparisons": max(int(item["comparisons"]) for item in measurements),
            "corpus_size": max(int(item["size"]) for item in measurements),
        },
    }
    (workspace / RESULT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def main() -> int:
    workspace = Path.cwd()
    measurements = [_measure(size) for size in SIZES]
    _write_report(workspace, measurements)
    _write_result(workspace, measurements)
    print(json.dumps({"measurements": measurements}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
