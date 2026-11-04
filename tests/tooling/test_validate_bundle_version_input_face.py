"""旧版本串扫描的**输入面同样由 git 决定**（与链接检查同一口径，D-10）。

**为什么需要这条判据**：`check_versions()` 里的旧版本正则原先走裸 `os.walk`，于是
**任何客户端写进被忽略目录的状态快照**（例如 `.zcode/plans/` 下的会话计划）都会参与
判红 —— 本机门红而干净 checkout 绿，正是 D-10 要消灭的形态。同一文件的链接检查早已
按 git 面筛选，版本扫描是同一个缺陷剩下的一半。

判四条（与链接检查同一组身份，缺一不可）：

1. **被忽略的坏文件不判红**；
2. **同内容但已跟踪 ⇒ 仍判红**（安全边界：排除不得让已跟踪文件逃过）；
3. **被忽略目录里 force-add 的文件 ⇒ 仍判红**（已跟踪优先于忽略）；
4. **未跟踪未被忽略的新文件 ⇒ 仍判红**（输入面不是「只扫已跟踪」）。

夹具用**任意目录名**（`ignored-area/`），所以「按目录名特判」的实现会在这条判据上红。
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".cursor" / "skills" / "system-spec-check" / "scripts" / "validate_bundle.py"

#: 刻意不叫 `scratch` / `.zcode`：按目录名特判的实现会在这里红。
IGNORED_DIR = "ignored-area"

#: 命中旧版本正则的探针值。**刻意不用完整字面量**：本文件自身就在
#: `validate_bundle` 的扫描面内，写死形如「0 点 3 点 0」的三段式字符串会让这条判据把
#: **自己**判红（MEM-20260920-087 记录过同一形态的自伤）。拼接出来的值在运行期等价。
STALE_VERSION = ".".join(("0", "3", "0"))

#: 夹具的**当前**版本：刻意不用任何历史形态，这样命中的只有植入的探针。
CURRENT_VERSION = "9.9.9"

#: `check_versions()` 会核对这些主文档是否含 `v<version>`（夹具必须先满足）。
REQUIRED_DOCS = ("README.md", "AGENTS.md", "CODEX_BOOTSTRAP.md", "docs/PRODUCT.md", "CHANGELOG.md")

TRACKED_BAD = "docs/tracked-stale-version.md"
IGNORED_BAD = f"{IGNORED_DIR}/ignored-stale-version.md"
FORCE_ADDED_BAD = f"{IGNORED_DIR}/force-added-stale-version.md"
UNTRACKED_BAD = "docs/untracked-stale-version.md"

#: 驱动脚本：只跑被测函数并把判词打出来（`sys.argv[1]` = 被测脚本路径）。
_DRIVER = """\
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("validate_bundle_under_test", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.check_versions()
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


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _stale_doc() -> str:
    return f"# 探针\n\n历史版本 {STALE_VERSION} 的说明。\n"


def _fixture_root(tmp_path: Path) -> Path:
    """git 工作树夹具 + **前提断言**（前提不成立 ⇒ 判据空转，所以先钉住）。"""
    assert _git(tmp_path, "init", "-q").returncode == 0, "夹具需要 git 工作树"
    _write(tmp_path, "VERSION", f"{CURRENT_VERSION}\n")
    _write(
        tmp_path,
        ".cursor/framework.json",
        f'{{"framework_version": "{CURRENT_VERSION}", "version_source": "VERSION"}}',
    )
    _write(
        tmp_path,
        f"examples/protocols/ai_ml_research_v{CURRENT_VERSION}.yaml",
        f'id: ai_ml_research_v{CURRENT_VERSION}\nversion: "{CURRENT_VERSION}"\n',
    )
    for doc in REQUIRED_DOCS:
        _write(tmp_path, doc, f"# {doc}\n\nv{CURRENT_VERSION}\n")
    _write(tmp_path, ".gitignore", f"{IGNORED_DIR}/\n")
    for relative in (TRACKED_BAD, IGNORED_BAD, FORCE_ADDED_BAD, UNTRACKED_BAD):
        _write(tmp_path, relative, _stale_doc())
    assert _git(tmp_path, "add", TRACKED_BAD).returncode == 0
    assert _git(tmp_path, "add", "-f", FORCE_ADDED_BAD).returncode == 0
    # 前提：三个身份各自成立（忽略 / 已跟踪 / 未跟踪未忽略）。
    assert _git(tmp_path, "check-ignore", "-q", IGNORED_BAD).returncode == 0, "该文件必须被忽略"
    assert FORCE_ADDED_BAD in _git(tmp_path, "ls-files", "--cached").stdout
    assert UNTRACKED_BAD in _git(tmp_path, "ls-files", "--others", "--exclude-standard").stdout
    return tmp_path


def _scan_findings(root: Path) -> str:
    """在被测根上调用**被改的那个函数**，返回它的判词（换行已归一）。"""
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


def test_ignored_state_snapshots_are_skipped_while_tracked_files_are_still_judged(
    tmp_path: Path,
) -> None:
    findings = _scan_findings(_fixture_root(tmp_path))
    # ① 被忽略的坏文件 ⇒ 不判红（客户端状态快照不得让本机门变红）。
    assert IGNORED_BAD not in findings, f"被忽略的文件不得进判据：{findings}"
    # ② 同内容但已跟踪 ⇒ 仍判红（安全边界）。
    assert TRACKED_BAD in findings, f"已跟踪文件必须照扫：{findings}"
    # ③ 被忽略目录里 force-add 的已跟踪文件 ⇒ 仍判红。
    assert FORCE_ADDED_BAD in findings, f"已跟踪优先于忽略：{findings}"
    # ④ 未跟踪但未被忽略 ⇒ 仍判红。
    assert UNTRACKED_BAD in findings, f"未跟踪未忽略的文件必须照扫：{findings}"


def test_the_scan_face_is_unavailable_on_a_non_git_root(tmp_path: Path) -> None:
    """扫描根不在工作树 ⇒ 版本扫描**不得**静默通过（该扫却扫不成不算通过）。"""
    assert _git(tmp_path, "rev-parse", "--is-inside-work-tree").returncode != 0, (
        "夹具前提：临时目录不得落在任何 git 工作树内"
    )
    _write(tmp_path, "VERSION", f"{STALE_VERSION}\n")
    _write(tmp_path, ".cursor/framework.json", f'{{"framework_version": "{STALE_VERSION}"}}')
    _write(tmp_path, "docs/stray-stale-version.md", _stale_doc())
    driver = SCRIPT.read_text(encoding="utf-8")
    assert "git_decided_inputs()" in driver, "版本扫描必须复用 git 输入面"
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
    assert completed.returncode != 0, "非 git 根上该门必须硬失败"


def test_the_version_scan_reuses_the_git_input_face() -> None:
    """源码锚点：版本扫描里必须出现 `git_decided_inputs()` 的筛选（防止回退成裸 walk）。"""
    source = SCRIPT.read_text(encoding="utf-8")
    marker = "version_inputs = git_decided_inputs()"
    assert marker in source, f"版本扫描必须按 git 输入面筛选（缺 `{marker}`）"
    assert "if relative not in version_inputs:" in source, "筛选必须在循环体内生效"


def test_the_module_is_importable_by_path() -> None:
    """`scripts/` 不是包 ⇒ 按路径加载必须可行（判据自身的前提）。"""
    spec = importlib.util.spec_from_file_location("validate_bundle_probe", SCRIPT)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    sys.modules["validate_bundle_probe"] = module
    spec.loader.exec_module(module)
    assert callable(getattr(module, "check_versions", None))
