"""`validate_bundle` 的**输入面由 git 决定**（D-10 / GOAL-20260925-017 EC-01）。

判什么（四条，缺一不可）：

1. **gitignored 的坏文件不判红** —— 别人的未跟踪在制品不是本仓的产物（`R-3` 的成因）；
2. **同内容但已跟踪 ⇒ 仍判红** —— 这是本项的安全边界：排除**不得**让任何已跟踪文件逃过扫描；
3. **被忽略目录里 force-add 的已跟踪文件 ⇒ 仍判红** —— 直接钉住「已跟踪优先于忽略」；
4. **未跟踪但**未**被忽略的新文件 ⇒ 仍判红** —— 输入面是「已跟踪 ∪ 未跟踪未忽略」，
   不是「只扫已跟踪」（否则新写的文档会在被 `git add` 之前逃过判据）；
   并钉一条**门禁自身不可用**的硬失败：扫描根不是 git 工作树 ⇒ **点名**（`not_a_git_tree`）
   且退出码非 0，**不得**静默通过。

判据为什么长这样：

- 夹具里的被忽略目录用**任意名字**（`ignored-area/`，不是 `scratch/`）⇒ 排除规则若是
  「按目录名特判」这条判据就会红 —— 它是**名字无关**这一点的机器取证；
- 夹具是「git 工作树」而**不是**完整仓库：`validate_bundle` 是**多检查**脚本，别处检查
  （`check_index_links` 等）在骨架根上会先抛异常，从而把本判据要看的判词埋掉
  （实测过一次）。所以这里**直接驱动被改的那个函数**（`validate_local_markdown_links`）
  并在**同一次运行内**同时给出「该报的红」与「不该报的红」——正向对照与反向对照同源，
  排除「脚本什么都没扫也算绿」这一失效模式；
- 夹具**自身的前提**（该文件真的被忽略 / 真的已跟踪 / 根真的不在工作树内）逐条先断言：
  否则夹具一失效，判据就变成空转。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".cursor" / "skills" / "system-spec-check" / "scripts" / "validate_bundle.py"

#: 被忽略目录的名字**刻意不叫** `scratch`：按目录名特判的实现会在这条判据上红。
IGNORED_DIR = "ignored-area"
#: 指向**不存在**文件的本地链接（只有「存在性」这一条判据会命中它）。
MISSING_TARGET = "./goal017-missing-target.md"

TRACKED_BAD = "docs/tracked-bad-link.md"
IGNORED_BAD = f"{IGNORED_DIR}/ignored-bad-link.md"
FORCE_ADDED_BAD = f"{IGNORED_DIR}/force-added-bad-link.md"
UNTRACKED_BAD = "docs/untracked-bad-link.md"

#: 驱动脚本：**只**跑被改的那个函数并打印它的判词（`sys.argv[1]` = 被测脚本路径）。
_DRIVER = """\
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("validate_bundle_under_test", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.validate_local_markdown_links()
print("FINDINGS:")
for finding in module.ERRORS:
    print(finding)
print("DONE")
"""


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _bad_link_doc() -> str:
    return f"# 探针\n\n[probe]({MISSING_TARGET})\n"


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_root(tmp_path: Path) -> Path:
    """git 工作树夹具 + **前提断言**（前提不成立 ⇒ 判据空转，所以先钉住）。"""
    assert _git(tmp_path, "init", "-q").returncode == 0, "夹具需要 git 工作树"
    _write(tmp_path, ".gitignore", f"{IGNORED_DIR}/\n")
    for relative in (TRACKED_BAD, IGNORED_BAD, FORCE_ADDED_BAD, UNTRACKED_BAD):
        _write(tmp_path, relative, _bad_link_doc())
    assert _git(tmp_path, "add", TRACKED_BAD).returncode == 0
    assert _git(tmp_path, "add", "-f", FORCE_ADDED_BAD).returncode == 0
    # 前提：夹具三个身份各自成立（忽略 / 已跟踪 / 未跟踪未忽略）。
    assert _git(tmp_path, "check-ignore", "-q", IGNORED_BAD).returncode == 0, "该文件必须被忽略"
    assert FORCE_ADDED_BAD in _git(tmp_path, "ls-files", "--cached").stdout
    assert UNTRACKED_BAD in _git(tmp_path, "ls-files", "--others", "--exclude-standard").stdout
    return tmp_path


def _scan_findings(root: Path) -> str:
    """在被测根上跑**被改的那个函数**，返回它给出的判词（换行已归一）。"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", _DRIVER, str(SCRIPT)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "CURSOR_FRAMEWORK_ROOT": str(root)},
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "FINDINGS:" in completed.stdout and "DONE" in completed.stdout, completed.stdout
    body = completed.stdout.split("FINDINGS:", 1)[1].split("DONE", 1)[0]
    return body.replace("\\", "/")


class TestGitDecidedInputFace:
    def test_ignored_is_skipped_while_tracked_and_fresh_files_are_judged(
        self, tmp_path: Path
    ) -> None:
        root = _fixture_root(tmp_path)
        findings = _scan_findings(root)

        # ① gitignored 的坏文件 ⇒ 不判红。
        assert IGNORED_BAD not in findings, f"gitignored 文件不得进判据：{findings}"
        # ② 同内容但已跟踪 ⇒ 仍判红（安全边界）。
        assert TRACKED_BAD in findings, f"已跟踪文件必须照扫：{findings}"
        # ③ 被忽略目录里 force-add 的已跟踪文件 ⇒ 仍判红（已跟踪优先于忽略）。
        assert FORCE_ADDED_BAD in findings, f"已跟踪优先于忽略：{findings}"
        # ④ 未跟踪但未被忽略 ⇒ 仍判红（输入面不是「只扫已跟踪」）。
        assert UNTRACKED_BAD in findings, f"未跟踪未忽略的文件必须照扫：{findings}"

    def test_the_scan_face_is_available_on_a_git_root(self, tmp_path: Path) -> None:
        """反向对照：夹具是工作树 ⇒ **不得**出现「输入面不可用」——否则上面那条判据
        可能是靠「门禁直接罢工」而不是靠「按 git 面筛」变绿的。"""
        findings = _scan_findings(_fixture_root(tmp_path))
        assert "not_a_git_tree" not in findings, findings


class TestUnscannableRootFailsHard:
    def test_non_git_root_names_the_unscannable_face_and_exits_non_zero(
        self, tmp_path: Path
    ) -> None:
        """扫描根不是 git 工作树 ⇒ **点名** + 非 0 退出（「该扫却扫不成」不算通过）。"""
        assert _git(tmp_path, "rev-parse", "--is-inside-work-tree").returncode != 0, (
            "夹具前提：临时目录不得落在任何 git 工作树内"
        )
        _write(tmp_path, "docs/stray-bad-link.md", _bad_link_doc())
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "CURSOR_FRAMEWORK_ROOT": str(tmp_path)},
        )
        combined = completed.stdout + completed.stderr
        assert completed.returncode != 0, combined
        # 判词必须**当场**可见（不能因为别的检查先崩而消失）且**点名**未扫成的面。
        assert "not_a_git_tree" in combined, combined
        assert "门禁输入面不可用" in combined, combined
