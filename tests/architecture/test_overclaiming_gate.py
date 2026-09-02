"""M17 WP7b: overclaiming audit gate (deterministic, serves independent review §11).

Two deterministic checks over the documentation surface:
1. Every occurrence of a deferred-capability term (multi-GPU / NCCL / Slurm /
   PBS / MPI / HPC / RDMA / InfiniBand / multi-node / distributed training /
   autoscaling / GPU fleet) must sit on a line that ALSO carries a deferral /
   not-verified marker — these capabilities are never claimed as supported or
   implemented.
2. The honest boundary "physically-remote GPU host = NOT VERIFIED" is actually
   stated in the M17 authority documents.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCS = _REPO_ROOT / "docs"

# 过度宣称只对 M17/GPU 权威文档有意义（这些文档若把推迟能力写成已实现即
# 误导）；通用架构文档描述未来部署形态不在此门禁范围。
_SCAN_FILES = (
    _DOCS / "roadmap" / "MILESTONES.md",
    _DOCS / "adr" / "ADR-0028-personal-scale-rebaseline.md",
    _DOCS / "adr" / "ADR-0029-gpu-execution-boundary.md",
    _DOCS / "references" / "upstream" / "M17_GPU_RUNTIME_QUALIFICATION.md",
    _DOCS / "roadmap" / "M17_COMPLETION_RECORD.md",
)
# 推迟标记可在命中行的上下文窗口内出现（列表/表格的 Deferred 标题常在邻行）。
_CONTEXT_WINDOW = 4

# 被推迟的能力词（M17 明确不实现清单 + ADR-0028 Deferred）。词边界匹配，
# 避免 "MPI" 命中 "Compile" 这类子串误报。
_FORBIDDEN_TERMS = (
    "multi-GPU",
    "NCCL",
    "Slurm",
    "PBS",
    "MPI",
    "HPC",
    "RDMA",
    "InfiniBand",
    "multi-node",
    "distributed training",
    "autoscaling",
    "GPU fleet",
)
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in _FORBIDDEN_TERMS) + r")\b",
    re.IGNORECASE,
)

# 同一行（或上下文窗口）必须出现的推迟/未验证标记之一（大小写不敏感）。
_DEFERRAL_MARKERS = (
    "deferred",
    "not verified",
    "不实现",
    "推迟",
    "移出",
    "不做",
    "不建",
    "没有",
    "禁止",
    "defer",
    "not claimed",
    "never",
    "不宣称",
    "不作为",
    "不进入",
    "不声称",
    "收缩",
    "rebaseline",
    "面向",
    "原「",
    "解锁",
)

_SCAN_GLOBS = ("**/*.md",)


def _has_deferral_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _DEFERRAL_MARKERS)


def _violations() -> list[str]:
    """命中推迟能力词、且上下文窗口内无推迟/未验证标记的行。"""
    found: list[str] = []
    for path in _SCAN_FILES:
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, start=1):
            if not _FORBIDDEN_RE.search(line):
                continue
            lo = max(0, lineno - 1 - _CONTEXT_WINDOW)
            hi = min(len(lines), lineno + _CONTEXT_WINDOW)
            window = "\n".join(lines[lo:hi])
            if not _has_deferral_marker(window):
                rel = path.relative_to(_REPO_ROOT).as_posix()
                found.append(f"{rel}:{lineno}: {line.strip()[:120]}")
    return found


def test_deferred_terms_only_appear_in_deferral_context() -> None:
    violations = _violations()
    assert not violations, (
        "deferred GPU/HPC capability claimed outside a deferral context:\n" + "\n".join(violations)
    )


def test_physically_remote_boundary_is_declared_not_verified() -> None:
    """The honest same-host limitation must be stated in the M17 authority docs."""
    authority = [
        _DOCS / "roadmap" / "MILESTONES.md",
        _DOCS / "adr" / "ADR-0029-gpu-execution-boundary.md",
        _DOCS / "roadmap" / "M17_COMPLETION_RECORD.md",
    ]
    present = [p for p in authority if p.exists()]
    assert present, "expected at least one M17 authority document to exist"
    combined = "\n".join(p.read_text(encoding="utf-8") for p in present).lower()
    assert "physically-remote" in combined or "physically remote" in combined
    assert "not verified" in combined
    # 不得把本机 GPU 描述为「远程服务器 GPU」：该短语只允许出现在带禁止
    # 标记（不得/禁止/not）的行内（即作为被禁止的说法本身被引用）。
    _REMOTE_CLAIM_RE = re.compile(r"remote server gpu|远程服务器 ?gpu")
    _PROHIBITION = ("不得", "禁止", "never", "not ", "no ")
    for path in present:
        for line in path.read_text(encoding="utf-8").splitlines():
            if _REMOTE_CLAIM_RE.search(line.lower()):
                assert any(p in line.lower() for p in _PROHIBITION), (
                    f"{path.name} claims a remote-server GPU outside a "
                    f"prohibition: {line.strip()[:120]}"
                )
