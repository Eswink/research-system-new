"""GOAL-024 EC-03 判据：把「观测隐私」的两条条款与四条未覆盖面**钉在文档上**。

判据形态：

- **条款锚点**：两条条款必须**逐字**同时出现在 `docs/architecture/OBSERVABILITY.md` 与
  `docs/security/THREAT_MODEL.md`（两处同源，缺一处即判红）；
- **未覆盖面**：四条逐条在位（OBSERVABILITY 全称 + THREAT_MODEL 同口径简写）；
- **被点名的判据文件必须存在**（改名即判红）——条款不许悬空指向不存在的判据；
- **零夸大**：两份文档都必须带「不作安全结论」的同义锚点；
- **INDEX 登记**：`docs/INDEX.md` 必须登记这两处新增节。

纯函数（`missing_anchors` / `missing_files`）便于反证与按压：合成文本 / 合成路径即可判红。
"""

from __future__ import annotations

from pathlib import Path

OBSERVABILITY = "docs/architecture/OBSERVABILITY.md"
THREAT_MODEL = "docs/security/THREAT_MODEL.md"
INDEX = "docs/INDEX.md"
PIN_JUDGE = "tests/observability/test_privacy_boundary_clauses_are_pinned.py"

#: 条款锚点（两份文档都必须逐字包含）。
CLAUSE_ANCHORS: tuple[str, ...] = (
    "条款 ①（canonical 允许持有用户输入）",
    "条款 ②（非 canonical 出口不得含内容）",
)

#: 受判面与口径锚点（OBSERVABILITY 侧）。
SURFACE_ANCHORS: tuple[str, ...] = (
    "**受判出口（6 条）**",
    "**读面口径 = 白名单**",
    PIN_JUDGE,
)

#: 未覆盖面（OBSERVABILITY 全称 + THREAT_MODEL 同口径）。
UNCOVERED_FULL: tuple[str, ...] = (
    "未覆盖面 1：debug mode 的受控内容采样",
    "未覆盖面 2：真实 collector / 生产部署面未验证",
    "未覆盖面 3：CI 产物面不在射程",
    "未覆盖面 4：R-M1 未收口",
)
UNCOVERED_SHORT: tuple[str, ...] = (
    "debug mode 的受控内容采样**未验证**",
    "真实 collector / 生产部署面**未验证**",
    "**CI 产物面不在射程**",
    "**`R-M1` 未收口**",
)

#: 零夸大锚点（两份文档各一）。
NO_CLAIM_ANCHORS: tuple[str, ...] = (
    "**不作安全结论**",
    "**本节不是安全结论**",
)

#: INDEX 登记锚点。
INDEX_ANCHORS: tuple[str, ...] = (
    "2026-09-28 增「观测隐私边界与受判面」节",
    "**2026-09-28 增第 7 节：观测隐私条款与未覆盖面**",
)

#: 被点名的判据文件（**改名即判红**）。
NAMED_JUDGE_FILES: tuple[str, ...] = (
    "tests/observability/test_privacy_canary.py",
    "tests/observability/test_privacy_exit_census.py",
    "tests/observability/test_privacy_content_canary_end_to_end.py",
    "tests/observability/test_privacy_read_face_canary.py",
    PIN_JUDGE,
)


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def missing_anchors(text: str, anchors: tuple[str, ...]) -> list[str]:
    """返回缺失锚点（纯函数：合成文本即可反证）。"""
    return [anchor for anchor in anchors if anchor not in text]


def missing_files(paths: tuple[str, ...]) -> list[str]:
    """返回不存在的文件（纯函数：合成路径即可反证「改名即判红」）。"""
    return [path for path in paths if not Path(path).is_file()]


def test_the_two_clauses_are_stated_in_both_documents() -> None:
    findings: list[str] = []
    for path in (OBSERVABILITY, THREAT_MODEL):
        findings.extend(
            f"{path} 缺条款锚点:{item}" for item in missing_anchors(read(path), CLAUSE_ANCHORS)
        )
    assert not findings, findings


def test_observability_states_judged_surfaces_and_the_whitelist() -> None:
    findings = missing_anchors(read(OBSERVABILITY), SURFACE_ANCHORS)
    assert not findings, f"受判面/口径锚点缺失:{findings}"


def test_uncovered_scope_is_registered_item_by_item() -> None:
    findings = [
        f"{OBSERVABILITY} 缺未覆盖面:{item}"
        for item in missing_anchors(read(OBSERVABILITY), UNCOVERED_FULL)
    ]
    findings.extend(
        f"{THREAT_MODEL} 缺未覆盖面同口径:{item}"
        for item in missing_anchors(read(THREAT_MODEL), UNCOVERED_SHORT)
    )
    assert not findings, findings


def test_no_security_claim_language_is_pinned() -> None:
    findings = missing_anchors(read(OBSERVABILITY), NO_CLAIM_ANCHORS[:1])
    findings.extend(missing_anchors(read(THREAT_MODEL), NO_CLAIM_ANCHORS[1:]))
    assert not findings, f"零夸大锚点缺失:{findings}"


def test_named_judge_files_exist() -> None:
    findings = missing_files(NAMED_JUDGE_FILES)
    assert not findings, f"条款点名的判据文件不存在(改名即判红):{findings}"


def test_the_pinning_judge_names_itself_and_every_named_judge_file_is_referenced() -> None:
    text = read(OBSERVABILITY)
    findings = [path for path in NAMED_JUDGE_FILES if path not in text]
    assert not findings, f"OBSERVABILITY 没有点名这些判据:{findings}"


def test_documents_are_registered_in_the_index() -> None:
    findings = missing_anchors(read(INDEX), INDEX_ANCHORS)
    assert not findings, f"docs/INDEX.md 缺登记:{findings}"


def test_a_renamed_judge_file_is_red() -> None:
    """按压：把被点名的判据文件换成不存在的路径 ⇒ 判红并点名。"""
    renamed = tuple(list(NAMED_JUDGE_FILES[:-1]) + ["tests/observability/__renamed_pin_judge.py"])
    findings = missing_files(renamed)
    assert findings and "__renamed_pin_judge" in findings[0], findings


def test_a_missing_clause_anchor_is_red() -> None:
    """反证：条款锚点被改写 ⇒ 判红并点名（文档被编辑改坏了抓得住）。"""
    findings = missing_anchors("这里没有条款", CLAUSE_ANCHORS)
    assert findings == list(CLAUSE_ANCHORS), findings
