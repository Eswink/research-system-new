"""anthropic 面口径的同源判据（GOAL-009 EC-02 / PLAN-20260920-122）。

**这个判据判的是「一次 run 到底消费哪一面」，判的是事实而不是文笔。**

背景（GOAL-009 cycle 1 的 F-10）：域里声明了 `protocol: ANTHROPIC` 的
`agnes-anthropic` 端点，但**一次 run 消费的模型并不是 `agnes_flash`**——协议的两个 phase 要
`domain_researcher` / `scientific_reviewer`，它们解析到的 agent 绑的是 `research_alpha` /
`reviewer_gamma`，两者都在 `main`（`OPENAI_COMPATIBLE`）上。`agnes_flash` **只**被 live 判据的
**probe 段**用到。于是口径是：

    run 腿  = `main`（OPENAI_COMPATIBLE）
    probe 腿 = `agnes-anthropic`（ANTHROPIC）

本判据把这个口径钉成**可判事实**：任何一次改绑都会让它变红，从而**逼着**改绑者先读
`docs/integration/LLM_ENDPOINTS.md` 的改绑小节（步骤 / 影响面 / 判据草案），
而不是把边界留在注释和口头约定里。

**判据红 ≠ 改绑是错的**：改绑是架构决策，撞门是**有意**的。红的正确处置是
「按文档改绑小节同步更新本判据」，**不是**绕开或放松本判据。
"""

from __future__ import annotations

import re
from pathlib import Path

from adapters.contracts.models_loaders import (
    load_llm_endpoints,
    load_models,
)
from adapters.contracts.protocol_loaders import load_protocol
from adapters.contracts.roles_loaders import load_agents

REPO_ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = "examples/protocols/console_demo_research_v1.yaml"
AGENTS = "examples/config/agents.yaml"
MODELS = "examples/config/models.yaml"
ENDPOINTS = "examples/config/llm_endpoints.yaml"

LIVE_TEST = REPO_ROOT / "tests/e2e/test_ec04_live_first_run.py"
ENDPOINTS_DOC = REPO_ROOT / "docs/integration/LLM_ENDPOINTS.md"

#: run 腿必须走的那一面；probe 腿必须走的那一面。
RUN_PROTOCOL = "OPENAI_COMPATIBLE"
PROBE_PROTOCOL = "ANTHROPIC"
ANTHROPIC_ENDPOINT = "agnes-anthropic"

#: 改绑小节必须出现在文档里（缺任一 ⇒ 红）：它承載「步骤 / 影响面 / 判据草案」三件。
REQUIRED_DOC_HEADINGS: tuple[str, ...] = (
    "## 12. run 腿与 probe 腿：现在走哪一面",
    "### 12.1 现在走哪一面",
    "### 12.2 改绑步骤",
    "### 12.3 影响面（实测）",
)

_PATH_ROOTS = ("adapters/", "apps/", "docs/", "examples/", "packages/", "services/", "tests/")
_BACKTICK = re.compile(r"`([^`]+)`")


def _run_leg_endpoint_protocols() -> dict[str, str]:
    """协议 phase 的 `required_roles` → agent → 模型 → 端点 → 协议（run 腿的真实链条）。"""
    protocol = load_protocol(PROTOCOL)
    roles = {pool.role for phase in protocol.phases for pool in phase.required_roles}
    agents = load_agents(AGENTS)
    models = load_models(MODELS)
    endpoints = load_llm_endpoints(ENDPOINTS)
    resolved: dict[str, str] = {}
    for agent in agents.values():
        if agent.role not in roles:
            continue
        model_id = agent.model_binding.value
        assert model_id is not None, f"agent {agent.id!r} has a binding with no model value"
        model = models.get(model_id)
        assert model is not None, f"agent {agent.id!r} binds unknown model {model_id!r}"
        endpoint = endpoints.get(model.endpoint_id)
        assert endpoint is not None, (
            f"model {model_id!r} binds unknown endpoint {model.endpoint_id!r}"
        )
        resolved[model_id] = endpoint.protocol
    return resolved


