"""GOAL-025 EC-01 判据：读面**响应头**进扫描面（收 GOAL-024 的残余 `G24-2`）。

**受判命题**：沿默认离线链注入合成内容金丝雀后，读面响应**只**在契约声明返回内容的路由的
**响应体**里能看到它；**任何响应头**都**零命中**。

判据形态（承 MEM-158 / MEM-156 / MEM-159）：

- 头部清单是**分区**（`read_face_header_inventory.HEADER_RULES`，逐条显式、理由非空、
  三种判定无第四种）；**运行期观测到的未分类头**、**登记为不发射却出现的头**、
  **登记陈旧（本轮一次都没观测到）**三条都判红；
- **非空取证**：每个受判头必须在本轮**真的被观测到**（逐条计数非空），且实取响应路由数 ≥ 下界；
- **两向反证**：把金丝雀塞进受判头 ⇒ 判红并点名**路由 + 头名 + 字段**；内容放进 **canonical**
  （正文）⇒ **不**判红（该红时红、不该红时不红）；
- **正控制**：证明受判头是**活的**且是**标识符**回显面（`Content-Disposition.filename` 真的
  回显 `artifact.id`、`ETag` 真的回显 `artifact.digest`）—— 否则「零命中」可能是「头根本不在发」。

**边界（写清，否则判据会自伤）**：受判命题是**内容**不回头；**标识符**回显是契约行为
（id 在 `/artifacts/{artifact_id}` 元数据面上按契约可见）⇒ 夹具自己的 id **不得**携带金丝雀
token（本文件末有专门断言钉住）。
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping

import pytest
from starlette.responses import Response

from tests.observability.content_canary_support import ARTIFACT_BODY, CANARIES, PROMPT_TEXT
from tests.observability.read_face_canary_support import (
    ARTIFACT_ID,
    ARTIFACT_PARTNER_ID,
    ReadFace,
    fill_path,
    open_read_face,
    read_routes,
    response_text,
    scan,
)
from tests.observability.read_face_header_inventory import (
    MIN_EXERCISED,
    all_names,
    exempt_shape_findings,
    judged_names,
    judged_observation_findings,
    partition_findings,
    scan_route_headers,
)

#: 本轮登记为「取不到」的路由（缺对象 id）⇒ 实取集合必须恰好是读面减去这三条。
#: 与 GOAL-024 读面判据的登记同源（`UNEXERCISED_ZERO_HIT` + `UNEXERCISED_DECLARED`）。
UNEXERCISED: tuple[str, ...] = (
    "/workspace-snapshots/{digest}/files",
    "/workspace-snapshots/{left}/diff/{right}",
    "/library/{resource_id}",
)

#: 受判头「活的」证据必须在场的路由（制品正文通道）。
CONTENT_ROUTE = "/artifacts/{artifact_id}/content"


@pytest.fixture(scope="module")
def face() -> Iterator[ReadFace]:
    with open_read_face() as opened:
        yield opened


@pytest.fixture(scope="module")
def observed(face: ReadFace) -> Mapping[str, tuple[tuple[str, str], ...]]:
    """逐路由实取**响应头**（不筛状态码：错误响应同样受扫）。"""
    collected: dict[str, tuple[tuple[str, str], ...]] = {}
    for path in read_routes(face.app):
        filled = fill_path(path, face.ids)
        if filled is None:
            continue
        response = face.client.get(filled)
        collected[path] = tuple((name.lower(), value) for name, value in response.headers.items())
    return collected


def _observed_names(observed: Mapping[str, tuple[tuple[str, str], ...]]) -> tuple[str, ...]:
    return tuple(sorted({name for pairs in observed.values() for name, _ in pairs}))


def _observed_counts(observed: Mapping[str, tuple[tuple[str, str], ...]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for pairs in observed.values():
        for name in {item[0] for item in pairs}:
            counts[name] += 1
    return dict(counts)


def test_header_inventory_is_a_partition_of_the_observed_headers(
    observed: Mapping[str, tuple[tuple[str, str], ...]],
) -> None:
    """分区自审：未分类 / 重复 / 空理由 / 未知判定 / 不发射却出现 / 陈旧 / 下界。"""
    findings = partition_findings(_observed_names(observed))
    assert not findings, f"响应头清单不是分区:{findings}"


def test_the_read_face_headers_were_really_exercised(
    observed: Mapping[str, tuple[tuple[str, str], ...]],
) -> None:
    """非空取证（承 MEM-156）：实取路由数达下界，且每个受判头真的被观测到。"""
    assert len(observed) >= MIN_EXERCISED, (
        f"实取到响应的读面路由只有 {len(observed)} 条 < 下界 {MIN_EXERCISED} ⇒ 空转绿"
    )
    counts = _observed_counts(observed)
    findings = judged_observation_findings(counts)
    assert not findings, (
        f"受判头取证失败:{findings}（受判面 = {judged_names()}；逐条观测计数 {counts}）"
    )


def test_unexercised_routes_are_exactly_the_registered_ones(face: ReadFace) -> None:
    """取不到的路由集合与登记一致（新增一条取不到的路由必须显式登记）。"""
    unfilled = tuple(path for path in read_routes(face.app) if fill_path(path, face.ids) is None)
    assert sorted(unfilled) == sorted(UNEXERCISED), (
        f"取不到的路由与登记不一致:{sorted(unfilled)} / {sorted(UNEXERCISED)}"
    )


def test_no_canary_in_any_response_header(
    observed: Mapping[str, tuple[tuple[str, str], ...]],
) -> None:
    """零命中：**任何**响应头的值都不许出现金丝雀；失败消息点名路由 + 头名 + 字段。"""
    violations: list[str] = []
    for path, pairs in sorted(observed.items()):
        violations.extend(scan_route_headers(path, pairs))
    assert not violations, f"读面响应头出现内容金丝雀:{violations}"


def test_exempt_headers_keep_their_mechanical_value_shape(
    observed: Mapping[str, tuple[tuple[str, str], ...]],
) -> None:
    """豁免不是散文：每个被观测到的豁免头都必须满足它的机械值形态。"""
    violations: list[str] = []
    for path, pairs in sorted(observed.items()):
        violations.extend(f"{path}: {item}" for item in exempt_shape_findings(pairs))
    assert not violations, f"豁免头的值形态断言失败:{violations}"


def test_judged_headers_are_live_and_identifier_derived(
    face: ReadFace, observed: Mapping[str, tuple[tuple[str, str], ...]]
) -> None:
    """正控制：受判头是**活的**，且回显的是**标识符**（不是内容）。"""
    pairs = dict(observed[CONTENT_ROUTE])
    meta = face.deps.artifacts.meta(ARTIFACT_ID)
    sanitized = "".join(char if char.isalnum() or char in "._-" else "_" for char in ARTIFACT_ID)[
        -120:
    ]
    disposition, _, filename = pairs.get("content-disposition", "").partition("; ")
    # 处置词由制品 media_type 决定（可内联媒体 ⇒ `inline`，否则 `attachment`）⇒ 只钉住两者之一。
    assert disposition in {"inline", "attachment"}, (
        f"Content-Disposition 的处置词不在契约集合内:{disposition!r}"
    )
    assert filename == f'filename="{sanitized}"', (
        f"Content-Disposition 没有回显 artifact.id:{pairs.get('content-disposition')!r}"
    )
    assert pairs.get("etag") == f'"{meta.digest}"', (
        f"ETag 没有回显 artifact.digest:{pairs.get('etag')!r}"
    )


def test_canonical_content_in_bodies_does_not_redden_the_header_face(
    face: ReadFace, observed: Mapping[str, tuple[tuple[str, str], ...]]
) -> None:
    """两向反证（不该红时不红）：内容在 **canonical / 声明载体的正文**里 ⇒ 头面仍零命中。"""
    bodies = "".join(
        response_text(face.client.get(filled))
        for path in sorted(observed)
        if (filled := fill_path(path, face.ids)) is not None
    )
    assert {"prompt", "artifactbody"} <= set(scan(bodies)), (
        "本轮正文里没有金丝雀 ⇒ 头面零命中会是空真"
    )
    violations: list[str] = []
    for path, pairs in sorted(observed.items()):
        violations.extend(scan_route_headers(path, pairs))
    assert not violations, f"正文有金丝雀并不该让头面判红:{violations}"


def test_a_canary_in_a_judged_header_is_red() -> None:
    """反证（纯函数）：受判头带金丝雀 ⇒ 判红并点名头名与字段。"""
    findings = scan_route_headers("/x", [("ETag", f'"{PROMPT_TEXT.value}"')])
    assert findings and "/x" in findings[0] and "etag" in findings[0], findings
    assert "prompt" in findings[0], findings


def test_a_stale_header_registration_is_red() -> None:
    """反证（纯函数）：清单里的头本轮一次都没观测到 ⇒ 判红（清单必须跟着现实走）。"""
    without_content_type = tuple(name for name in all_names() if name != "content-type")
    findings = partition_findings(without_content_type)
    assert any("登记陈旧(本轮未观测到):content-type" in item for item in findings), findings


def test_a_canary_in_a_judged_header_on_the_real_app_is_red(face: ReadFace) -> None:
    """按压（真实应用 + 真实响应）：受判头带金丝雀 ⇒ 判红点名路由 + 头名 + 字段。"""

    async def press_probe() -> Response:
        return Response("ok", headers={"ETag": f'"{ARTIFACT_BODY.value}"'})

    face.app.get("/__header-canary-press-probe")(press_probe)
    response = face.client.get("/__header-canary-press-probe")
    findings = scan_route_headers("/__header-canary-press-probe", response.headers.items())
    assert findings, "受判头带金丝雀没有被抓到"
    joined = " ".join(findings)
    assert "etag" in joined and "artifactbody" in joined, findings
    assert "/__header-canary-press-probe" in joined, findings


def test_an_unclassified_observed_header_is_red() -> None:
    """反证：出现一个没登记的头 ⇒ 判红并点名（新头不能静默逃逸）。"""
    findings = partition_findings([*all_names(), "x-echo-prompt"])
    assert any("未分类的响应头:x-echo-prompt" in item for item in findings), findings


def test_an_absent_header_that_appears_is_red(face: ReadFace) -> None:
    """反证（真实应用）：登记为**不发射**的头一旦被观测到 ⇒ 判红并点名。"""

    async def press_probe() -> Response:
        return Response("ok", headers={"Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT"})

    face.app.get("/__absent-header-press-probe")(press_probe)
    response = face.client.get("/__absent-header-press-probe")
    names = [name.lower() for name in response.headers]
    findings = partition_findings([*all_names(), *names])
    assert any("登记为不发射却观测到:last-modified" in item for item in findings), findings


def test_identifier_boundary_is_not_carried_by_the_fixture(face: ReadFace) -> None:
    """边界钉住：夹具自己的**标识符**不得携带金丝雀 token（否则头面判据会自伤）。

    受判命题是「**内容**不回头」；`Content-Disposition.filename` 回显 `artifact.id` 是契约行为。
    若将来有人把金丝雀塞进 id，本断言先判红 ⇒ 提示必须重新决定这条边界，而不是让头面判据
    悄悄变成「标识符不许出现」。
    """
    identifiers = {
        "artifact_id": ARTIFACT_ID,
        "artifact_partner_id": ARTIFACT_PARTNER_ID,
        **face.ids,
    }
    offenders = [key for key, value in identifiers.items() if scan(str(value), CANARIES)]
    assert not offenders, f"夹具标识符携带了金丝雀 token ⇒ 头面判据会自伤:{offenders}"
