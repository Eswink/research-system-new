"""真实 runtime 跑一次 run 的共享装配（EC-03 离线全链 / EC-04 live 首次真实 run 共用）。

抽出来的**原因**（不是偏好整洁）：同一个测试模块被**两个模块名**导入时，SDK 的
`Action` 子类会被定义两次，判别联合随即拒绝后续任何事件 round-trip
（`Duplicate class definition for openhands.sdk.tool.schema.Action`）——
本模块只被 `tests.e2e.*` 这一个名字导入，`Action` 子类因此只定义一次。

本模块**不含** mock 端点与 fixture（那些是 EC-03 离线链的私有件）。

凭据纪律：`live_key` 的值由**调用方**从环境变量读出后传入，本模块只把它注册进
进程内解析器；不落盘、不回显、不写日志。
"""

from __future__ import annotations

from typing import Any, cast

from openhands.sdk.tool.schema import Action, Observation
from openhands.sdk.tool.tool import ToolDefinition, ToolExecutor

_PROTOCOL = "console_demo_research_v1.yaml"
#: GOAL-010 EC-03：真实执行体应当跑的**真实协议**（语义对真实执行体成立；
#: 头部不再自称「受控 Fake…不冒充真实研究执行」）。它的 id 必须出现在 run 的
#: canonical 事实里——判据见 `tests/e2e/test_real_protocol_canonical_live.py`。
REAL_PROTOCOL = "real_research_task_v1.yaml"
#: Live 运行注册进凭据解析器的引用名（= 目录里 endpoint 声明的 `credential_ref`）。
LIVE_CREDENTIAL_REF = "LLM_MAIN_KEY"
#: GOAL-011 EC-03：`sort_analysis_v1` 执行阶段的合约（沙箱实验声明落在它上面）。
EXPERIMENT_CONTRACT = "sort_analysis_execution"
#: 沙箱实验脚本（仓库相对路径）与**既有**沙箱镜像（M9 已 E2E 验证的那一个）。
EXPERIMENT_SCRIPT = "examples/experiments/sort_analysis_baseline.py"
EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"


class InertAction(Action):
    """惰性工具的动作（无副作用）；模块级定义的原因见 `inert_tool_class()`。"""

    note: str = ""


class InertExecutor(ToolExecutor[Any, Observation]):
    def __call__(self, action: Any, conversation: Any = None) -> Observation:
        return Observation.from_text("inert")


class InertTool(ToolDefinition[Any, Observation]):
    """测试侧惰性工具：只为让冻结集里的 provider id 在 SDK 注册表里可解析。"""

    @classmethod
    def create(cls, conv_state: Any = None, **params: Any) -> list[Any]:
        return [
            cls(
                description="Inert test tool",
                action_type=InertAction,
                observation_type=None,
                executor=InertExecutor(),
            )
        ]


def inert_tool_class() -> Any:
    """惰性 SDK 工具（无副作用）：只为让 provider id 在 SDK 注册表里可解析。

    类定义在**模块级**：SDK 会枚举 `Action` 的全部具体子类来构建判别联合，遇到
    `<locals>` 限定名直接抛 "Local classes not supported!" ⇒ 函数内局部类会**毒化
    同进程后续任何事件 round-trip**（fork 路径就会走它）。同族的第二种毒化是
    **同一文件被两个模块名导入**（`test_x` 与 `tests.e2e.test_x`）：类被定义两次，
    报 "Duplicate class definition" —— 本模块的存在就是为了让共享装配只有一个名字。
    """
    return InertTool


def inert_tool_class_for(registry_name: str) -> Any:
    """按**注册名**给一个**独有类名**的惰性工具类（`name` 由类名派生，见下）。

    为什么必须按名分：一个会话的冻结集里可以有多件 provider（`sort_analysis_v1` 的 review
    阶段有两件：`openhands_workspace` + `m12_artifact`），而 SDK 的 `ToolDefinition.name`
    是**类名派生的常量**（`InertTool` ⇒ `inert`）——两件同名会在 agent 初始化时直接抛
    `Duplicate tool names found: {'inert'}`。这是**本惰性替身自己的命名问题**，不是产品缺陷：
    真实的 provider→SDK 映射由 EC-05 承担。

    类只造一次并放进模块全局（`type()` + 显式 `__qualname__`/`__module__`）：SDK 会枚举
    `Action` 的具体子类来构建判别联合，`<locals>` 限定名会毒化同进程后续事件 round-trip
    （见 `inert_tool_class()`）；重复造类则触发 "Duplicate class definition"。
    """
    class_name = "Inert" + "".join(part.title() for part in registry_name.split("_")) + "Tool"
    existing = globals().get(class_name)
    if existing is not None:
        return existing
    created = type(class_name, (InertTool,), {"__module__": __name__, "__qualname__": class_name})
    globals()[class_name] = created
    return created


