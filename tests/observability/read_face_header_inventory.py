"""GOAL-025 EC-01 读面响应头清单：逐条显式分类 + 纯函数自审 + 头值扫描。

**为什么需要**：GOAL-024 的读面判据通过 `read_face_canary_support.response_text()`
**只读响应体**；响应头**字面上不在扫描面**（收口时登记为残余 `G24-2`）。而本仓读面**确实**
在发 `Content-Disposition`（`filename` 取自 `artifact.id`）与 `ETag`（取自 `artifact.digest`）
⇒ 回显类头是**真实存在**的面，不是假想面。

**口径（承 MEM-158）**：读面响应头与被扫的响应体一样属于**非 canonical 出口**。头部清单是一个
**分区**，三种判定，没有第四种状态：

- `JUDGED` —— **回显类**头（取值由运行期数据派生）⇒ 必须证明「内容金丝雀零命中」，
  且**必须在本轮被真的观测到**（否则受判面为空 ⇒ 空真，承 MEM-156）；
- `EXEMPT` —— 取值**结构上不可能承载内容**（常量 / 计数 / 媒体类型），理由非空，
  并且有一条**机械的值形态断言**（不是散文）；
- `ABSENT` —— **登记为不发射**（机械理由：产品根零发射点）⇒ 一旦在运行期被观测到即判红
  （免得「已登记的不发射头」静默地变成新的回显面）。

**边界（否则判据会自伤）**：`JUDGED` 判的是**内容（正文）**不回头，**不是**「头里不许出现任何
运行期字符串」。`Content-Disposition.filename` 按契约回显 `artifact.id`（字符类净化 + 尾 120
截断），而 id 本来就在 `/artifacts/{artifact_id}` 元数据面上按契约可见 ⇒
**标识符回显 ≠ 内容回显**。因此夹具自己的 id **不得**携带金丝雀 token
（`test_privacy_read_face_headers.py` 有专门断言钉住这条边界）。
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass

from tests.observability.content_canary_support import CANARIES, Canary, hits

JUDGED = "judged"
EXEMPT = "exempt"
ABSENT = "absent"


@dataclass(frozen=True, slots=True)
class HeaderRule:
    """一条响应头的判定（`note` 为理由，不得为空）。"""

    name: str
    verdict: str
    note: str


#: 头部清单：**逐条显式**（新增的头必须显式进来，否则运行期观测到即判红）。
HEADER_RULES: tuple[HeaderRule, ...] = (
    HeaderRule(
        "content-disposition",
        JUDGED,
        "回显类：`filename` 取自 `artifact.id`（字符类净化 + 尾 120 截断）"
        "⇒ 标识符回显面；受判命题是**内容**零命中（标识符回显是契约行为，见模块 docstring 的边界）",
    ),
    HeaderRule(
        "etag",
        JUDGED,
        "回显类：取值由运行期数据派生，**两个来源** —— 制品路由 "
        "`services/api/routers/artifacts.py` 取 `f'\"{artifact.digest}\"'`；"
        "草稿路由 `services/api/routers/protocol_drafts.py` 取 `f'\"{record.revision}\"'`"
        "（修订号）⇒ 两者都是标识符 / 计数，但取值面同样逐字节受扫（内容零命中）",
    ),
    HeaderRule(
        "content-type",
        EXEMPT,
        "媒体类型字面量：服务端按制品 `media_type` 取（`application/json` / `text/*` / "
        "`application/octet-stream`），不承载正文",
    ),
    HeaderRule(
        "content-length",
        EXEMPT,
        "十进制字节计数：纯数字结构上不可能承载内容",
    ),
    HeaderRule(
        "x-content-type-options",
        EXEMPT,
        "常量 `nosniff`：服务端固定值，不由运行期数据派生",
    ),
    HeaderRule(
        "last-modified",
        ABSENT,
        "登记为**不发射**：产品根实测**零发射点**（全仓唯一显式设头点是 "
        "`services/api/routers/artifacts.py` 的 `_content_headers()`，其中不含它）"
        "⇒ 一旦观测到即判红，需重新分类",
    ),
)

#: 受判面**下界**：受判头不许收缩（否则把受判头改判成豁免就能全绿；承 MEM-160）。
MIN_JUDGED = 2

#: 本轮**实取到响应**的路由下界（防空转绿；与读面判据同口径）。
MIN_EXERCISED = 40

#: 媒体类型允许的字符（保守但足够：`application/json; charset=utf-8` 一类）。
_MEDIA_TYPE_CHARS = "/+-.=; '\""


def _is_decimal(value: str) -> bool:
    return bool(value) and value.isdigit()


def _is_nosniff(value: str) -> bool:
    return value == "nosniff"


def _is_media_type(value: str) -> bool:
    return bool(value) and all(char.isalnum() or char in _MEDIA_TYPE_CHARS for char in value)


#: 豁免头的**机械值形态**（散文理由之外的第二道；缺形态断言的豁免头会被自审判红）。
_EXEMPT_SHAPES: Mapping[str, Callable[[str], bool]] = {
    "content-type": _is_media_type,
    "content-length": _is_decimal,
    "x-content-type-options": _is_nosniff,
}


def all_names() -> tuple[str, ...]:
    return tuple(rule.name for rule in HEADER_RULES)


def judged_names() -> tuple[str, ...]:
    return tuple(rule.name for rule in HEADER_RULES if rule.verdict == JUDGED)


def normalized(pairs: Iterable[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    """头名一律小写（httpx 已小写，但不靠调用方保证）。"""
    return tuple((name.lower(), value) for name, value in pairs)


def _rule_findings(rule: HeaderRule, seen: set[str]) -> list[str]:
    findings: list[str] = []
    if not rule.note.strip():
        findings.append(f"理由为空:{rule.name}")
    if rule.name in seen:
        findings.append(f"重复分类:{rule.name}")
    seen.add(rule.name)
    if rule.verdict not in (JUDGED, EXEMPT, ABSENT):
        findings.append(f"未知判定:{rule.name}={rule.verdict}")
    if rule.verdict == EXEMPT and rule.name not in _EXEMPT_SHAPES:
        findings.append(f"豁免头缺少机械值形态:{rule.name}")
    if rule.verdict == ABSENT and rule.name in _EXEMPT_SHAPES:
        findings.append(f"不发射的登记不该有值形态:{rule.name}")
    return findings


def _observed_findings(observed: Collection[str]) -> list[str]:
    findings: list[str] = []
    known = {rule.name for rule in HEADER_RULES}
    declared_absent = {rule.name for rule in HEADER_RULES if rule.verdict == ABSENT}
    findings.extend(f"未分类的响应头:{name}" for name in sorted(set(observed) - known))
    findings.extend(
        f"登记为不发射却观测到:{name}" for name in sorted(set(observed) & declared_absent)
    )
    return findings


def _stale_findings(observed: Collection[str]) -> list[str]:
    """登记陈旧：清单里的头本轮**一次都没观测到** ⇒ 判红（清单必须跟着现实走）。"""
    counts = set(observed)
    return [
        f"登记陈旧(本轮未观测到):{rule.name}"
        for rule in HEADER_RULES
        if rule.verdict != ABSENT and rule.name not in counts
    ]


def partition_findings(observed: Iterable[str]) -> list[str]:
    """分区自审：理由 / 重复 / 未知判定 / 未分类 / 不发射却出现 / 陈旧 / 受判面下界。"""
    observed_set = {name.lower() for name in observed}
    findings: list[str] = []
    seen: set[str] = set()
    for rule in HEADER_RULES:
        findings.extend(_rule_findings(rule, seen))
    findings.extend(_observed_findings(observed_set))
    findings.extend(_stale_findings(observed_set))
    judged = [rule.name for rule in HEADER_RULES if rule.verdict == JUDGED]
    if len(judged) < MIN_JUDGED:
        findings.append(f"受判面低于下界:{len(judged)} < {MIN_JUDGED}")
    return findings


def judged_observation_findings(counts: Mapping[str, int]) -> list[str]:
    """受判头**非空取证**（承 MEM-156）：每个受判头本轮必须被真的观测到。"""
    return [
        f"受判头本轮未被观测到(受判面为空):{name}"
        for name in judged_names()
        if counts.get(name, 0) <= 0
    ]


def scan_headers(
    pairs: Iterable[tuple[str, str]], canaries: tuple[Canary, ...] = CANARIES
) -> list[str]:
    """头值扫描（纯函数）：**任何**头的值命中金丝雀都判红，点名头名与 kind。"""
    findings: list[str] = []
    for name, value in normalized(pairs):
        kinds = hits(value, canaries)
        if kinds:
            findings.append(f"响应头出现金丝雀:{name} 命中 {kinds}")
    return findings


def scan_route_headers(
    route: str, pairs: Iterable[tuple[str, str]], canaries: tuple[Canary, ...] = CANARIES
) -> list[str]:
    """带路由名的头值扫描：失败消息点名**路由 + 头名 + 字段（kind）**。"""
    return [f"{route} 的{found}" for found in scan_headers(pairs, canaries)]


def exempt_shape_findings(pairs: Iterable[tuple[str, str]]) -> list[str]:
    """豁免头的机械值形态：观测到的每个豁免头都必须满足它的形态断言。"""
    findings: list[str] = []
    for name, value in normalized(pairs):
        shape = _EXEMPT_SHAPES.get(name)
        if shape is not None and not shape(value):
            findings.append(f"豁免头的值形态不符:{name}={value!r}")
    return findings
