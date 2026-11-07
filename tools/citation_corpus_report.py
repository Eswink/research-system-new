#!/usr/bin/env python3
"""引用充分性的**语料读数**入口（GOAL-20261107-107 EC-05）。

**它补哪一格**：`citation_distribution` 是纯函数（收文本、不读盘）。要回答「仓内现在有
几份真实手稿、三个读数分布如何、够不够标定」，必须有人把**盘上真实字节**喂给它 —— 那就
是本脚本。它也是「一条命令就能标定」这句话里那条命令。

**为什么不去树里 glob `manuscript*.md`**：实测（2026-11-07）仓内 `manuscript*.md`
**0 命中** —— 真实手稿是内容寻址的 blob（`data/artifact-blobs/<digest>`，无扩展名），
名字与路径都不带 `manuscript`。所以语料的**唯一可靠来源**是 run 库里的 artifact 行：
按 artifact id 的后缀 `:manuscript.md` 认，再按 digest 到 blob store 取字节。

**它不做什么**：

* **不写阈值**。只打印分布与门的结论；`MIN_*` 一个字节都不改。
* **不改任何库**。只读打开（`mode=ro`），不建表、不写入。
* **不扫测试夹具**。夹具正文是受控短文本（GOAL-105 `F-2` 的读数），把它们算进语料
  会让分布失真 —— 因此只认 `data/` 下的 run 库。

用法：

    uv run --frozen --no-sync python -B tools/citation_corpus_report.py --root .
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: run 库所在目录（相对 `--root`）。语料只从这里来 —— 见模块 docstring。
DATA_DIR = "data"
#: 内容寻址 blob store（相对 `--root`；按 digest 前缀分桶）。
BLOB_DIRS = ("data/artifact-blobs", "artifact-blobs", ".artifacts")
#: 手稿制品的 id 后缀（`{task_id}:manuscript.md` 或 `{run_id}:manuscript.md`）。
MANUSCRIPT_SUFFIX = ":manuscript.md"


def _blob_path(root: Path, digest: str) -> Path | None:
    """按内容摘要定位 blob（三种分桶形态都试；都没有 ⇒ `None`）。"""
    hexdigest = digest.split(":", 1)[-1]
    for relative in BLOB_DIRS:
        base = root / relative
        if not base.is_dir():
            continue
        for candidate in (base / hexdigest, base / hexdigest[:2] / hexdigest):
            if candidate.is_file():
                return candidate
    return None


def _manuscripts_in(path: Path, root: Path) -> list[tuple[str, str]]:
    """一个 run 库里的手稿正文 → `[(label, text)]`（库不可读 ⇒ 空，不抛）。"""
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return []
    try:
        tables = {row[0] for row in connection.execute("select name from sqlite_master")}
        if "artifacts" not in tables:
            return []
        rows = list(connection.execute("select artifact_id, digest from artifacts"))
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    found: list[tuple[str, str]] = []
    for artifact_id, digest in rows:
        name = str(artifact_id or "")
        if not name.endswith(MANUSCRIPT_SUFFIX) or not digest:
            continue
        blob = _blob_path(root, str(digest))
        if blob is None:
            continue
        found.append((f"{path.stem}|{name[: -len(MANUSCRIPT_SUFFIX)]}", blob.read_text("utf-8")))
    return found


def collect_corpus(root: Path) -> list[tuple[str, str]]:
    """整棵树里的真实手稿（按 `data/*.db` 逐个库读；同一份 blob 只算一次）。"""
    corpus: list[tuple[str, str]] = []
    seen: set[str] = set()
    for database in sorted((root / DATA_DIR).glob("*.db")):
        for label, text in _manuscripts_in(database, root):
            # 同一次 run 可能被多个库引用（探针库的副本）⇒ 按正文去重，
            # 否则分布会被同一份手稿重复计数。
            if text in seen:
                continue
            seen.add(text)
            corpus.append((label, text))
    return corpus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="citation corpus readings (EC-05)")
    parser.add_argument("--root", default=".", help="tree root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable readings")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).resolve()

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.application.deliverable.citation_distribution import (
        MIN_CORPUS,
        calibration_gate,
        collect_readings,
        summarize,
    )

    corpus = collect_corpus(root)
    readings = collect_readings(corpus)
    distribution = summarize(readings)
    gate = calibration_gate(readings)
    payload = {
        "min_corpus": MIN_CORPUS,
        "manuscripts": distribution.manuscripts,
        "labels": [item.label for item in readings],
        "sentences": list(distribution.sentences),
        "marks": list(distribution.marks),
        "references": list(distribution.references),
        "single_support_total": distribution.single_support_total,
        "marks_per_sentence": list(distribution.marks_per_sentence),
        "sufficient": gate.sufficient,
        "missing": list(gate.missing),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"corpus: {distribution.manuscripts} manuscript(s), gate needs {MIN_CORPUS}")
    for reading in readings:
        print(
            f"  {reading.label}: sentences={reading.sentences} marks={reading.marks} "
            f"references={reading.references} single_support={reading.single_support_sections}"
        )
    print(f"gate: {'OPEN (may calibrate)' if gate.sufficient else 'CLOSED'}")
    for item in gate.missing:
        print(f"  missing: {item}")
    print("thresholds: not set by this tool (MIN_* live in citation_sufficiency)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
