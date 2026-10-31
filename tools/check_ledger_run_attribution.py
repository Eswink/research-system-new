#!/usr/bin/env python3
"""GOAL 的 `## CI 台账` **run 归属**校验器（GOAL-20261030-101 EC-03）。

**它补哪一格**（同一族错误**第四次**出现，纯靠人核已被证伪）：GOAL 的 CI 台账每行声称
「某个提交跑出了某个 run」。实测过的错法：把**后一个提交**的 run 记在前一个提交名下
（`f15929e5` / `f90e4840` 就是这样被 GOAL-100 的序 69 归档轮复核更正的；096 / 097 / 099
各有同形错误）。

**判什么**：对台账里每一行

- 有 run id ⇒ 查那批 run 的 `head_sha`，断言「某个 run 的 head **以本行的提交哈希开头**」，
  否则该行**要么**显式带 `covered_by`（「本提交没有自己的 run，被别的提交的 run 覆盖」）；
- 带 `covered_by: <hash>` ⇒ 断言那个哈希**在台账里真的有一行**（覆盖者必须是账上的提交，
  不许指一个不存在的提交）。

**这是出网面** ⇒ **默认门不跑**。只在显式 `--online` 时真的查 GitHub API；不给 `--online`
时它**只做静态自洽检查**（解析台账、`covered_by` 指向的哈希在不在账上），并明确打印
`ONLINE=skipped`。静态判据 `tests/tooling/test_ledger_run_attribution_stays_offline.py`
钉住两件事：① 本工具**不在**默认门的任何检查清单里；② 它**不 import** 任何网络库到
模块顶层（`--online` 分支里才 import）。

**取证口径（如实登记）**：run id → `head_sha` 的映射来自 GitHub REST
`/repos/{owner}/{repo}/actions/runs/{run_id}`。**一个 run 的 head 就是它的提交** ——
本工具不相信台账的散文，只相信 API 的 `head_sha`。

用法：

```bash
# 静态自洽（默认，零出网、零凭据）
uv run --frozen --no-sync python -B tools/check_ledger_run_attribution.py --root .

# 真查 GitHub（出网；凭据从 git credential fill 取，或 GH_TOKEN）
uv run --frozen --no-sync python -B tools/check_ledger_run_attribution.py --root . --online \\
    --goal .cursor/plans/goals/GOAL-20261029-100-submission-ready-and-citation-binding.md
```
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: 仓库的 slug（出网面用它拼 API 路径；与本仓 origin 一致）。
REPO = "Eswink/research-system-new"
#: 台账小节的标题。
LEDGER_HEADING = "## CI 台账"
#: 台账数据行：首格是**反引号包住的提交哈希**（短哈希，≥ 7 位）。
_ROW = re.compile(r"^\|\s*`([0-9a-f]{7,40})`\s*\|(.*)$")
#: run 链接里的 run id（`…/actions/runs/<digits>`）。
_RUN_ID = re.compile(r"/actions/runs/(\d+)")
#: `covered_by` 的写法。本仓台账里真实出现过三种，**冒号与等号都要认**：
#: ① 规范形态 ``covered_by: f90e4840``（冒号，反引号在**内**）；
#: ② ``**`covered_by: 1310dee4`**``（冒号 + 加粗，反引号在加粗**内**）；
#: ③ `` `covered_by` = `609bab8a` ``（等号 + 中间夹反引号，GOAL-092/098 的散文形态）。
_COVERED = re.compile(r"covered_by\**[^:=]{0,12}[:=]\s*`?([0-9a-f]{7,40}|\d{6,})`?")
#: `covered_by` 的**散文形态**（写了说明却没给哈希）。实测过一次：某行写
#: `covered_by: 见本行说明` —— 它既不是哈希也不是 run id ⇒ 正则读不到 ⇒ 上一版工具**静默放行**。
_COVERED_PROSE = re.compile(r"covered_by[*\s`:]*[:=]\s*(?![`\s]*[0-9a-f]{7,40})(?![`\s]*\d{6,})")
#: 「本行**声称**没有自己的 run」的三种写法（此时该行**必须**有 covered_by）。
_NO_RUN = re.compile(r"零 run|无 run|无\*\* run|\*\*无 run\*\*|没有自己的 run")


@dataclass(frozen=True, slots=True)
class LedgerRow:
    """台账的一行（`commit` 是**本行声称的**提交；`covered_by` 是它声明的覆盖者）。"""

    commit: str
    run_ids: tuple[str, ...]
    covered_by: str | None
    raw: str
    #: 本行是否**明写**「零 run / 无 run」—— 那种行不给 run 是**正确**的（不是漏写）。
    claims_no_run: bool = False
    #: 本行写了 `covered_by:` 但值**不是**哈希/run id（散文）⇒ 解析不到覆盖者。
    covered_by_prose: bool = False


def _ledger_table_only(body: str) -> str:
    """小节正文里**那张台账表**的行（表头首格含「提交」；表一结束就停）。

    **为什么必须窄到这里**（实测 4 条假红的根因）：`## CI 台账` 小节里有时紧跟别的表
    （状态历史 / 判据分类），那些行也以反引号哈希开头，语义却完全不同 —— 把它们当台账读
    会产出「明写无 run 却挂着 run」这类假红。
    """
    lines = body.splitlines()
    start = None
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        first = line.strip().strip("|").split("|")[0].strip()
        if "提交" in first:
            start = index + 1
            break
    if start is None or start >= len(lines):
        return ""
    collected = [lines[start]]  # 分隔行
    for line in lines[start + 1 :]:
        if not line.lstrip().startswith("|"):
            break
        collected.append(line)
    return "\n".join(collected)


def ledger_rows(text: str) -> tuple[LedgerRow, ...]:
    """`## CI 台账` 的数据行（到下一个 `## ` 为止；只认「反引号哈希开头」那种行）。"""
    start = text.find(LEDGER_HEADING)
    if start == -1:
        return ()
    tail = text[start + len(LEDGER_HEADING) :]
    stop = tail.find("\n## ")
    body = _ledger_table_only(tail[: stop if stop != -1 else len(tail)])
    rows: list[LedgerRow] = []
    for line in body.splitlines():
        match = _ROW.match(line)
        if match is None:
            continue
        commit = match.group(1)
        covered = _COVERED.search(line)
        claims_no_run = _NO_RUN.search(line) is not None
        covered_by_prose = covered is None and _COVERED_PROSE.search(line) is not None
        # run id **只从第二格（run 列）取**：说明格里常有指向**覆盖者**的 run 链接
        # （GOAL-092 的零 run 行就是这样），把它算进「本行的 run」会让每一行都自相矛盾。
        # 那一格若**自己写着**「无 run / 零 run」，里面的链接就是覆盖者的 ⇒ 不算本行的 run
        # （GOAL-096 的 `d683c7d3` 正是这一形态：`无 run（…被 624338c5 的 [M0 …] 覆盖…）`）。
        cells = line.strip().strip("|").split("|")
        run_cell = cells[1] if len(cells) > 1 else ""
        if _NO_RUN.search(run_cell) is not None:
            run_ids: tuple[str, ...] = ()
        else:
            run_ids = tuple(_RUN_ID.findall(run_cell))
        rows.append(
            LedgerRow(
                commit=commit,
                run_ids=run_ids,
                covered_by=covered.group(1) if covered else None,
                raw=line,
                claims_no_run=claims_no_run,
                covered_by_prose=covered_by_prose,
            )
        )
    return tuple(rows)


def _git_ok(*args: str) -> bool:
    """跑一条只读 git 命令，成功 ⇒ True（**不出网**；git 只读本地对象库）。"""
    result = subprocess.run(
        ("git", *args), capture_output=True, text=True, encoding="utf-8", check=False
    )
    return result.returncode == 0


def static_problems(rows: tuple[LedgerRow, ...]) -> list[str]:
    """**零出网**的自洽检查：`covered_by` 必须指向一个**真实存在且在本提交之后**的提交。

    两种写法都认（实测台账里两种都出现过）：
    - `covered_by: <hash>` ⇒ 该提交必须存在，且是本行提交的**后代**（同批推送的后续提交）；
    - `covered_by: <run id>` ⇒ 该 run 必须出现在账上某一行的 run 列里。

    **不要求**覆盖者在**同一本**台账里：跨 GOAL 的覆盖是真实形态（GOAL-096 的收口 tip
    被 GOAL-097 的提交覆盖）。
    """
    run_ids = {run for row in rows for run in row.run_ids}
    problems: list[str] = []
    for row in rows:
        covered = row.covered_by
        if covered is None:
            if row.covered_by_prose:
                problems.append(
                    f"`{row.commit}` 的 covered_by 写了说明但**没有哈希** ⇒ §5.9 要求真实覆盖者哈希"
                    "（散文既不是哈希也不是 run id，解析不到覆盖者）"
                )
            continue
        if covered.isdigit():
            if covered not in run_ids:
                problems.append(
                    f"`{row.commit}` 的 covered_by 指向 run {covered}，但账上没有任何一行的 run "
                    "是它 —— 覆盖者必须是账上的 run"
                )
            continue
        if not _git_ok("cat-file", "-e", f"{covered}^{{commit}}"):
            problems.append(
                f"`{row.commit}` 的 covered_by 指向 `{covered}`，但本地对象库里没有那个提交 "
                "—— 覆盖者必须是真实存在的提交"
            )
            continue
        if covered == row.commit:
            problems.append(
                f"`{row.commit}` 的 covered_by 指向它自己 —— 一个提交装不下自己的哈希，这不是覆盖"
            )
            continue
        # **不**要求「覆盖者在本行之后」：GitHub 对同批推送的合并只保证「有一个 run 的 head
        # 是那批里的**某一个**提交」，台账写作时谁先谁后取决于观察顺序 ⇒ 把方向钉成不变量
        # 会产生假红（本 GOAL 实测：GOAL-098 的 5 行被这样误判）。**只**验存在性。
    return problems


def _github_token() -> str:
    """凭据：环境变量 `GH_TOKEN` 优先，否则问 `git credential fill`（本仓既有手法）。"""
    import os

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        check=False,
    )
    for line in result.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no GitHub credential: set GH_TOKEN or run `git credential fill` first")


def fetch_head_sha(run_id: str, token: str) -> str:
    """**出网**：一个 run 的 `head_sha`（GitHub REST）。失败 ⇒ 空串（由调用方点名）。"""
    import httpx

    url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}"
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=20.0,
        )
    except httpx.HTTPError:
        return ""
    if response.status_code != 200:
        return ""
    payload: Any = response.json()
    head = payload.get("head_sha") if isinstance(payload, dict) else None
    return str(head or "")


def _row_problems(row: LedgerRow, resolve: Any, readings: dict[str, str]) -> list[str]:
    """一行在**在线**面的判词（把 `online_problems` 的复杂度压到可读范围）。"""
    if not row.run_ids:
        if row.covered_by is None and not row.claims_no_run:
            return [
                f"`{row.commit}` 既没有 run、也没写 `covered_by`、也没明写「无 run」 "
                "⇒ 无法判定归属（空着不等于零 run）"
            ]
        if row.covered_by is None:
            return [
                f"`{row.commit}` 明写「无 run」但没有 `covered_by` ⇒ 那批推送的 run 是谁？"
                "零 run 必须指名覆盖者"
            ]
        # 有 covered_by ⇒ 归属由**覆盖者那一行**的 run 承担（本行 run 列空着是对的）。
        return []
    if row.claims_no_run:
        # run id 只从**第二格**（run 列）取；说明格里的 run 链接指向覆盖者，不算本行。
        return [
            f"`{row.commit}` 的 run 列挂着 {list(row.run_ids)} 却同时明写「无 run」 "
            "⇒ 一行只能是一种形态"
        ]
    heads: list[str] = []
    for run_id in row.run_ids:
        head = resolve(run_id)
        readings[run_id] = head
        if head:
            heads.append(head)
    if not heads:
        return [f"`{row.commit}` 的 run {list(row.run_ids)} 全部查不到 head_sha"]
    if any(head.startswith(row.commit) for head in heads):
        return []
    if row.covered_by is not None:
        # 本行声明的 run 不是它自己的，但**显式**写了 covered_by ⇒ 允许。
        return []
    return [
        f"`{row.commit}` 名下的 run {list(row.run_ids)} 的 head 是 "
        f"{[head[:8] for head in heads]}，**没有一个**以本行提交开头"
        "（把别的提交的 run 记在本行名下；如属同批推送请显式写 covered_by）"
    ]


def online_problems(
    rows: tuple[LedgerRow, ...], resolver: Any = None
) -> tuple[list[str], dict[str, str]]:
    """逐行对拍「run 的 head == 本行提交」；`resolver(run_id) -> head_sha` 可注入（判据用）。"""
    resolve = resolver if resolver is not None else fetch_head_sha
    problems: list[str] = []
    readings: dict[str, str] = {}
    for row in rows:
        problems.extend(_row_problems(row, resolve, readings))
    return problems, readings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL CI ledger run-attribution check")
    parser.add_argument("--root", default=".", help="tree root")
    parser.add_argument("--goal", action="append", default=[], help="GOAL file (repeatable)")
    parser.add_argument("--online", action="store_true", help="actually query the GitHub API")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).resolve()
    goals = [Path(item) for item in args.goal]
    if not goals:
        goals = sorted((root / ".cursor" / "plans" / "goals").glob("GOAL-*.md"))
    token = ""
    if args.online:
        token = _github_token()

    def resolver(run_id: str) -> str:
        assert token, "online mode requires a token"
        return fetch_head_sha(run_id, token)

    total_rows = 0
    total_problems = 0
    for goal in goals:
        path = goal if goal.is_absolute() else root / goal
        if not path.is_file():
            print(f"MISSING {goal}")
            total_problems += 1
            continue
        rows = ledger_rows(path.read_text(encoding="utf-8"))
        if not rows:
            continue
        total_rows += len(rows)
        problems = static_problems(rows)
        if args.online:
            online, readings = online_problems(rows, resolver)
            problems = [*problems, *online]
            print(f"ONLINE=queried {len(readings)} run(s) for {path.name}")
        else:
            print(f"ONLINE=skipped {path.name} (static self-consistency only)")
        for problem in problems:
            print(f"FAIL {path.name}: {problem}")
        total_problems += len(problems)
        if not problems:
            print(f"PASS {path.name} ({len(rows)} row(s))")
    print(f"SUMMARY rows={total_rows} problems={total_problems} online={args.online}")
    return 1 if total_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
