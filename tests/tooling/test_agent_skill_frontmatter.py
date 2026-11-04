"""`.agents/skills/*/SKILL.md` 的形状判据：新增技能必须**可被发现且可被自动路由**。

**为什么需要**：`.cursor/skills/` 的 17 个技能由 `validate_cursor_framework.py`
管 frontmatter；`.agents/skills/` **不在**任何既有 validator 的射程内，而它正是
ZCode 能发现技能的两个根之一（`<repo>/.zcode/skills` 与 `<repo>/.agents/skills`）。

ZCode 的发现链（bundle 实测）：`resolveDefaultSkillRoots` → `skillRootsForBase` 产出
`join(base, ".zcode", "skills")` 与 `join(base, ".agents", "skills")`，base 从 cwd
逐级上溯到 git 根。发现之后，模型只会拿到 **name + 一行 description**，然后自己决定
要不要调 —— 所以这个文件同时判「形状」与「可路由性」：

- 名字与目录不一致 / 缺 description ⇒ 被发现但无法路由；
- description 没有触发条件 ⇒ 模型无从判断何时该调；
- 设了 `disable-model-invocation: true` ⇒ 自动选择被关掉。

frontmatter 字段集合同 `.cursor/skills/`（五字段闭集，禁 legacy `globs`）——
两处形态一致，避免同一技能迁到另一侧时出现两套写法。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
SKILLS_ROOT: Final[Path] = ROOT / ".agents" / "skills"

#: 与 `validate_cursor_framework.py` 用同一条正则（小写字母 / 数字 / 连字符）。
SKILL_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: 允许的 frontmatter 字段（五字段闭集；`globs` 是 legacy，已禁用）。
ALLOWED_FIELDS: Final[frozenset[str]] = frozenset({
    "name",
    "description",
    "paths",
    "disable-model-invocation",
    "metadata",
})

#: 单个技能正文的上限：技能是**按需加载**的，正文过长就失去索引价值。
MAX_SKILL_LINES: Final[int] = 200

#: 正文里引用的脚本（skill 相对路径形态）；不以下划线开头的会被执行，必须真实存在。
_SCRIPT_REFERENCE: Final[re.Pattern[str]] = re.compile(r"scripts/[A-Za-z0-9_./-]+\.py")


def _skill_files() -> list[Path]:
    if not SKILLS_ROOT.is_dir():
        return []
    return sorted(SKILLS_ROOT.glob("*/SKILL.md"))


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    """`(字段表, 正文)`；围栏缺失即返回空表（由判据点名）。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "\n".join(lines[index + 1 :])
        key, separator, value = line.partition(":")
        if separator and key.strip() and not key.startswith((" ", "-")):
            fields[key.strip()] = value.strip()
    return {}, text


def test_the_directory_exists_and_holds_skills() -> None:
    """空目录会让「显式调用」变成一个无声的承诺。"""
    assert SKILLS_ROOT.is_dir(), f"{SKILLS_ROOT} 不存在 ⇒ ZCode 侧没有任何可调用技能"
    assert _skill_files(), "`.agents/skills/` 下没有任何 SKILL.md"


def test_name_matches_the_directory_and_the_naming_regex() -> None:
    """`name` 必须与目录名逐字相等且合规（ZCode 用它做 Skill 工具的路由键）。"""
    for path in _skill_files():
        fields, _body = _frontmatter(path.read_text(encoding="utf-8"))
        expected = path.parent.name
        assert fields.get("name") == expected, f"{path} 的 name 必须等于目录名 {expected!r}"
        assert SKILL_NAME_RE.fullmatch(expected), f"{expected!r} 不是 kebab-case 技能名"


def test_every_skill_has_a_routable_description() -> None:
    """没有 `description` 的技能会被发现但无法路由 —— 索引注入也就拿不到一行。"""
    for path in _skill_files():
        fields, _body = _frontmatter(path.read_text(encoding="utf-8"))
        description = fields.get("description", "").strip()
        assert description, f"{path} 缺少 description"
        assert len(description) >= 20, f"{path} 的 description 过短，无法表达触发条件"


def test_frontmatter_uses_the_closed_field_set() -> None:
    """五字段闭集：多一个字段会让「这字段到底生效吗」变成不可判的问题。"""
    for path in _skill_files():
        fields, _body = _frontmatter(path.read_text(encoding="utf-8"))
        unknown = sorted(set(fields) - ALLOWED_FIELDS)
        assert not unknown, f"{path} 含不支持的 frontmatter 字段：{unknown}"


