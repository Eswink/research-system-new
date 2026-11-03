"""凭据四面审计的判据（GOAL-20261103-104 的执行纪律 5.9）。

**为什么单列**：`tools/goal104_closeout_assertions.py` 加进这一组会撞 450 行硬上限
（实测 495 行 ⇒ 规模门判红）。凭据面与七条 EC 的产品面是两件事，各有自己的契约，
拆开也便于单独按压。

**它补哪一格**：5.9 原文是「`credential_audit.py` 四面 `offenders=0`」——这是**一条要跑
的命令**，不是一句可以写进记录的结论。散文没有失效机制：写「已审计、无泄漏」与真的跑
一遍是两件事。所以收口验证器**自己跑**那次审计并逐面判读数。

**状态的合法取值**（照抄 `credential_audit.py` 自己的契约，不自行收紧）：

- `scanned`：面扫成了；
- `not_present`：面本体不存在（还没建 DB、还没日志）。干净 checkout 里 `data/**` 与
  `scratch/**` 都是 gitignore 的 ⇒ `config_db` / `logs` 必然落到这里；
- 其余（如 `not_a_git_tree`）是「**该扫而扫不成**」⇒ 判红。

第一版判据要求四个面都 `scanned`，被**两树复检**抓到：clean 侧
`not_scanned=['config_db','logs']` ⇒ 两树对不上。修法是对齐契约，**不是**放宽成
「只看退出码」（少扫一面也会退出 0）。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CREDENTIAL_AUDIT = "tools/credential_audit.py"
CREDENTIAL_FACES: tuple[str, ...] = ("tracked", "records", "config_db", "logs")
#: 合法状态（见模块 docstring 的三分）。
LEGAL_STATUSES: tuple[str, ...] = ("scanned", "not_present")


def _parse_faces(stdout: str) -> list[dict[str, Any]]:
    """从 `--json` 输出里取面报告（`PASS:` 行会混在 stdout 前面 ⇒ 找第一个 `[`）。"""
    start = stdout.find("[")
    if start == -1:
        return []
    parsed, _end = json.JSONDecoder().raw_decode(stdout[start:])
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def credential_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """跑审计并判四个面：面齐、状态合法、`offenders` 为空。"""
    script = toolbox.tree(root, CREDENTIAL_AUDIT)
    if not script.is_file():
        return [toolbox.verdict("credential-faces-clean", False, f"{CREDENTIAL_AUDIT} 不在树")]
    proc = subprocess.run(
        [sys.executable, "-B", str(script), "--json", "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(root),
    )
    faces = _parse_faces(proc.stdout)
    by_name = {str(face.get("face")): face for face in faces}
    missing = [name for name in CREDENTIAL_FACES if name not in by_name]
    bad_status = [
        name
        for name in CREDENTIAL_FACES
        if name in by_name and by_name[name].get("status") not in LEGAL_STATUSES
    ]
    offenders: dict[str, int] = {}
    for name in CREDENTIAL_FACES:
        if name in by_name:
            offenders[name] = len(by_name[name].get("offenders") or [])
    dirty = {name: count for name, count in offenders.items() if count != 0}
    ok = not missing and not bad_status and not dirty
    detail = f"missing={missing} bad_status={bad_status} offenders={dirty} exit={proc.returncode}"
    return [toolbox.verdict("credential-faces-clean", ok, "" if ok else detail)]