def register_inert_tools(frozen: tuple[str, ...]) -> None:
    """把冻结 Tool Set 按名注册为惰性工具（测试侧替代 EC-05 的 provider→SDK 映射）。"""
    from openhands.sdk.tool.registry import register_tool

    for name in frozen:
        register_tool(name, inert_tool_class_for(name))


def point_catalog_at(deps: Any, base_url: str) -> None:
    """把目录里所有 endpoint 的 base_url 指向 `base_url`（其余字段不动）。"""
    from dataclasses import replace

    context = deps.preflight_override
    assert context is not None
    endpoints = {
        key: replace(endpoint, base_url=base_url)
        for key, endpoint in context.catalog.endpoints.items()
    }
    deps.preflight_override = replace(
        context, catalog=replace(context.catalog, endpoints=endpoints)
    )


def declare_sandbox_experiment(deps: Any, *, script: str, image: str) -> None:
    """GOAL-011 EC-03：在**本次 run 的目录**上给执行阶段合约加「沙箱实验」声明。

    为什么在装配面声明、而不写进协议文件或目录文件：`sort_analysis_v1` 是 M7 参考场景，
    它的执行阶段被 10+ 条已判绿用例按**会话**语义驱动 ⇒ 改协议/改共享目录会让那批语义
    消失。这里走的是与 GOAL-009/010/011 全部真实 run 同一条路径——**测试/运维显式声明的
    执行上下文**（`preflight_override` 就是这条路径的既有载体），协议与共享夹具零改动。
    """
    from dataclasses import replace

    from packages.domain.tasks import ExperimentExecutionSpec

    context = deps.preflight_override
    assert context is not None
    contracts = dict(context.catalog.task_contracts)
    contracts[EXPERIMENT_CONTRACT] = replace(
        contracts[EXPERIMENT_CONTRACT],
        experiment=ExperimentExecutionSpec(script=script, image=image),
    )
    deps.preflight_override = replace(
        context, catalog=replace(context.catalog, task_contracts=contracts)
    )


