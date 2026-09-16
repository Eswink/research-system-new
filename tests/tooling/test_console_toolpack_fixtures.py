"""Console live e2e 的 ToolPack manifest fixture（PLAN-20260915-065 / EC-02）。

live 套件（`apps/web/tests/e2e/live-tool-pack-write.spec.ts`）要向真实控制面提交
**内容自洽**的 manifest：digest 必须等于控制面重算值，capability 必须落在平台词表里。
fixture 因此由域代码生成（`manifest_document`），本测试守住两件事：

1. 仓库里的 JSON == 域代码现算的文档（规则漂移 → 这里红，而不是 live 用例 422）；
2. fixture 用到的 capability 都在 `examples/config/capabilities.yaml` 里
   （否则 live install 会被 422 拒绝，而失败点离原因很远）。

重新生成（仓库根）：

    UPDATE_TOOLPACK_FIXTURES=1 uv run --frozen --no-sync python -m pytest \
        tests/tooling/test_console_toolpack_fixtures.py
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from packages.domain.core import Digest, Version
from packages.domain.tools import (
    ToolPackManifest,
    manifest_document,
    manifest_from_document,
    toolpack_content_digest,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "apps" / "web" / "tests" / "e2e" / "fixtures" / "toolpack-live-manifests.json"
VOCABULARY = ROOT / "examples" / "config" / "capabilities.yaml"

PACK_ID = "live_console_pack"
# 扩张项必须是**新增** capability，否则提交更新不构成权限扩张（不会转待批准）。
BASE_CAPABILITIES = ("dataset.read",)
EXPANDED_CAPABILITIES = ("dataset.read", "audit.write")


def _manifest(version: str, capabilities: tuple[str, ...]) -> ToolPackManifest:
    placeholder = ToolPackManifest(
        id=PACK_ID,
        version=Version(version),
        source="fixture://live-console",
        resolved_revision=f"rev-console-{version}",
        digest=Digest.of_bytes(b"placeholder"),
        license="MIT",
        requested_capabilities=list(capabilities),
    )
    return replace(placeholder, digest=toolpack_content_digest(placeholder))


def generated_documents() -> dict[str, dict[str, object]]:
    """base（v1.0.0）与 expanded（v1.1.0，新增 audit.write）。"""
    return {
        "base": manifest_document(_manifest("1.0.0", BASE_CAPABILITIES)),
        "expanded": manifest_document(_manifest("1.1.0", EXPANDED_CAPABILITIES)),
    }


def _vocabulary() -> set[str]:
    payload: Any = yaml.safe_load(VOCABULARY.read_text(encoding="utf-8"))
    return {str(item) for item in payload["capabilities"]}


def test_console_toolpack_fixture_matches_domain_documents() -> None:
    generated = generated_documents()
    if os.environ.get("UPDATE_TOOLPACK_FIXTURES") == "1":
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(generated, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        FIXTURE.write_text(text, encoding="utf-8")
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert committed == generated, (
        f"{FIXTURE.relative_to(ROOT)} 与域代码现算的 manifest 文档不一致；"
        "用 UPDATE_TOOLPACK_FIXTURES=1 重新生成。"
    )


def test_console_toolpack_fixture_roundtrips_and_uses_platform_vocabulary() -> None:
    vocabulary = _vocabulary()
    for name, document in generated_documents().items():
        manifest = manifest_from_document(document)
        assert manifest.verify_content_digest(), f"{name}: digest 与内容不自洽"
        unknown = set(manifest.requested_capabilities) - vocabulary
        assert not unknown, f"{name}: capability 不在平台词表里: {sorted(unknown)}"
