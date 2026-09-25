"""GOAL-20260925-016 EC-04：三处「已拍板决定」的文档必须**在位且可引用**（离线判据）。

覆盖用户 2026-09-25 按 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 建议列拍板的三项
**文档类**决定：

- **D-07(b)**：`ADR-0031` 维持 `Proposed`，并**补一节「否证条件」**（什么证据会否证它 /
  何时该改判）——本节判据只断言**结构**（该节在位、`Status` 未变），不改 ADR 的结论。
- **D-08(b)**：`ModelCompatibilityProfile` **维持派生视图**（不建一等域实体、不动
  Canonical State），并把「**若要改成实体必须先出 ADR**」写成可引用的前置条件。
- **D-09(a)**：新增 `ADR-0032` 记录**既有非 ASCII 路径豁免**（30 条已跟踪路径
  **不重命名**，依据 `AGENTS.md` §13）。

**判据的形状**（每条都**可被按压**，不是恒真断言）：

1. **清单与现实双向比对**：非 ASCII 路径**实跑 `git` 数出来**（不是抄一个数字），
   与 `ADR-0032` 的清单逐条比对：现实中有的必须在清单里（漏登记 ⇒ 红），
   清单条数必须等于实数（清单被删空 / 现实变多 ⇒ 红）。
2. **枚举陷阱是判据的一部分**：`git ls-files` 默认受 `core.quotepath` 影响，会把非 ASCII
   路径**转义**成 `\\3xx` 形态 ⇒ 用「路径里有没有非 ASCII 码点」去数会得到 **0 条**（假绿）。
   本判据**同时**断言这两种形态，把「怎么数」钉住。
3. **按压**：把清单里的一条路径从文本里拿掉 ⇒ 比对函数必须报缺（而不是仍绿）；
   并断言「注入一条新的非 ASCII 路径」也会被抓到。

**边界**：本判据**不**改 `AGENTS.md` §13、**不**改任何门禁、**不**重命名任何路径——
它只验证「豁免这件事有可引用的依据、且依据与现实一致」。

**参数化而非拼接**：本判据对 `git` 的两次调用都写成**字面量参数列表**（argv），
不经 shell、不接受任何外部输入拼串。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADR_TOOLPACK = ROOT / "docs" / "adr" / "ADR-0031-toolpack-capability-policy.md"
ADR_NON_ASCII = ROOT / "docs" / "adr" / "ADR-0032-legacy-non-ascii-path-exemption.md"
MODEL_COMPATIBILITY = ROOT / "docs" / "architecture" / "MODEL_COMPATIBILITY.md"
INDEX = ROOT / "docs" / "INDEX.md"

EXPECTED_NON_ASCII = 30
UNRENAMED_CLAUSE = "既有历史路径不会仅为满足本规则而批量重命名"
FALSIFICATION_HEADING = "否证条件"
PRECONDITION_CLAUSE = "必须先出 ADR"


def raw_ls_files() -> list[str]:
    """`git ls-files` 的**默认**输出（受 `core.quotepath` 影响，非 ASCII 会被转义）。"""
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def unescaped_ls_files() -> list[str]:
    """关掉 `core.quotepath` 后的输出（非 ASCII 原样返回）。"""
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def non_ascii(paths: list[str]) -> list[str]:
    return sorted(path for path in paths if any(ord(char) > 127 for char in path))


def declared_non_ascii(text: str, reality: list[str]) -> list[str]:
    """现实里有、但**没有被写进**文本的路径（漏登记）。"""
    return [path for path in reality if path not in text]


def summary(text: str) -> dict[str, object]:
    """一条 ADR-0032 式的结构摘要，供断言与按压共用。"""
    reality = non_ascii(unescaped_ls_files())
    return {
        "count": len(reality),
        "missing": declared_non_ascii(text, reality),
        "cites_section_13": UNRENAMED_CLAUSE in text,
        "says_no_rename": "不重命名" in text,
        "accepted": "Status: Accepted" in text,
    }


def test_tracked_non_ascii_paths_are_enumerated_and_matched_by_the_adr() -> None:
    """现实与清单双向一致：数量为 30，且每一条都写进了 ADR-0032。"""
    facts = summary(ADR_NON_ASCII.read_text(encoding="utf-8"))
    assert facts["count"] == EXPECTED_NON_ASCII, (
        f"已跟踪的非 ASCII 路径应为 {EXPECTED_NON_ASCII} 条，实测 {facts['count']} 条；"
        f"新增非 ASCII 路径必须走 §13，而不是扩充豁免清单"
    )
    assert facts["missing"] == [], f"ADR-0032 的清单漏了这些已跟踪路径：{facts['missing']}"


def test_the_quoting_trap_is_pinned_so_naive_checks_cannot_fake_green() -> None:
    """枚举陷阱：默认 `core.quotepath` 下，朴素的非 ASCII 计数会得到 0（假绿）。"""
    naive = non_ascii(raw_ls_files())
    assert naive == [], (
        "默认 quotepath 下应数出 0 条（git 把非 ASCII 转义成 \\3xx 形态）；"
        "若这里变成非空，说明判据漏掉了「怎么数」这件事"
    )
    escaped = [line for line in raw_ls_files() if "\\3" in line]
    assert escaped, "默认输出里应存在转义形态的路径，否则上面的 0 条就不是那个陷阱造成的"


def test_adr_0032_records_the_exemption_with_its_basis() -> None:
    """ADR-0032 在位：含 §13 引文、明确「不重命名」、登记进 docs/INDEX.md。"""
    text = ADR_NON_ASCII.read_text(encoding="utf-8")
    facts = summary(text)
    assert facts["cites_section_13"], f"必须引用 AGENTS.md §13 的原文口径：{UNRENAMED_CLAUSE!r}"
    assert facts["says_no_rename"], "必须写明「不重命名」"
    assert facts["accepted"], "本 ADR 记录的是**已拍板**的豁免（D-09 取 (a)）"

    index = INDEX.read_text(encoding="utf-8")
    assert ADR_NON_ASCII.name in index, "豁免依据必须能从 docs/INDEX.md 走到"


def test_the_comparison_is_pressable() -> None:
    """按压：清单少一条 ⇒ 报缺；注入一条新的非 ASCII 路径 ⇒ 同样被抓到。"""
    text = ADR_NON_ASCII.read_text(encoding="utf-8")
    reality = non_ascii(unescaped_ls_files())
    victim = reality[0]

    without_one = text.replace(victim, "<removed>")
    assert declared_non_ascii(without_one, reality) == [victim], "清单少一条时应报出这一条"

    injected = [*reality, "docs/新路径.md"]
    assert declared_non_ascii(text, injected) == ["docs/新路径.md"], (
        "现实里出现新的非 ASCII 路径而清单没跟上时，必须被判为漏登记"
    )


def test_adr_0031_keeps_proposed_and_gains_falsification_conditions() -> None:
    """D-07(b)：ADR-0031 补「否证条件」节，且 `Status` **未变**（仍 Proposed）。"""
    text = ADR_TOOLPACK.read_text(encoding="utf-8")
    assert FALSIFICATION_HEADING in text, "D-07(b) 的交付物就是这一节"
    assert "Status: Proposed" in text, "D-07(b) 明文维持 Proposed"
    assert "Status: Accepted" not in text, "未拍板不得冒充已接受"


def test_the_derived_view_decision_is_written_down_with_its_precondition() -> None:
    """D-08(b)：维持派生视图，且「若要建一等域实体必须先出 ADR」是可引用的前置条件。"""
    text = MODEL_COMPATIBILITY.read_text(encoding="utf-8")
    assert "维持派生视图" in text, "D-08(b) 的决定必须写在兼容性文档里"
    assert PRECONDITION_CLAUSE in text, f"必须写明前置条件：{PRECONDITION_CLAUSE!r}"
    assert "Canonical State" in text, "必须点明它属于 Canonical State 边界问题"
    assert "回滚" in text, "必须要求迁移与回滚方案"