def test_skills_are_available_for_model_invocation() -> None:
    """技能必须**可被模型自动选择**：不得设 `disable-model-invocation: true`。

    `disable-model-invocation` 是 Cursor 的语义（禁止模型自动调用），ZCode 侧
    解析器里**没有这个字段**（bundle 实测零命中）。把它写成 `true` 在 ZCode 下不会
    阻止自动调用，却会在 Cursor 下真的禁掉 —— 两侧行为不一致，而这个文件的三个技能
    正是要被自动选中的。要阻止自动调用时应当在正文里写清边界，不靠这个字段。
    """
    for path in _skill_files():
        fields, _body = _frontmatter(path.read_text(encoding="utf-8"))
        disabled = fields.get("disable-model-invocation", "").strip().lower()
        assert disabled not in {"true", "yes", "1"}, (
            f"{path} 设了 disable-model-invocation: {disabled!r} ⇒ 模型不会自动选择它"
        )


def test_the_skills_root_is_one_zcode_scans() -> None:
    """发现面：技能根必须是 ZCode **真的**会扫的那个路径。

    ZCode 的 `skillRootsForBase` 只产出两个仓库内根：`<repo>/.zcode/skills` 与
    `<repo>/.agents/skills`。`.cursor/skills` **不在其中** —— 把它当成发现点会让
    「装了但调不到」，而且不报错。本判据把这一点钉在代码里：

    1. 技能根在 `.agents/skills`（与 `.zcode/skills` 二选一，这里选前者因为
       `.zcode/` 被 `.gitignore` 忽略、不可共享）；
    2. 技能根**必须**落在 git 根之内（ZCode 从 cwd 上溯到 git 根）；
    3. 每个技能目录都必须有 `SKILL.md`（ZCode 只认这个文件名）。

    反证：把技能挪到 `.cursor/skills` ⇒ 本判据必红。
    """
    assert SKILLS_ROOT == ROOT / ".agents" / "skills", (
        f"技能根必须在 .agents/skills（ZCode 的扫描根之一），实际 {SKILLS_ROOT}"
    )
    assert (ROOT / ".git").exists(), "技能根必须在 git 根之内（ZCode 上溯到 git 根为止）"
    for path in _skill_files():
        assert path.name == "SKILL.md", f"ZCode 只认 SKILL.md 这个文件名：{path}"
        assert path.parent.parent == SKILLS_ROOT, f"技能必须直接位于 {SKILLS_ROOT}/<name>/ 下"


def test_description_carries_a_routing_trigger() -> None:
    """`description` 必须写成**触发条件**，因为它就是模型用来路由的唯一依据。

    ZCode 在 system-reminder 里只给模型两样东西：技能名与这段一行描述。描述里若没有
    「什么时候用」，模型只能靠名字猜 —— 名字常常不足以区分同类任务。所以判两件事：

    1. 含显式的触发句式（`Use when` / `当…时` / `when`），不是纯名词短语；
    2. 不含「仅在用户明确要求时才用」这类**显式限定语** —— 那等于把自动选择关掉。

    反证：把描述改成纯名词短语 ⇒ 本判据必红。
    """
    for path in _skill_files():
        fields, _body = _frontmatter(path.read_text(encoding="utf-8"))
        description = fields.get("description", "").strip()
        lowered = description.lower()
        trigger_forms = ("use when", "use this when", "当", "时使用", "when ")
        assert any(form in lowered or form in description for form in trigger_forms), (
            f"{path} 的 description 没有触发条件（模型无从判断何时调用）：{description!r}"
        )
        explicit_only = ("仅当用户明确要求", "only when the user explicitly", "只有用户明确要求")
        matched = [phrase for phrase in explicit_only if phrase in description]
        assert not matched, f"{path} 的 description 含显式限定语 {matched} ⇒ 等于关闭自动选择"


def test_referenced_scripts_exist() -> None:
    """正文点名的脚本必须存在：死引用会让「跑这个脚本」变成一次白跑。"""
    for path in _skill_files():
        _fields, body = _frontmatter(path.read_text(encoding="utf-8"))
        for reference in sorted(set(_SCRIPT_REFERENCE.findall(body))):
            assert (path.parent / reference).is_file(), f"{path} 点名了不存在的 {reference}"


def test_skills_stay_within_the_line_budget() -> None:
    """正文是**按需加载**的：过长就失去索引价值，也更难被真读一遍。"""
    for path in _skill_files():
        count = len(path.read_text(encoding="utf-8").splitlines())
        assert count <= MAX_SKILL_LINES, f"{path} 有 {count} 行，超过 {MAX_SKILL_LINES} 行上限"
