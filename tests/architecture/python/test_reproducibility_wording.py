"""结论口径同源判据（GOAL-008 EC-04 / AGENTS.md §4）。

判两件事：

1. **该说的话在**：口径面必须出现「可重复配置」这一档（中文原词或既有英文原词）；
2. **不该说的话不在**：**肯定式**宣称「完全可复现 / fully reproducible」判红。

第 2 条的判定形态（避免判「话题」而不是判「宣称」）：

- **加引号的提及**（「完全可复现」/ "fully reproducible"）是对该说法的**引用**，
  不是宣称 ⇒ 放行；
- 同一行含否定标记（禁止/不得/而非/不是/不能/不可/无法/没有/不宣称/不存在/≠/not/never/…）
  ⇒ 是否定句 ⇒ 放行；
- 其余（**不加引号 + 无否定**）⇒ 判红。

已知射程边界（如实登记，不假装覆盖）：引用-豁免是**行级**启发式——把肯定式宣称
加引号写出来可以绕过本判据；本判据挡的是「顺手把结论吹上去」这类默认漂移，
不是恶意规避。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

#: 口径必须出现的面（每个面至少一个原词；中英都对，按面既有语种取）。
REQUIRED_FACES: dict[str, tuple[str, ...]] = {
    "AGENTS.md": ("可重复配置",),
    "packages/domain/enums.py": ("可重复配置",),
    "packages/application/model_relay/live_run_record.py": ("可重复配置",),
    "services/api/dto/models.py": ("configuration reproducible",),
    "apps/web/src/features/models/ModelDetails.tsx": ("Configuration reproducible",),
    "docs/integration/LLM_ENDPOINTS.md": ("可重复配置",),
}

OVERCLAIM_PHRASES: tuple[str, ...] = (
    "完全可复现",
    "完全模型可复现",
    "fully reproducible",
    "fully model-reproducible",
)

NEGATION_MARKERS: tuple[str, ...] = (
    "禁止",
    "不得",
    "而非",
    "不是",
    "不能",
    "不可",
    "无法",
    "没有",
    "不宣称",
    "不存在",
    "≠",
    "not ",
    "never",
    "forbidden",
    "cannot",
)

_QUOTE_OPEN = "「“‘\"'"
_QUOTE_CLOSE = "」”\"'’"

#: 扫描面：口径会出现的代码/文档/记录；跳过产物与依赖目录。
_SCAN_ROOTS: tuple[str, ...] = (
    "AGENTS.md",
    "adapters",
    "apps/web/src",
    "docs",
    "examples",
    "packages",
    "services",
    "tests",
    ".cursor/plans",
)
_SCAN_SUFFIXES = (".py", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml")
_SKIP_DIRS = {"node_modules", "__pycache__", ".venv", "dist", ".git", "scratch"}


def _scan_files() -> Iterator[Path]:
    """扫描面。**本文件自身豁免**：它含故意构造的反例串（见文件末尾自检），
    那是夹具而不是宣称；豁免写在这里，不藏在规则里。"""
    self_path = Path(__file__).resolve()
    for root in _SCAN_ROOTS:
        target = REPO_ROOT / root
        if target.is_file():
            yield target
            continue
        for path in sorted(target.rglob("*")):
            if not path.is_file() or path.suffix not in _SCAN_SUFFIXES:
                continue
            if _SKIP_DIRS & set(path.relative_to(REPO_ROOT).parts):
                continue
            if path.resolve() == self_path:
                continue
            yield path


def _has_negation(line: str) -> bool:
    return any(marker in line for marker in NEGATION_MARKERS)


def _is_quoted(line: str, start: int, end: int) -> bool:
    # 空串是任何字符串的子串 ⇒ 边界处必须显式排除，否则「行尾」会被误判成「引号」
    before = line[start - 1] if start > 0 else ""
    after = line[end] if end < len(line) else ""
    return (before != "" and before in _QUOTE_OPEN) or (after != "" and after in _QUOTE_CLOSE)


def _overclaims(path: Path) -> list[str]:
    """本文件里**像宣称**的越级表述（引号提及与否定句不算）。"""
    hits: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _has_negation(line):
            continue
        for phrase in OVERCLAIM_PHRASES:
            index = line.find(phrase)
            while index != -1:
                end = index + len(phrase)
                if not _is_quoted(line, index, end):
                    rel = path.relative_to(REPO_ROOT).as_posix()
                    hits.append(f"{rel}:{lineno}: {line.strip()}")
                index = line.find(phrase, end)
    return hits


class TestRequiredWordingIsPresent:
    def test_every_face_carries_the_repeatable_configuration_wording(self) -> None:
        missing: list[str] = []
        for rel, phrases in REQUIRED_FACES.items():
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            if not any(phrase in text for phrase in phrases):
                missing.append(f"{rel} 缺 {phrases}")
        assert not missing, missing

    def test_the_verdict_enum_is_one_of_the_required_faces(self) -> None:
        """口径不是只在文案里：承载它的枚举本身也必须说这一档。"""
        assert "packages/domain/enums.py" in REQUIRED_FACES


class TestNoAffirmativeOverclaim:
    def test_scan_faces_are_non_empty(self) -> None:
        """扫描面为空 = **没扫成**，不是「没命中」。"""
        assert len(list(_scan_files())) > 50

    def test_no_affirmative_fully_reproducible_claim(self) -> None:
        violations: list[str] = []
        for path in _scan_files():
            violations.extend(_overclaims(path))
        assert not violations, "肯定式越级表述（应改成「可重复配置」或写成否定句/引用）：" + str(
            violations
        )

    def test_the_rule_judges_claims_not_topics(self) -> None:
        """规则自检：引用与否定句放行，肯定式宣称判红。"""
        assert _has_negation("禁止宣称完全可复现") is True
        assert _has_negation("本 run 是完全可复现的") is False

        def _quoted_here(text: str, phrase: str) -> bool:
            start = text.index(phrase)
            return _is_quoted(text, start, start + len(phrase))

        assert _quoted_here("结论：完全可复现", "完全可复现") is False
        assert _quoted_here("口径写着「完全可复现」这一档不存在", "完全可复现") is True
        assert _quoted_here("he said fully reproducible here", "fully reproducible") is False
        # 行尾的短语不得因为「后面没有字符」被当成引号收尾（空串是任何串的子串）
        assert _quoted_here("结论就是完全可复现", "完全可复现") is False
