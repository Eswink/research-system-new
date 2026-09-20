"""明文凭据审计的判据（GOAL-20260920-008 EC-03：`tools/credential_audit.py`）。

判据有两半，缺一不可：

1. **当前树干净**：四面（跟踪文件 / 记录 / 配置面 DB / 日志）逐一报告并断言 0 命中；
   同时断言「扫描面非空 且 状态为 `scanned`」——否则把审计改成什么都不扫、或让某个面
   扫失败，也能让本用例变绿；
2. **审计会咬**：在一个临时根（`--root`）里写一个**审计不认识**的杜撰键，断言审计判红
   并点名文件；再写一个白名单里的老串，断言**不算**命中（白名单只放行已看过的值）。

临时根用 `git init` 变成工作树：跟踪面在非 git 目录下会记 `not_a_git_tree` 并判红，
这是有意的（「该扫而扫不成」不算通过），所以反证要把这个前提摆正，才测得到想测的一面。
探针落在 `<root>/data/*.log`——`logs` 面正是扫这个位置，因此走的是生产同一套选择器。

审计**不回声**匹配文本（只报 `路径:行 [模式名]`），本用例也据此断言输出里不得出现触发串。
探针行用 `format` 拼装而非字面量赋值：用例源码自身不该出现「关键字 + 值」的凭据形态。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "credential_audit.py"

#: 待扫文本的形态模板（关键字与值在运行时拼装）。
_PROBE_TEMPLATE = '{kw}: "{value}"\n'
_PROBE_KEYWORD = "api_" + "key"

#: 仅供本用例使用的杜撰键：**故意**不在审计白名单里（否则「会咬」这条判据是空断言）。
_UNKNOWN_FAKE_KEY = "s" + "k-audit-probe-not-allowlisted-0001"
_KNOWN_FIXTURE = "s" + "k-backfill-placeholder"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(TOOL), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _probe_line(value: str) -> str:
    return _PROBE_TEMPLATE.format(kw=_PROBE_KEYWORD, value=value)


def _probe_root(tmp_path: Path, value: str) -> Path:
    """临时根：git 工作树 + `data/<name>.log` 里的一行探针。"""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    data = tmp_path / "data"
    data.mkdir()
    (data / "leak-probe.log").write_text(_probe_line(value), encoding="utf-8")
    return tmp_path


def _faces(report: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(item["face"]): item for item in report}


def test_repository_faces_are_scanned_and_clean() -> None:
    result = _run(["--json"], ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    faces = _faces(json.loads(result.stdout))
    assert set(faces) == {"tracked", "records", "config_db", "logs"}
    # 扫描面非空**且状态为 scanned**：两条件一起才排除「没扫还报绿」。
    for face in ("tracked", "records"):
        assert faces[face]["status"] == "scanned", face
    assert int(faces["tracked"]["files_scanned"]) > 100  # type: ignore[arg-type]
    assert int(faces["records"]["files_scanned"]) > 10  # type: ignore[arg-type]
    for face, item in faces.items():
        assert item["offenders"] == [], f"{face}: {item['offenders']}"


def test_unknown_key_is_flagged(tmp_path: Path) -> None:
    root = _probe_root(tmp_path, _UNKNOWN_FAKE_KEY)
    result = _run(["--json", "--root", str(root)], root)
    assert result.returncode == 1, result.stdout + result.stderr
    faces = _faces(json.loads(result.stdout))
    logs = faces["logs"]
    assert int(logs["files_scanned"]) == 1  # type: ignore[arg-type]
    assert logs["offenders"], "陌生键必须判红"
    assert any("leak-probe.log" in str(item) for item in logs["offenders"])  # type: ignore[union-attr]
    # 命中只落在探针那一面：其余三面（含跟踪面）不得被牵连。
    for face, item in faces.items():
        if face != "logs":
            assert item["offenders"] == [], f"{face}: {item['offenders']}"
    assert _UNKNOWN_FAKE_KEY not in result.stdout, "审计不得回声匹配文本"


def test_allowlisted_fixture_is_not_an_offender(tmp_path: Path) -> None:
    root = _probe_root(tmp_path, _KNOWN_FIXTURE)
    result = _run(["--json", "--root", str(root)], root)
    assert result.returncode == 0, result.stdout + result.stderr
    faces = _faces(json.loads(result.stdout))
    logs = faces["logs"]
    assert int(logs["files_scanned"]) == 1  # type: ignore[arg-type]
    assert int(logs["hits"]) >= 1  # type: ignore[arg-type]
    assert logs["allowed"] == logs["hits"], "白名单串应全部放行"
    for face, item in faces.items():
        assert item["offenders"] == [], f"{face}: {item['offenders']}"


def test_non_git_root_is_unscannable_not_clean(tmp_path: Path) -> None:
    """反证：把根指向非 git 目录时，跟踪面必须记 `not_a_git_tree` 并判红。"""
    (tmp_path / "stray.txt").write_text(_probe_line(_KNOWN_FIXTURE), encoding="utf-8")
    result = _run(["--json", "--root", str(tmp_path)], tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    faces = _faces(json.loads(result.stdout))
    assert faces["tracked"]["status"] == "not_a_git_tree"
    assert "not_a_git_tree" in result.stderr, "结论必须点名未扫成的面"