class TestWhichSurfaceTheRunConsumes:
    """run 腿：必须是 OpenAI 兼容面（改绑即红）。"""

    def test_protocol_roles_resolve_to_at_least_one_model(self) -> None:
        """反证判据自身的前提：解析链必须真的解析出模型，否则下面的断言是空转。"""
        resolved = _run_leg_endpoint_protocols()
        assert resolved, "no agent matched the protocol's required_roles — the chain is broken"

    def test_run_leg_models_all_sit_on_the_openai_compatible_face(self) -> None:
        resolved = _run_leg_endpoint_protocols()
        wrong = {m: p for m, p in resolved.items() if p != RUN_PROTOCOL}
        assert not wrong, (
            f"the run leg moved off {RUN_PROTOCOL}: {wrong}. If this is an intentional rebind, "
            "read docs/integration/LLM_ENDPOINTS.md §12.2-12.3 and update this judge with it."
        )

    def test_probe_leg_targets_the_anthropic_endpoint(self) -> None:
        """probe 腿：`agnes-anthropic` 必须是 ANTHROPIC 且启用。"""
        endpoints = load_llm_endpoints(ENDPOINTS)
        endpoint = endpoints[ANTHROPIC_ENDPOINT]
        assert endpoint.protocol == PROBE_PROTOCOL, endpoint.protocol
        assert endpoint.enabled is True, "the anthropic endpoint must stay enabled to be probeable"

    def test_live_judge_probes_that_same_endpoint(self) -> None:
        """live 判据的 probe 段引用**同一个**端点 id（否则口径与实际驱动面不一致）。"""
        source = LIVE_TEST.read_text(encoding="utf-8")
        match = re.search(r'^_ANTHROPIC_ENDPOINT\s*=\s*"([^"]+)"', source, re.MULTILINE)
        assert match is not None, "the live judge no longer declares _ANTHROPIC_ENDPOINT"
        assert match.group(1) == ANTHROPIC_ENDPOINT, match.group(1)


class TestTheBoundaryIsReadableAtTheReadFace:
    """边界**本来就可读**：模型说走哪个端点、端点说是什么协议。"""

    def test_endpoint_read_dto_exposes_protocol(self) -> None:
        text = (REPO_ROOT / "services/api/dto/endpoints.py").read_text(encoding="utf-8")
        assert "protocol: str" in text, "LlmEndpointReadDto must keep exposing protocol"

    def test_model_read_dto_exposes_endpoint_id(self) -> None:
        text = (REPO_ROOT / "services/api/dto/models.py").read_text(encoding="utf-8")
        assert "endpoint_id: str" in text, "ModelReadDto must keep exposing endpoint_id"


class TestTheRebindPathIsWrittenDown:
    """改绑小节必须存在，且它引用的仓库路径**真的存在**（同源，不判文笔）。"""

    def test_doc_exists(self) -> None:
        assert ENDPOINTS_DOC.exists(), ENDPOINTS_DOC

    def test_every_rebind_heading_is_present(self) -> None:
        text = ENDPOINTS_DOC.read_text(encoding="utf-8")
        missing = [h for h in REQUIRED_DOC_HEADINGS if h not in text]
        assert not missing, f"the rebind section is incomplete: {missing}"

    def test_every_cited_repo_path_exists(self) -> None:
        text = ENDPOINTS_DOC.read_text(encoding="utf-8")
        cited: set[str] = set()
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                continue
            cited.update(token.strip() for token in _BACKTICK.findall(line))
        missing = sorted(
            token
            for token in cited
            if token.startswith(_PATH_ROOTS)
            and " " not in token
            and not (REPO_ROOT / token.split("::", 1)[0]).exists()
        )
        assert not missing, f"the rebind section cites paths that do not exist: {missing}"

    def test_rebind_section_names_the_real_coupling_points(self) -> None:
        """影响面必须是**实测到的**耦合点，而不是「可能会有影响」这种空话。"""
        text = ENDPOINTS_DOC.read_text(encoding="utf-8")
        section = text.split(REQUIRED_DOC_HEADINGS[3], 1)[1]
        for coupling in (
            "tests/loaders/test_contract_loaders.py",
            "tests/e2e/test_ec03_real_runtime_offline_chain.py",
            "services/api/dto/endpoints.py",
        ):
            assert coupling in section, f"the impact list omits a real coupling point: {coupling}"
