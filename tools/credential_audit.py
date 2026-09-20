"""明文凭据审计（GOAL-008 EC-03）。

把「仓库 / 记录 / 配置面 DB / 日志里没有明文凭据」从一句话变成**可复跑判据**：
审计逐面扫描、逐面报告「扫描文件数 + 命中数 + 放行数」，命中即非零退出。

四面（每面独立报告，缺面时如实记 `not_present`，**不写成 PASS**）：

1. `tracked`：`git ls-files` 的全部跟踪文件（文本；二进制按 NUL 字节嗅探跳过并计数）；
2. `records`：`.cursor/plans/**` 的记录（属跟踪集，单列以示强调——EC-03 明确点名）；
3. `config_db`：配置面 SQLite 文件（按字节扫；路径取 `RESEARCHOS_DB_PATH` 或默认值）；
4. `logs`：`data/**/*.log` 与 `scratch/*.log`（本机运行日志）。

三条纪律：

- **只报位置，不回声**：命中只输出 `路径:行 [模式名]`，**绝不**打印匹配文本
  （审计工具自己泄漏凭据就荒谬了）；
- **放行要写理由**：已知的无害字面量（例如一次性本地测试容器的密码）走
  `ALLOWED_SUBSTRINGS` 白名单并逐条给出理由，放行数单独统计——不用「没扫到」冒充通过；
- **该扫而扫不成 ≠ 没命中**：面扫描失败（例如根目录不是 git 工作树）记
  `not_a_git_tree` 并判红；只有「面本身不存在」（`not_present`）才算空面。

用法：`uv run --frozen --no-sync python -B tools/credential_audit.py [--json] [--root PATH]`

`--root` 默认本仓库根；指定它可就地审计**另一份 checkout**（收口时的干净 clone 封印）。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS_DIR = ".cursor/plans"
DEFAULT_DB = "data/research-os-control.db"
LOG_GLOBS = ("data/**/*.log", "scratch/*.log")
_SNIFF_BYTES = 8192

#: 已知无害字面量（匹配文本**包含**其中任一项即视为放行，逐条给理由）。
#:
#: 白名单按**值**匹配而不是按路径：把命中文件整个放行会让真实凭据贴进那个文件也无人报警，
#: 而按值匹配只放行这些**已逐个看过的**杜撰串——新出现的串仍然判红（WP-F 的反证正是这样做的）。
#: 表里只列**实际命中过并逐个看过**的串（`--json` 输出可复核每条的命中位置与条数）；
#: 本表自身含这些串，因此本文件也会出现「allowed」命中，属预期。
ALLOWED_SUBSTRINGS: dict[str, str] = {
    "research_os_m14_test": (
        "一次性本地测试容器的口令（infra/compose/postgres-test.yaml 起的 throwaway Postgres），"
        "不是任何环境的真实凭据"
    ),
    "change-me-now": "`.env.example` 里的**待替换占位**（字面含义即「改成你自己的」）",
    "sk-test": "测试替身用的固定串（fake gateway 不发起真实请求）",
    "sk-super-secret": "redaction 单测/夹具里的杜撰串家族（token / value / worker-token 三变体）",
    "sk-proj-abcdef1234567890": "redaction 单测里的杜撰串（证明 Bearer 形态会被脱敏）",
    "sk-abcdefghijklmnopqrstuvwxyz123456": "redaction 单测里的杜撰串（`key=<sk-…>` 形态）",
    "sk-abcdefghijklmnop1234567890": "redaction 单测里的杜撰串（`api-key` 响应头形态）",
    "sk-secret-token-12345678": "redaction 单测里的杜撰串（同时是异常消息用例）",
    "sk-secret-token-987654321": "relay gateway 单测里的杜撰串（证明鉴权头不落日志）",
    "sk-secret-1234567890abcdef": "凭据 Port 语义单测里的杜撰串（证明 repr 脱敏）",
    "sk-backfill-placeholder": "`tools/snapshot_migrate.py` 注册的**自述占位串**（非真实键）",
    "test-key-not-a-real-secret": "编排 skill 的 fakes.ts 里的自述占位串",
    "sup3rs3cret": "secret redaction 单测里的杜撰串（`user:sup3rs3cret@` 形态）",
    "secret123": "redaction 单测里的杜撰串（`https://user:secret123@` 形态）",
}
_MARKER = "-" * 3

#: 面的状态取值：`scanned`（扫成）、`not_present`（面本体不存在：还没建 DB、还没日志）、
#: `not_a_git_tree`（该扫却扫不成）。**只有前两者的「0 命中」才算通过**。
UNSCANNABLE_STATUSES = frozenset({"not_a_git_tree"})


def _patterns() -> dict[str, re.Pattern[str]]:
    """模式表：与治理 `validate.py` 同源的四类 + 本仓额外的 DSN 形态。

    两处**有意收紧**（否则审计会被表达式噪声淹没，门就不成门）：

    - `assigned-secret`：只认**带引号的字面量**值。治理版允许裸值，会把
      `api_key = self._api_key()` / `apiKey={form.apiKey}` / `secret = tmp_path...`
      这类**表达式**也算命中（本仓实测 20 处全是假阳性）；
    - `dsn-with-inline-password`：只认**内联字面量**口令，跳过 `$VAR` / `{placeholder}`
      形式的替换（那是配置模板，不是凭据）。

    字面量用拼接构造——审计源码自身不应出现**完整**的可用凭据形态。
    """
    key_prefix = "s" + "k-"
    google_prefix = "AI" + "za"
    quoted_literal = r"""["'](?=[^"'\n]{8,}["'])[^"'\n]+["']"""
    return {
        "openai-style-key": re.compile(r"\b" + key_prefix + r"[A-Za-z0-9_-]{20,}\b"),
        "google-style-key": re.compile(r"\b" + google_prefix + r"[A-Za-z0-9_-]{20,}\b"),
        "private-key-block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE " + "KEY-----"),
        "assigned-secret": re.compile(
            r"(?im)^\s*(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*" + quoted_literal
        ),
        "dsn-with-inline-password": re.compile(
            r"\b[a-z][a-z0-9+]*://[A-Za-z0-9_.-]+:"
            r"(?!\*\*\*|\$|\{)[^\s@/\"'`${}]{8,}@"
        ),
    }