def with_sandbox_experiment(
    deps: Any, *, script: str, image: str, runtime: Any | None = None
) -> None:
    """把**既有**实验执行链接进运行编排的实验缝（同一个装配，同 run-chain 能力步的形态）。

    `runtime` 缺省 `None` ⇒ 沿用装配里既有的执行体（真实 adapter 路径）；离线判据需要
    **会话侧交付物**时显式传入（受控执行体必须**自己声明**它交付了什么——冻结后的
    `register_session_result` 对空交付物如实拒绝，本函数不替它伪造）。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from services.api.experiment_support import (
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    declare_sandbox_experiment(deps, script=script, image=image)
    policy_evaluator = policy_bindings().get("policy_evaluator")
    assert policy_evaluator is not None, "policy.yaml must be loadable for the sandbox experiment"
    runner = sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            policy=policy_evaluator,
            script=script,
            image=image,
            experiment_store=deps.experiment_store,
        )
    )
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(
        replace(
            old._deps,
            runtime=runtime if runtime is not None else old._deps.runtime,
            experiment_task=runner,
        )
    )


def register_live_key(deps: Any, live_key: str | None) -> None:
    """把环境变量里的凭据**值**注册进解析器；本模块不写任何可用凭据字面量。"""
    if live_key is None:
        return
    from adapters.fakes.credential_resolver import FakeCredentialResolver

    # `ApiDeps.credentials` 声明为 Port；run_fixtures 注入的是 Fake 实现。
    cast(FakeCredentialResolver, deps.credentials).register(LIVE_CREDENTIAL_REF, live_key)


def host_shell_workspace(lease: Any, session_id: str) -> Any:
    """测试侧 workspace 构造：**显式**打开 host shell（生产的默认 deny 不放松）。"""
    from adapters.openhands.workspace_adapter import build_local_workspace

    return build_local_workspace(lease, session_id, allow_host_shell=True)


def real_runtime(deps: Any, settings: Any, policy: Any, *, map_tools: bool) -> Any:
    """测试装配的真实 adapter；`map_tools=False` 改走**生产装配**以测量缺映射行为。"""
    from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
    from adapters.openhands.session_types import AdapterDependencies
    from services.api.assembly import policy_bindings
    from services.api.runtime_support import build_agent_runtime, session_llm_factory

    policy_evaluator = policy_bindings().get("policy_evaluator")
    assert policy_evaluator is not None, "policy.yaml must be loadable for the real runtime"
    if not map_tools:
        # 生产装配的 register_tools 缺省为空操作——保留原样以**如实测量**缺映射时的行为。
        runtime = build_agent_runtime(
            settings,
            credentials=deps.credentials,
            policy_evaluator=policy_evaluator,
            budget_ledger=deps.budget,
        )
        assert isinstance(runtime, OpenHandsRuntimeAdapter)
        return runtime
    return OpenHandsRuntimeAdapter(
        AdapterDependencies(
            credential_resolver=deps.credentials,
            policy_evaluator=policy_evaluator,
            build_llm=session_llm_factory(deps.credentials, policy),
            build_workspace=host_shell_workspace,
            register_tools=register_inert_tools,  # 测试侧补上 EC-05 的映射
            budget_ledger=deps.budget,
        )
    )


def openhands_deps(
    base_url: str,
    *,
    map_tools: bool,
    allow_localhost: bool = True,
    live_key: str | None = None,
) -> Any:
    """run-ready 装配 + 真实 adapter + 指向 `base_url` 的目录。

    `live_key` 非空时把它注册进凭据解析器——**值只从环境变量来**（调用方读
    `RESEARCHOS_LIVE_E2E_KEY` 或目录声明的 `credential_ref`）。
    运行链能力步另经 `with_run_chain_capabilities` 接（同一个装配，见那里）。
    """
    from dataclasses import replace

    from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.runtime_support import OPENHANDS_RUNTIME, resolve_runtime_selection
    from services.api.settings import ApiSettings
    from tests.api.run_fixtures import make_run_ready_deps

    deps = make_run_ready_deps()
    point_catalog_at(deps, base_url)
    register_live_key(deps, live_key)
    settings = ApiSettings(
        agent_runtime=OPENHANDS_RUNTIME,
        allow_localhost_endpoints=allow_localhost,
        workspace_allow_host_shell=True,
    )
    policy = EndpointUrlPolicy(allow_localhost=allow_localhost)
    runtime = real_runtime(deps, settings, policy, map_tools=map_tools)
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(replace(old._deps, runtime=runtime))
    deps.runtime_selection = resolve_runtime_selection(settings)
    deps.endpoint_url_policy = policy
    return deps


def start_run(client: Any, protocol: str = _PROTOCOL) -> dict[str, Any]:
    """经既有 API 启动一次 run（幂等键每次新生成）。

    `protocol` 缺省仍是 demo 协议：EC-01/EC-02 的判据当初就是在它上面取样的，
    这里**照原样**保留以便它们可复跑、不追溯改写既有证据。GOAL-010 EC-03 的判据
    显式传 `REAL_PROTOCOL`，让「这一次真实 run 用的是哪份协议」在**调用点**可读。
    """
    import uuid

    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": protocol},
        headers={"Idempotency-Key": f"ec03-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def declare_second_artifact(deps: Any, contract_id: str, extra: str) -> None:
    """测试侧反证预置：把 `contract_id` 改成声明**两个** artifact 名。

    用于 GOAL-010 EC-01 的**反证分支**——合约声明不再唯一时，adapter 必须**不猜**
    （回落事实名），验收门随之判拒。只动 `preflight_override` 的目录快照，
    与 `point_catalog_at` 同一手法；不写任何配置文件、不改产品代码路径。
    """
    from dataclasses import replace

    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion

    context = deps.preflight_override
    assert context is not None
    catalog = context.catalog
    contracts = dict(catalog.task_contracts)
    contract = contracts[contract_id]
    extra_criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact=extra
    )
    contracts[contract_id] = replace(
        contract, acceptance_criteria=[*contract.acceptance_criteria, extra_criterion]
    )
    deps.preflight_override = replace(context, catalog=replace(catalog, task_contracts=contracts))


def run_failures(client: Any, run_id: str) -> list[str]:
    """从 canonical 事件链读失败原因（`run.failed` / `task.failed` 的 message）。"""
    events = client.get(f"/runs/{run_id}/events").json()
    return [
        event["payload"].get("message", "")
        for event in events
        if event["type"] in ("run.failed", "task.failed")
    ]


#: GOAL-011 EC-01：运行链检索的两步（**声明式**：谁、哪个工具、参数从哪来）。
def _retrieval_calls() -> tuple[Any, ...]:
    """两步：检索（query 来自声明输入的 `retrieval.query`）→ 读取（ids 来自上一步结果）。

    第 2 步的标识**只可能**来自第 1 步的响应（`ids`），不内置任何厂商知识、也不从
    夹具凭空生成 ⇒ 证据链里的 PMID 是这次检索真实返回的那一串。
    """
    from packages.application.run_orchestration.phase_capabilities import RunChainCall

    return (
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_search",
            capability="literature.search",
            arguments_from_input=("retrieval.query",),
            fixed_arguments={"retmax": 3},
        ),
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_read",
            capability="literature.read",
            ids_from_previous="ids",
        ),
    )


#: 离线判据的检索响应（**夹具值**）：esearch 返回两个 id，efetch 回第一个。
MOCK_PMIDS: tuple[str, ...] = ("38000001", "38000002")
_MOCK_SEARCH_JSON = {"esearchresult": {"count": "2", "idlist": list(MOCK_PMIDS)}}
_MOCK_EFETCH_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?><PubmedArticleSet><PubmedArticle>'
    b"<MedlineCitation><PMID>38000001</PMID><Article>"
    b"<ArticleTitle>Frozen embeddings for low-resource classification</ArticleTitle>"
    b"<Journal><Title>J Test Res</Title></Journal></Article></MedlineCitation>"
    b"</PubmedArticle></PubmedArticleSet>"
)


def offline_ncbi_http(calls: list[str]) -> Any:
    """**离线** NCBI 传输（httpx.MockTransport）：测的是链，不是公网可达性。

    live 判据**不**用它（真出网，按 `requires_live_llm` 放行面）；传输层以外的一切
    都相同——同一个真实 adapter、同一条运行链。
    """
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path.rsplit("/", 1)[-1])
        if request.url.path.endswith("esearch.fcgi"):
            return httpx.Response(200, json=_MOCK_SEARCH_JSON)
        if request.url.path.endswith("efetch.fcgi"):
            return httpx.Response(200, content=_MOCK_EFETCH_XML)
        return httpx.Response(404, text="not found")

    return httpx.Client(transport=httpx.MockTransport(handler))


def run_chain_store_ledger(deps: Any) -> tuple[Any, Any]:
    """运行链要用的 artifact store 与 evidence ledger（= 该 run 装配持有的同一对实例）。"""
    inner = deps.runs._deps
    return inner.artifacts, inner.ledger


def ncbi_run_chain_provider(deps: Any, *, http_client: Any = None) -> Any:
    """运行链用的**真实** NCBI provider。

    离线判据传 `httpx.MockTransport` 的 client（不出网）；live 判据不传（真出网，
    按 `requires_live_llm` 放行面）。
    `spill_threshold_bytes=1`：运行链证据要求**内容寻址的内容在场**（
    `register_tool_evidence` 会重算 digest），而默认阈值 32KiB 会让小响应不落盘 ⇒
    证据准入 fail closed。
    """
    from adapters.research_tools import NcbiEutilsProvider

    store, _ledger = run_chain_store_ledger(deps)
    return NcbiEutilsProvider(
        store,
        credentials=deps.credentials,
        http_client=http_client,
        spill_threshold_bytes=1,
    )


def retrieval_capabilities(deps: Any, provider: Any) -> Any:
    """运行链检索能力步的装配（provider 由调用方给：离线 mock / live 真实）。

    目录里的 provider spec 用**既有那份**（examples/config/tool_providers.yaml 经
    run-ready 装配读入），不在测试里重写一份。
    """
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps
    from services.api.assembly import policy_bindings

    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers["ncbi_eutils"]
    store, ledger = run_chain_store_ledger(deps)
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "policy.yaml must be loadable for the run-chain policy check"
    return CapabilityDeps(
        calls=_retrieval_calls(),
        providers={spec.id: provider},
        provider_specs={spec.id: spec},
        policy=policy,
        artifacts=store,
        ledger=ledger,
    )


def with_run_chain_capabilities(deps: Any, provider: Any) -> None:
    """把运行链能力步接到**既有装配**上（provider 由调用方给：离线 mock / live 真实）。

    与 `openhands_deps` 换 runtime 同一手法：重建服务、复用同一批 store/ledger 实例。
    只对声明了 `capability_execution: run_chain` 的 phase 生效——其余协议行为不变。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService

    deps.runs = RunOrchestrationService(
        replace(
            deps.runs._deps,
            capabilities=retrieval_capabilities(deps, provider),
        )
    )
