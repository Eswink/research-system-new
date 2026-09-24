"""确定性「精确去重」基准实验（GOAL-014 EC-02 的真实实验体，纯标准库）。

实验问题：在一份**确定性生成**的语料上做精确重复检测，两两比较（O(n^2)）与哈希索引
（O(n)）在**结果一致**的前提下，比较次数差多少。两法都对同一份语料求出同一批重复项，
因此这条实验有一个**可判真伪**的结论（`agreement` 必须为真），而不是自证。

设计约束（与沙箱姿态一致）：

- **纯标准库**（沙箱镜像 `python:3.12-slim` 不含第三方包；不引入 package install）；
- **确定性**：语料由固定种子生成、两法均无随机性 ⇒ 同一 seed/镜像重跑得同一 metrics；
- **不出网、不读仓库**：全部输入在脚本内生成（容器只挂它自己的工作区）。

产出（对齐 `schemas/experiment_run_output_v1.schema.json` 与合约判据）：

- `metrics`：本实验的科学指标（**合约的 `ARTIFACT_EXISTS(metrics)` 判的就是它**）；
- `experiment_result.json`：执行器解析的标准输出契约（`experiment_run_id` 由执行器经
  环境变量交进来，逐字回声——解析器会比对，不等即判实验违约）。

`EXPERIMENT_RUN_ID` 缺失时**直接失败**（不猜 id）：没有它就没有可回溯的实验标识。
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

SEED = 7
N_ITEMS = 800
#: 语料里**故意**注入的重复项数（重复项由同一素材复制而来，两法都该找到它们）。
N_DUPLICATE_PAIRS = 40
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def build_corpus(seed: int, n_items: int, duplicate_pairs: int) -> list[str]:
    """确定性语料：`n_items - duplicate_pairs` 条唯一 + `duplicate_pairs` 条**复制**的重复项。"""
    # 固定种子是**可复现性**要求（同 seed/镜像 ⇒ 同 metrics），与"安全随机"无关：
    # 本脚本不生成任何秘密，`random` 在这里的用途是确定性构造语料。
    rng = random.Random(seed)
    width = 24
    unique = [
        "".join(rng.choice(ALPHABET) for _ in range(width))
        for _ in range(n_items - duplicate_pairs)
    ]
    items = list(unique)
    for index in range(duplicate_pairs):
        items.append(unique[index * 3 % len(unique)])
    rng.shuffle(items)
    return items


def pairwise_duplicates(items: list[str]) -> tuple[list[tuple[int, int]], int]:
    """两两比较：返回（重复对，比较次数）。纯 O(n^2)，是最直白的基线。"""
    pairs: list[tuple[int, int]] = []
    comparisons = 0
    for left in range(len(items)):
        for right in range(left + 1, len(items)):
            comparisons += 1
            if items[left] == items[right]:
                pairs.append((left, right))
    return pairs, comparisons


def indexed_duplicates(items: list[str]) -> tuple[list[tuple[int, int]], int]:
    """哈希索引：桶内才比较。返回（重复对，比较次数）——比较次数就是它的成本。"""
    buckets: dict[str, list[int]] = {}
    pairs: list[tuple[int, int]] = []
    comparisons = 0
    for index, item in enumerate(items):
        bucket = buckets.setdefault(item, [])
        for other in bucket:
            comparisons += 1
            if items[other] == item:
                pairs.append((other, index))
        bucket.append(index)
    return pairs, comparisons


def run() -> dict[str, object]:
    started = time.monotonic()
    items = build_corpus(SEED, N_ITEMS, N_DUPLICATE_PAIRS)
    flat_pairs, flat_comparisons = pairwise_duplicates(items)
    index_pairs, index_comparisons = indexed_duplicates(items)
    elapsed = time.monotonic() - started
    agreement = sorted(flat_pairs) == sorted(index_pairs)
    ratio = (flat_comparisons / index_comparisons) if index_comparisons else 0.0
    return {
        "seed": SEED,
        "n_items": len(items),
        "duplicates_expected": N_DUPLICATE_PAIRS,
        "duplicates_found": len(index_pairs),
        "pairwise_comparisons": flat_comparisons,
        "indexed_comparisons": index_comparisons,
        "comparison_reduction_ratio": round(ratio, 4),
        "agreement": agreement,
        "elapsed_time_s": round(elapsed, 4),
    }


def main() -> None:
    run_id = os.environ.get("EXPERIMENT_RUN_ID")
    if not run_id:
        raise SystemExit("EXPERIMENT_RUN_ID is required (the executor supplies it)")
    metrics = run()
    if metrics["agreement"] is not True or metrics["duplicates_found"] != N_DUPLICATE_PAIRS:
        raise SystemExit(
            "experiment self-check failed: "
            f"agreement={metrics['agreement']} found={metrics['duplicates_found']}"
        )
    Path("metrics").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    payload = {
        "experiment_run_id": run_id,
        "status": "SUCCEEDED",
        "artifact_refs": ["metrics"],
        "metrics": {key: value for key, value in metrics.items() if not key.endswith("_time_s")},
    }
    Path("experiment_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    print("duplicates_found=", metrics["duplicates_found"])
    print("comparison_reduction_ratio=", metrics["comparison_reduction_ratio"])


if __name__ == "__main__":
    main()
