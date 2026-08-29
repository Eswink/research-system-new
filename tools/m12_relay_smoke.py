"""M12 真实 Model Relay 冒烟（requires_live_llm 语义，显式手动运行）。

验证正式 production path：
EnvCredentialResolver(llm_main_key) → OpenAIChatGateway →
  list_models / probe_connectivity / probe_endpoint（basic chat）→
  run_probe（能力探测）→ build_fingerprint → usage 归账。

凭据纪律：key 只从环境变量 `llm_main_key` 解析（SecretValue 密封，
repr 脱敏）；本脚本不接收/不回显任何 secret；结果只输出
digest/status/model 名（AGENTS.md §4 漂移可见性字段）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.contracts.models_loaders import load_llm_endpoints, load_models
from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.gateway import OpenAIChatGateway
from packages.application.model_relay.fingerprint import (
    build_fingerprint,
    endpoint_config_digest,
    probe_suite_digest,
)
from packages.application.model_relay.probe import ProbeOptions, run_probe
from packages.application.model_relay.suite import default_probe_suite


def main() -> int:
    gateway = OpenAIChatGateway(default_timeout_seconds=120)
    credentials = EnvCredentialResolver()
    try:
        endpoints = load_llm_endpoints("examples/config/llm_endpoints.yaml")
        models = load_models("examples/config/models.yaml")
    except Exception as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    endpoint = endpoints["main"]
    model = models["research_alpha"]
    print(f"endpoint: {endpoint.id} base_url={endpoint.base_url}")
    print(f"model: {model.id} model_name={model.model_name}")

    # 1. 凭据可解析（不打印值）
    try:
        credentials.resolve(endpoint.credential_ref)
        print("credential: resolved (redacted)")
    except Exception as exc:
        print(f"CREDENTIAL ERROR: {exc}")
        return 3

    # 2. run_probe（connectivity gate → basic chat → 能力探测）
    suite = default_probe_suite()
    result, assertions = run_probe(
        gateway=gateway,
        credential_resolver=credentials,
        endpoint=endpoint,
        model=model,
        options=ProbeOptions(suite=suite),
    )
    print(f"probe ok={result.ok} error_category={result.error_category}")
    if not result.ok:
        print(f"probe error (redacted): {result.error_message}")
        gateway.close()
        return 4
    print(f"returned_model_name={result.returned_model_name}")
    print(f"system_fingerprint={result.system_fingerprint}")
    print(
        "observed_capabilities="
        + ",".join(sorted(item.value for item in result.observed_capabilities))
    )
    print(
        "capability_failures="
        + ",".join(
            f"{item.capability.value}:{item.error_category.value}"
            for item in result.capability_failures
        )
    )

    # 3. fingerprint（AGENTS.md §4 漂移可见性）
    from packages.domain.models import EndpointProbeSnapshot

    snapshot = EndpointProbeSnapshot(
        ok=True,
        returned_model_name=result.returned_model_name,
        system_fingerprint=result.system_fingerprint,
        safe_response_metadata={},
    )
    fingerprint = build_fingerprint(
        endpoint=endpoint,
        requested_model_id=model.model_name,
        snapshot=snapshot,
        suite_spec=suite,
        observed_capabilities=frozenset(result.observed_capabilities),
    )
    print(f"endpoint_config_digest={endpoint_config_digest(endpoint)}")
    print(f"probe_suite_digest={probe_suite_digest(suite)}")
    print(
        json.dumps(
            {
                "requested_model_id": fingerprint.requested_model_id,
                "returned_model_identifier": fingerprint.returned_model_identifier,
                "system_fingerprint": fingerprint.system_fingerprint,
                "probe_suite_digest": str(fingerprint.probe_suite_digest),
                "endpoint_config_digest": str(fingerprint.endpoint_config_digest),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    gateway.close()
    print("RELAY SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