@dataclass
class Hit:
    path: str
    line: int
    label: str
    allowed_by: str | None = None


@dataclass
class FaceReport:
    face: str
    status: str = "scanned"
    files: int = 0
    binary_skipped: int = 0
    hits: list[Hit] = field(default_factory=list)

    @property
    def allowed(self) -> list[Hit]:
        return [hit for hit in self.hits if hit.allowed_by is not None]

    @property
    def offenders(self) -> list[Hit]:
        return [hit for hit in self.hits if hit.allowed_by is None]

    def as_dict(self) -> dict[str, object]:
        return {
            "face": self.face,
            "status": self.status,
            "files_scanned": self.files,
            "binary_skipped": self.binary_skipped,
            "hits": len(self.hits),
            "allowed": len(self.allowed),
            "offenders": [f"{hit.path}:{hit.line} [{hit.label}]" for hit in self.offenders],
        }


def _allowed_by(matched: str) -> str | None:
    for literal, reason in ALLOWED_SUBSTRINGS.items():
        if literal in matched:
            return reason
    return None


def _scan_text(text: str, rel: str, patterns: dict[str, re.Pattern[str]]) -> list[Hit]:
    hits: list[Hit] = []
    for label, pattern in patterns.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            hits.append(Hit(rel, line, label, _allowed_by(match.group(0))))
    return hits


def _scan_file(
    path: Path, rel: str, patterns: dict[str, re.Pattern[str]]
) -> tuple[list[Hit], bool]:
    """返回 (命中, 是否二进制跳过)。"""
    raw = path.read_bytes()
    if b"\x00" in raw[:_SNIFF_BYTES]:
        return _scan_bytes(raw, rel, patterns), True
    return _scan_text(raw.decode("utf-8", errors="replace"), rel, patterns), False


