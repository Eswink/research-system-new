"""GOAL-028 EC-04 判据：**台账逐提交审计**的两向反证（先红后绿）。

**被测对象**：`tools/audit_goal028_ledger.py` —— 把「批量推送的**每一个提交**都要有 run 行」
机械化。本文件喂**合成台账**（不依赖真实 CI 响应），断言判据在两个方向上都会咬：

- **漏记**：提交无自带 run 且无覆盖声明 ⇒ **判红**（并点名 sha）；
- **补齐**：同一条提交补上 `covered_by` + `coverage_note` ⇒ **判绿**；
- `cancelled` **不写原因** ⇒ 判红；写了原因 ⇒ 判绿；
- **空集合**（`commits == []`）与**空字段** ⇒ 判红（承 `MEM`：空集合 = 未取证，不是 OK）；
- **结构化绑定**（承 `MEM:141`）：覆盖声明必须是 40 位 sha + 非空说明 —— 散文喂不饱它。

**为什么是合成输入**：真实台账的原始 JSON 在 `scratch/`（gitignored，承 GOAL-026 `R26-7`）
⇒ 仓内可复跑的部分是**判据本身**；真实台账由收口复检在本机跑一次并留档。
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_AUDIT = _ROOT / "tools" / "audit_goal028_ledger.py"

#: 两个 40 位小写 hex（判据自造，与任何真实提交无关 —— 输入是合成台账）。
_SHA_HEAD = "a" * 40
_SHA_MID = "b" * 40


def _load() -> Any:
    """按路径加载被测工具（`tools/` 不是包 ⇒ 静态导入会让同一文件有两个身份）。

    **必须**先写 `sys.modules` 再 `exec_module`：否则 dataclasses 解析 `@dataclass`
    注解时 `sys.modules[cls.__module__]` 为 None（实测 `AttributeError: 'NoneType'
    object has no attribute '__dict__'`）。加载是**幂等**的（先查 `sys.modules`）。
    """
    name = "goal028_ledger_audit"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, _AUDIT)
    assert spec is not None and spec.loader is not None, _AUDIT
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def audit_module() -> Any:
    return _load()


def _run(ledger: Mapping[str, object]) -> list[Any]:
    """喂一份**合成台账**给被测审计（`Mapping` 而非 `dict`：dict 的值类型是不变的，
    字面量会被推断成更窄的嵌套类型 ⇒ 传参处 mypy 报 arg-type）。"""
    verdicts: list[Any] = _load().audit(ledger)
    return verdicts


def _failed(verdicts: list[Any]) -> list[str]:
    return [v.line() for v in verdicts if not v.ok]


def _ok(verdicts: list[Any]) -> bool:
    return all(v.ok for v in verdicts)


class TestAMissingCommitIsJudgedRed:
    """反证一向：漏记中间提交 ⇒ 判红；补齐 ⇒ 判绿（两向成对）。"""

    def test_a_commit_without_a_run_and_without_coverage_fails(self) -> None:
        ledger = {
            "commits": [
                {"sha": _SHA_HEAD, "runs": [_success_run("M0 Quality Gates")]},
                {"sha": _SHA_MID, "runs": []},
            ]
        }
        verdicts = _run(ledger)
        assert not _ok(verdicts), [v.line() for v in verdicts]
        assert any(_SHA_MID[:12] in detail for detail in _failed(verdicts)), _failed(verdicts)
        assert any("未取证" in detail for detail in _failed(verdicts)), _failed(verdicts)

    def test_the_same_commit_passes_once_the_coverage_is_declared(self) -> None:
        """补齐（结构化字段）⇒ 判绿 —— 与上一条成对，证明红来自「漏记」而非别的原因。"""
        ledger = {
            "commits": [
                {"sha": _SHA_HEAD, "runs": [_success_run("M0 Quality Gates")]},
                {
                    "sha": _SHA_MID,
                    "runs": [],
                    "covered_by": _SHA_HEAD,
                    "coverage_note": "与 head 同批推送，其 run 被 head 覆盖，由 head 的绿承担",
                },
            ]
        }
        verdicts = _run(ledger)
        assert _ok(verdicts), [v.line() for v in verdicts]


class TestTheCoverageDeclarationMustBeStructured:
    """承 MEM:141：判据绑定**结构化字段**，散文喂不饱它。"""

    @pytest.mark.parametrize(
        "entry",
        [
            {"sha": _SHA_MID, "runs": [], "coverage_note": "我口头保证它绿了"},
            {"sha": _SHA_MID, "runs": [], "covered_by": _SHA_HEAD},
            {"sha": _SHA_MID, "runs": [], "covered_by": "not-a-sha", "coverage_note": "x"},
            {"sha": _SHA_MID, "runs": [], "covered_by": _SHA_HEAD[:12], "coverage_note": "x"},
        ],
    )
    def test_a_prose_or_partial_declaration_fails(self, entry: dict[str, object]) -> None:
        verdicts = _run({"commits": [entry]})
        assert not _ok(verdicts), entry


class TestCancelledRunsMustCarryAReason:
    """`cancelled` 如实登记：记了结论还要写为什么。"""

    def test_cancelled_without_a_note_fails(self) -> None:
        ledger = {"commits": [{"sha": _SHA_HEAD, "runs": [_run_entry("cancelled")]}]}
        assert any("未登记原因" in detail for detail in _failed(_run(ledger)))

    def test_cancelled_with_a_note_passes(self) -> None:
        entry = _run_entry("cancelled")
        entry["cancellation_note"] = "同批第二批推送触发 cancel-in-progress"
        ledger = {"commits": [{"sha": _SHA_HEAD, "runs": [entry]}]}
        assert _ok(_run(ledger)), [v.line() for v in _run(ledger)]


class TestEmptySetsAndEmptyFieldsAreNotEvidence:
    """空集合 / 空字段 = 未取证（判红），不是 OK。"""

    def test_an_empty_commit_list_fails(self) -> None:
        verdicts = _run({"commits": []})
        assert not _ok(verdicts)
        assert any("未取证" in detail for detail in _failed(verdicts)), _failed(verdicts)

    @pytest.mark.parametrize("field", ["run_id", "name", "conclusion"])
    def test_an_empty_run_field_fails(self, field: str) -> None:
        entry = _success_run("M0 Quality Gates")
        entry[field] = ""
        verdicts = _run({"commits": [{"sha": _SHA_HEAD, "runs": [entry]}]})
        assert any("未取证" in detail for detail in _failed(verdicts)), _failed(verdicts)

    def test_a_short_sha_fails(self) -> None:
        verdicts = _run({
            "commits": [{"sha": "abc123", "runs": [_success_run("M0 Quality Gates")]}]
        })
        assert any("40 位" in detail for detail in _failed(verdicts)), _failed(verdicts)

    def test_a_non_terminal_run_fails(self) -> None:
        entry = _success_run("M0 Quality Gates")
        entry["status"] = "in_progress"
        verdicts = _run({"commits": [{"sha": _SHA_HEAD, "runs": [entry]}]})
        assert any("未到终态" in detail for detail in _failed(verdicts)), _failed(verdicts)


class TestTheCommandLineBitesBothWays:
    """CLI 层：空台账 ⇒ 退出码 1；良台账 ⇒ 退出码 0（判词行以 PASS/FAIL 开头）。"""

    def test_the_cli_exits_nonzero_on_an_empty_ledger(self, tmp_path: Path) -> None:
        path = tmp_path / "ledger.json"
        path.write_text(json.dumps({"commits": []}), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-B", str(_AUDIT), "--ledger", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)
        assert "FAIL [" in result.stdout, result.stdout
        assert "未取证" in result.stdout, result.stdout

    def test_the_cli_exits_zero_on_a_clean_ledger(self, tmp_path: Path) -> None:
        ledger = {"commits": [{"sha": _SHA_HEAD, "runs": [_success_run("M0 Quality Gates")]}]}
        path = tmp_path / "ledger.json"
        path.write_text(json.dumps(ledger), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-B", str(_AUDIT), "--ledger", str(path), "--expect-sha", "a" * 40],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        assert all(
            line.startswith(("PASS ", "FAIL ", "SUMMARY")) for line in result.stdout.splitlines()
        ), result.stdout


def _run_entry(conclusion: str) -> dict[str, object]:
    return {
        "run_id": 1,
        "name": "M0 Quality Gates",
        "status": "completed",
        "conclusion": conclusion,
        "run_attempt": 1,
    }


def _success_run(name: str) -> dict[str, object]:
    entry = _run_entry("success")
    entry["name"] = name
    return entry
