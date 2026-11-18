"""EC-02：**旧站标识在产品面与判据面零命中**（白名单只给历史记录类）。

**它补哪一格**（GOAL-20261119-115 建档实测）：换站之后旧站地址与旧模型名仍散落在
配置、文档、判据与收口资产里 —— 于是「我们用的是新站」这句话在树上**不可判**：
两个站点同时"合法"。更糟的是旧模型名留在判据里，换站后那条判据会**假红**，
而红不代表被守的那件事坏了（GOAL-20261111-108 的口径修正正是这条教训）。

**受判面**（两条，都是"产品会读到或被 CI 执行"的面）：

- 产品面：`packages/` `services/` `adapters/` `examples/` `schemas/`
- 判据面：`tests/` `tools/`

**豁免白名单**（进本文件源码，逐条给理由）：历史记录类 —— 它们记录的是"当时是什么"，
改掉它们等于伪造历史（`.cursor/memory/entries/**`、`goals/evidence/**`、
`rechecks/**`、`tasks/**`、已收口 GOAL 正文、`MAINLINE.md`、`goals/archive/**`）。

**反证臂**：往 `examples/config/` 临时写一行旧地址 ⇒ 判红并点名（路径 + 行号）。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

#: 要清零的旧站标识（地址 + 三个旧模型名）。`hy4free` 是 `hy4-flash-free` 的子串
#: 反面：两者互不为子串，所以按字面量搜不会互相误伤。
STALE_MARKERS: tuple[str, ...] = (
    "192.168.101.9",
    "hy4free",
    "hy4-preview-f",
    "hy4flash-exp4",
)

#: 受判面（仓库相对路径前缀）。**只有这些**目录里的命中算违规。
PRODUCT_PREFIXES: tuple[str, ...] = (
    "packages/",
    "services/",
    "adapters/",
    "examples/",
    "schemas/",
)
CRITERION_PREFIXES: tuple[str, ...] = ("tests/", "tools/")

#: 历史记录类白名单（前缀 + **非空理由**）。改它们等于伪造历史。
#: 前缀以 `/` 结尾；**不带** `/` 的条目是**精确文件**豁免（洞面最小）。
EXEMPT: tuple[tuple[str, str], ...] = (
    (".cursor/memory/entries/", "工程记忆：记录的是当时的读数，不回填"),
    (".cursor/plans/goals/evidence/", "证据文件：一次真实运行的原始读数"),
    (".cursor/plans/rechecks/", "复检记录：对某次提交的历史判词"),
    (".cursor/plans/tasks/", "历史 PLAN：当时的目标与执行记录"),
    (".cursor/plans/goals/archive/", "归档宪章：不可变历史资产"),
    (".cursor/plans/goals/GOAL-20261111-108-", "已收口 GOAL 正文：历史记录"),
    (".cursor/plans/goals/GOAL-20261118-", "已收口 GOAL 正文：历史记录"),
    (".cursor/plans/goals/MAINLINE.md", "宪章程序表：历史刻度不可改写"),
    (".cursor/plans/goals/evidence/M0-WITNESS.json", "m0 见证：某次运行的字节快照"),
    (".cursor/plans/ALL_PLAN.md", "计划索引：历史计划标题不可回填"),
    (".cursor/experience/", "经验条目：历史记录"),
    (".cursor/plans/m12-r1_remediation_plan_aaca9616.plan.md", "旧一代整改计划：历史记录"),
    ("docs/roadmap/ROUNDS_", "轮次完成记录：当时的事实"),
    ("docs/roadmap/PA1_COMPLETION_RECORD.md", "完成记录：当时的事实"),
    ("docs/roadmap/MILESTONES.md", "里程碑历史：当时的事实"),
    (
        "tests/tooling/test_goal108_probe_readings.py",
        "它判的是 GOAL-108 台账（历史记录）里的读数；台账写的是 2026-11-11 的四个旧免费模型"
        " —— 判据与台账必须同时是当时的事实，改这里等于让判据去判一份被改过的历史。"
        "站点演进后『当前配置只用零价模型』由 tests/loaders/test_free_model_only_policy.py 判。",
    ),
)


def _tracked_files() -> list[str]:
    """仓库里**被跟踪**的文件（git ls-files）；未跟踪的草稿不参与。"""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line for line in result.stdout.splitlines() if line]


def _is_exempt(relative: str) -> str | None:
    for entry, reason in EXEMPT:
        if entry.endswith("/"):
            if relative.startswith(entry):
                return reason
        elif relative == entry:
            return reason
    return None


def _in_scope(relative: str) -> bool:
    return relative.startswith(PRODUCT_PREFIXES) or relative.startswith(CRITERION_PREFIXES)


def scan(extra: dict[str, str] | None = None) -> list[str]:
    """返回违规命中（`path:line: marker | text`）。

    **只读被跟踪文件**：`git ls-files` 是"这棵树声明拥有什么"的唯一来源，
    与产品/判据的实际执行面同源。二进制文件按 UTF-8 宽松解码（不会抛）。

    `extra` **非空时只看合成输入**（反证臂要判的是"这条注入会不会被抓"，
    而不是"当前树上还有没有别的命中" —— 后者会让反证臂被无关命中连带染红，
    于是它既证明不了咬合，也证明不了不误报）。
    """
    contents: dict[str, str] = dict(extra or {})
    if not contents:
        for relative in _tracked_files():
            if not _in_scope(relative) or _is_exempt(relative):
                continue
            path = _ROOT.joinpath(*relative.split("/"))
            if not path.is_file():
                continue
            contents[relative] = path.read_bytes().decode("utf-8", "replace")
    hits: list[str] = []
    for relative, text in contents.items():
        if _is_exempt(relative):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for marker in STALE_MARKERS:
                if marker in line:
                    hits.append(f"{relative}:{number}: {marker} | {line.strip()[:120]}")
    return hits


class TestTheStalePinsAreCleared:
    def test_the_scan_is_not_vacuous(self) -> None:
        """受判面非空：真的扫到了一批被跟踪文件（否则"零命中"是空真）。"""
        scoped = [item for item in _tracked_files() if _in_scope(item) and not _is_exempt(item)]
        assert len(scoped) > 200, f"受判面只有 {len(scoped)} 个文件 ⇒ 扫描不成立"

    def test_no_stale_marker_survives_in_the_product_or_criterion_face(self) -> None:
        hits = scan()
        assert not hits, "旧站标识仍在受判面里（换站未清干净）：\n" + "\n".join(hits)

    def test_every_exemption_has_a_reason(self) -> None:
        """白名单不得有空理由（"登记了"与"说明了为什么"是两件事）。"""
        empty = [prefix for prefix, reason in EXEMPT if not reason.strip()]
        assert not empty, empty


class TestTheCriterionBitesInBothDirections:
    """**反证臂**：合成注入必须被同一条扫描抓出来（否则判据只是同义反复）。"""

    @pytest.mark.parametrize("marker", STALE_MARKERS)
    def test_a_marker_injected_into_a_product_file_is_reported(self, marker: str) -> None:
        synthetic = {"examples/config/llm_endpoints.yaml": f"  base_url: http://{marker}:8798/v1\n"}
        hits = scan(extra=synthetic)
        assert any(marker in hit for hit in hits), hits

    def test_a_marker_inside_an_exempt_path_is_not_reported(self) -> None:
        """豁免面确实豁免（否则白名单形同虚设，历史记录会被要求改写）。"""
        relative = ".cursor/plans/rechecks/RECHECK-20261111-108-example.md"
        hits = scan(extra={relative: "旧站 192.168.101.9 的读数\n"})
        assert not hits, hits

    def test_a_clean_product_file_is_not_reported(self) -> None:
        """正控制：没有旧标识的文件不得被报（假阳性会让判据不可用）。"""
        synthetic = {"examples/config/llm_endpoints.yaml": "  base_url: https://opencode.ai/\n"}
        assert scan(extra=synthetic) == []