def _scan_bytes(raw: bytes, rel: str, patterns: dict[str, re.Pattern[str]]) -> list[Hit]:
    """二进制面（配置面 DB）：按字节找**文本形态**的模式；行号对二进制无意义，记 0。"""
    text = raw.decode("utf-8", errors="ignore")
    return _scan_text(text, rel, patterns)


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _tracked_paths(root: Path) -> list[str] | None:
    """跟踪文件列表；根目录不是 git 工作树时返回 None（**没扫成**，不是「没命中」）。"""
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def audit_tracked(patterns: dict[str, re.Pattern[str]], root: Path) -> FaceReport:
    report = FaceReport("tracked")
    tracked = _tracked_paths(root)
    if tracked is None:
        report.status = "not_a_git_tree"
        return report
    for rel in tracked:
        path = root / rel
        if not path.is_file():
            continue
        hits, is_binary = _scan_file(path, rel, patterns)
        report.files += 1
        report.binary_skipped += int(is_binary)
        report.hits.extend(hits)
    return report


def audit_records(patterns: dict[str, re.Pattern[str]], root: Path) -> FaceReport:
    report = FaceReport("records")
    records_root = root / RECORDS_DIR
    if not records_root.is_dir():
        report.status = "not_present"
        return report
    for path in sorted(records_root.rglob("*")):
        if not path.is_file():
            continue
        hits, is_binary = _scan_file(path, _relative(path, root), patterns)
        report.files += 1
        report.binary_skipped += int(is_binary)
        report.hits.extend(hits)
    return report


def audit_config_db(patterns: dict[str, re.Pattern[str]], root: Path) -> FaceReport:
    import os

    report = FaceReport("config_db")
    rel = os.environ.get("RESEARCHOS_DB_PATH") or DEFAULT_DB
    path = Path(rel)
    if not path.is_absolute():
        path = root / rel
    if not path.is_file():
        report.status = "not_present"
        return report
    report.files = 1
    report.hits.extend(_scan_bytes(path.read_bytes(), _relative(path, root), patterns))
    return report


def audit_logs(patterns: dict[str, re.Pattern[str]], root: Path) -> FaceReport:
    report = FaceReport("logs")
    seen: set[Path] = set()
    for glob in LOG_GLOBS:
        for path in sorted(root.glob(glob)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            hits, is_binary = _scan_file(path, _relative(path, root), patterns)
            report.files += 1
            report.binary_skipped += int(is_binary)
            report.hits.extend(hits)
    if report.files == 0:
        report.status = "not_present"
    return report


def run_audit(root: Path | None = None) -> list[FaceReport]:
    base = ROOT if root is None else root
    patterns = _patterns()
    return [
        audit_tracked(patterns, base),
        audit_records(patterns, base),
        audit_config_db(patterns, base),
        audit_logs(patterns, base),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="plaintext credential audit (GOAL-008 EC-03)")
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable report on stdout"
    )
    parser.add_argument(
        "--root",
        default=None,
        help="audit another checkout instead of this repository root",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else None
    reports = run_audit(root)
    offenders = sum(len(report.offenders) for report in reports)
    unscannable = [
        f"{report.face}({report.status})"
        for report in reports
        if report.status in UNSCANNABLE_STATUSES
    ]
    if args.json:
        # stdout 只放 JSON（判据要能直接 parse）；结论走 stderr + 退出码。
        print(json.dumps([report.as_dict() for report in reports], ensure_ascii=False, indent=2))
        print(_verdict(offenders, unscannable), file=sys.stderr)
        return 1 if offenders or unscannable else 0
    for report in reports:
        print(
            f"{report.face:10} status={report.status:14} files={report.files:5} "
            f"binary={report.binary_skipped:3} hits={len(report.hits):3} "
            f"allowed={len(report.allowed):3} offenders={len(report.offenders):3}"
        )
        for hit in report.offenders:
            print(f"  OFFENDER {hit.path}:{hit.line} [{hit.label}]")
    print(_verdict(offenders, unscannable))
    return 1 if offenders or unscannable else 0


def _verdict(offenders: int, unscannable: list[str]) -> str:
    if unscannable:
        return f"FAIL: 面 {', '.join(unscannable)} 未扫成（该扫而扫不成不算通过）"
    if offenders:
        return f"FAIL: {offenders} plaintext credential offender(s); 命中位置见上（不回显匹配文本）"
    return "PASS: 四面扫描无明文凭据命中（放行项已逐条给理由）"


if __name__ == "__main__":
    sys.exit(main())
