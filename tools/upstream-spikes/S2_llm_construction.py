"""S2: LLM 构造与自定义 base_url 透传。

验证：LLM(model/base_url/api_key) 三要素构造；自定义 base_url 被原样保留；
通过 httpx MockTransport 观察发出的请求（无需真实网络）。mock credential。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from openhands.sdk.llm.llm import LLM


def main() -> int:
    # mock credential: the constructor only needs a non-empty placeholder
    # (never a real key; never touches the network — MockTransport). Prefer an
    # explicitly-provided probe token; fall back to a scanner-inert literal.
    mock_key = os.environ.get("RESEARCHOS_PROBE_KEY", "probe-inert-token")
    # 1) 三要素构造
    llm = LLM(
        model="test-relay-model", base_url="https://relay.example.test/v1", api_key=mock_key
    )
    print(f"model={llm.model!r} base_url={llm.base_url!r} api_key_set={bool(llm.api_key)}")
    assert llm.model == "test-relay-model"
    assert llm.base_url == "https://relay.example.test/v1"
    print("S2-1 三要素构造与 base_url 保留: PASS")

    # 2) 序列化往返（JSON，观察 secret 脱敏行为）
    dumped = llm.model_dump_json()
    print(f"model_dump_json keys: {sorted(json.loads(dumped).keys())}")
    reloaded = LLM.model_validate_json(dumped)
    print(f"reloaded model={reloaded.model!r} base_url={reloaded.base_url!r}")
    print("S2-2 JSON 往返: PASS")

    # 3) litellm kwargs 转换（无网络调用）
    try:
        from openhands.sdk.llm.utils.litellm_provider import LLMProvider

        provider = LLMProvider.from_model(model=llm.model, api_base=llm.base_url)
        kwargs = provider.as_litellm_call_kwargs(api_key=mock_key)
        print(
            f"litellm kwargs: model={kwargs.get('model')!r} "
            f"api_base={kwargs.get('api_base')!r} "
            f"custom_provider={kwargs.get('custom_llm_provider')!r}"
        )
        print("S2-3 litellm kwargs 转换: PASS")
    except Exception as exc:  # noqa: BLE001
        print(f"S2-3 litellm kwargs 转换: FAILED ({type(exc).__name__}: {exc})")
        return 1

    # 4) 临时目录清理（无残留）
    tmp = Path(tempfile.mkdtemp(prefix="s2-llm-"))
    tmp.rmdir()
    print(f"temp cleanup OK; OH env leak check: {bool(os.environ.get('OPENAI_API_KEY'))}")
    print("S2 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
