"""M12 NCBI E-utilities 真实网络冒烟（requires_live_llm 手动运行）。

验证真实 production path：EnvCredentialResolver(NCBI_API_KEY) → NcbiEutilsProvider
→ eutils.ncbi.nlm.nih.gov 真实 esearch。不输出任何 secret 内容。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.fakes import FakeArtifactStore
from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.research_tools import NcbiEutilsProvider
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import EffectClass, ProviderType, TrustLevel
from packages.domain.tools import ToolCallRecord, ToolProviderSpec

PROVIDER = ToolProviderSpec(
    id="ncbi_eutils",
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["literature.search", "literature.read", "citation.inspect"],
    effect_class=EffectClass.READ_ONLY,
)

QUERY = "text classification embeddings"


def main() -> int:
    store = FakeArtifactStore()
    resolver = EnvCredentialResolver()
    provider = NcbiEutilsProvider(store, credentials=resolver, spill_threshold_bytes=1)
    args = {"query": QUERY, "retmax": 5}
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    call = ToolCallRecord(
        task_id="smoke-task-1",
        attempt=1,
        operation_key="op-search-1",
        tool_id="literature_search",
        capability="literature.search",
        argument_digest=Digest.of_bytes(raw),
    )
    store.put(
        Artifact(
            id=f"tool-args:{call.task_id}:{call.operation_key}",
            digest=Digest.of_bytes(raw),
            size_bytes=len(raw),
            media_type="application/json",
        ),
        raw,
    )
    result = provider.execute(PROVIDER, call)
    print("status:", result.status.value)
    print("failure_category:", result.failure_category)
    assert result.status.value == "SUCCEEDED", result
    artifact = next(
        item
        for item in store.list_refs()
        if item.id == f"tool-result:{call.task_id}:{call.operation_key}:literature_search"
    )
    content = store.get(artifact.id)
    payload = json.loads(content.decode("utf-8"))
    print("count:", payload["count"])
    print("ids:", payload["ids"][:5])
    assert int(payload["count"]) >= 1, "expected at least one hit"
    print("SMOKE OK")
    provider.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())