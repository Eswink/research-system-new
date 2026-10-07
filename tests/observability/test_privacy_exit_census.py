"""GOAL-024 EC-01:非 canonical 出口清单(显式分类,承 MEM-158)。

**为什么有这条判据**:M15 WP4 的 `test_privacy_canary.py` 验证的是**词汇层**
(「不存在内容通道」+ 键集闭合),并在 docstring 里**明文**把「把内容硬塞进 identity
字段(例如往 `endpoint_id` 里写 prompt)」交给调用方;产品代码会不会这么做**从未被验证**。
本判据先把**扫描面**从散文变成源码内、可复算、无第三种状态的清单:每个可机械发现的
发射点都必须被**恰好一条**显式分类认领 —— 受判出口(会被 EC-02 逐面扫描)或
**带理由的豁免**。新增出口/新形态**未登记即判红**,登记的发射点消失同样判红。

**边界**:canonical state(PG 域实体 / SQLite 域表)允许持有用户自己的任务输入 ——
那是业务真相,**不是泄漏**;本清单只管**非 canonical 出口**。

本文件**不碰文件系统**(形态自检走 `ast.parse`,反证走合成候选集):判据只需读源码。
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.observability.privacy_exit_census import (
    EXEMPT,
    JUDGED,
    PRODUCT_ROOTS,
    Emitter,
    EmitterKind,
    ExemptProducer,
    ExitSurface,
    classify_module,
    discover_emitters,
    lower_bound_findings,
    partition_findings,
    surface_findings,
)

ROOT = Path(__file__).resolve().parents[2]

_REASON_WORKER_PROCESS = "worker 进程面:默认(离线 Fake、进程内)运行路径上不启动该进程"
_REASON_CLI = "CLI / 一次性工具面:默认控制面路径不调用"
_REASON_CONTAINER = "容器 / GPU 执行面:默认路径不进入容器"
_REASON_POSTGRES = "postgres 组合根:默认(SQLite + Fake)路径不装配它"
_REASON_REAL_RELAY = "真实中转站链路:默认路径用 FakeModelGateway,不经过 relay"
_REASON_REAL_RUNTIME = "真实 OpenHands adapter:默认 runtime 是 Fake"
_REASON_WORKER_GATEWAY = "独立 worker-gateway 应用:默认控制面进程不装配它"
_REASON_EVAL_IO = "eval 报告 IO:默认控制面路径不写 eval 报告"
_REASON_WORKSPACE_BUNDLE = "workspace bundle 物化:默认路径用 FakeWorkspaceBackend"
_REASON_VOCABULARY = "观测词汇层定义点(operation / metric API 自身):定义发射 API,不是内容发射点"

#: 受判出口(EC-02 逐面扫描;**观测方式**必须写明,否则本文件自身的判据判红)。
EXIT_SURFACES: tuple[ExitSurface, ...] = (
    ExitSurface(
        id="otlp-traces-wire",
        kind=EmitterKind.otlp_span,
        classification=JUDGED,
        observation="注入真实 OTLP sink 后,`/v1/traces` 收到的原始 wire bytes + 解码后的 span 属性",
        reason="",
        producers=(
            "adapters/sqlite/workflow_engine.py",
            "packages/application/evaluation/runner.py",
            "packages/application/run_orchestration/phase_runner.py",
            "packages/application/run_orchestration/service.py",
            "packages/application/tool_plane/execution.py",
            "services/api/experiment_queue.py",
            "services/api/lease_recovery.py",
            "services/api/scheduler.py",
        ),
    ),
    ExitSurface(
        id="otlp-metrics-wire",
        kind=EmitterKind.otlp_metric,
        classification=JUDGED,
        observation="真实 OTLP sink 注入后 `/v1/metrics` 的原始 bytes 与解码属性",
        reason="",
        producers=(
            "adapters/otel/failsafe.py",
            "adapters/sqlite/workflow_ops.py",
            "packages/application/evaluation/runner.py",
            "services/api/experiment_queue.py",
            "services/api/lease_recovery.py",
        ),
    ),
    ExitSurface(
        id="application-log",
        kind=EmitterKind.application_log,
        classification=JUDGED,
        observation="`caplog` 捕获的 logging record(含 `record.getMessage()` 与格式化后的行)",
        reason="",
        producers=(
            "services/api/app.py",
            "services/api/experiment_queue.py",
        ),
    ),
    ExitSurface(
        id="read-face-http",
        kind=EmitterKind.read_face,
        classification=JUDGED,
        observation="应用自身路由表上的 GET/HEAD 响应体(经 `TestClient` 实取)",
        reason="",
        producers=(
            "services/api/app.py",
            "services/api/routers/approvals.py",
            "services/api/routers/artifacts.py",
            "services/api/routers/budget_forecast.py",
            "services/api/routers/deliverable.py",
            "services/api/routers/experiment_queue.py",
            "services/api/routers/experiments.py",
            "services/api/routers/inspection.py",
            "services/api/routers/library.py",
            "services/api/routers/lineage.py",
            "services/api/routers/llm_endpoints.py",
            "services/api/routers/memory.py",
            "services/api/routers/models.py",
            "services/api/routers/notifications.py",
            "services/api/routers/operations.py",
            "services/api/routers/ops_control.py",
            "services/api/routers/ops_schedules.py",
            "services/api/routers/ops_view.py",
            "services/api/routers/policy.py",
            "services/api/routers/project_cost_forecast.py",
            "services/api/routers/projects.py",
            "services/api/routers/protocol_drafts.py",
            "services/api/routers/run_events.py",
            "services/api/routers/runs.py",
            "services/api/routers/team_protocol.py",
            "services/api/routers/tool_packs.py",
            "services/api/routers/tool_providers.py",
            "services/api/routers/tool_registrations.py",
            "services/api/routers/workspace_snapshots.py",
        ),
    ),
    ExitSurface(
        id="failure-payload",
        kind=EmitterKind.failure_payload,
        classification=JUDGED,
        observation="`ProblemDetail` 响应体(含未被二次脱敏的 `ApiError.detail`)与失败消息字段",
        reason="",
        producers=(
            "services/api/approvals.py",
            "services/api/catalog_merge.py",
            "services/api/deps.py",
            "services/api/idempotency.py",
            "services/api/mappers/cost_daily.py",
            "services/api/mappers/endpoints.py",
            "services/api/mappers/operations.py",
            "services/api/mappers/project_cost_forecast.py",
            "services/api/protocol_source.py",
            "services/api/routers/approvals.py",
            "services/api/routers/artifacts.py",
            "services/api/routers/budget_forecast.py",
            "services/api/routers/deliverable.py",
            "services/api/routers/experiment_queue.py",
            "services/api/routers/experiments.py",
            "services/api/routers/inspection.py",
            "services/api/routers/library.py",
            "services/api/routers/lineage.py",
            "services/api/routers/llm_endpoints.py",
            "services/api/routers/memory.py",
            "services/api/routers/models.py",
            "services/api/routers/notifications.py",
            "services/api/routers/operations.py",
            "services/api/routers/ops_control.py",
            "services/api/routers/ops_schedules.py",
            "services/api/routers/ops_view.py",
            "services/api/routers/policy.py",
            "services/api/routers/project_cost_forecast.py",
            "services/api/routers/projects.py",
            "services/api/routers/protocol_drafts.py",
            "services/api/routers/run_events.py",
            "services/api/routers/runs.py",
            "services/api/routers/team_custom.py",
            "services/api/routers/team_protocol.py",
            "services/api/routers/tool_packs.py",
            "services/api/routers/tool_registrations.py",
            "services/api/routers/workspace_snapshots.py",
            "services/api/run_access.py",
            "services/api/run_execution.py",
            "services/api/schedule_support.py",
            "services/api/team_support.py",
            "services/api/tool_pack_support.py",
            "services/api/tool_registry_support.py",
        ),
    ),
    ExitSurface(
        id="disk-run-artifacts",
        kind=EmitterKind.disk_write,
        classification=JUDGED,
        observation="受判运行根(临时目录)下的制品 blob 与运行 / 证据目录文件内容",
        reason="",
        producers=("adapters/sqlite/artifact_store.py",),
    ),
    ExitSurface(
        id="stdout-stderr",
        kind=EmitterKind.stdout,
        classification=EXEMPT,
        observation="",
        reason=(
            "默认(进程内 Fake)路径上没有任何 print 生产点:命中的模块全在 worker 进程 / "
            "CLI / 容器内面;EC-02 仍以正控制证明该通道对内容可见"
        ),
        producers=(),
    ),
)

#: 受判形态在**默认路径之外**的生产者:逐条登记理由,不是静默放过。
EXEMPT_PRODUCERS: tuple[ExemptProducer, ...] = (
    ExemptProducer("adapters/cli/eval_gate.py", EmitterKind.disk_write, _REASON_CLI),
    ExemptProducer("adapters/cli/eval_gate.py", EmitterKind.stdout, _REASON_CLI),
    ExemptProducer("adapters/contracts/eval_report_io.py", EmitterKind.disk_write, _REASON_EVAL_IO),
    ExemptProducer(
        "adapters/execution/docker_backend.py", EmitterKind.disk_write, _REASON_CONTAINER
    ),
    ExemptProducer(
        "adapters/execution/docker_backend.py", EmitterKind.otlp_span, _REASON_CONTAINER
    ),
    ExemptProducer("adapters/execution/gpu_probe.py", EmitterKind.disk_write, _REASON_CONTAINER),
    ExemptProducer(
        "adapters/openhands/policy_wrapper.py", EmitterKind.otlp_span, _REASON_REAL_RUNTIME
    ),
    ExemptProducer("adapters/postgres/artifact_store.py", EmitterKind.disk_write, _REASON_POSTGRES),
    ExemptProducer("adapters/postgres/outbox_relay.py", EmitterKind.otlp_metric, _REASON_POSTGRES),
    ExemptProducer(
        "adapters/postgres/telemetry_notes.py", EmitterKind.otlp_metric, _REASON_POSTGRES
    ),
    ExemptProducer(
        "adapters/postgres/workflow_engine.py", EmitterKind.otlp_metric, _REASON_POSTGRES
    ),
    ExemptProducer("adapters/postgres/workflow_engine.py", EmitterKind.otlp_span, _REASON_POSTGRES),
    ExemptProducer(
        "adapters/postgres/workflow_requeue.py", EmitterKind.otlp_span, _REASON_POSTGRES
    ),
    ExemptProducer("adapters/relay/gateway.py", EmitterKind.otlp_span, _REASON_REAL_RELAY),
    ExemptProducer("adapters/relay/transport.py", EmitterKind.otlp_metric, _REASON_REAL_RELAY),
    ExemptProducer(
        "adapters/workspace/bundle.py", EmitterKind.disk_write, _REASON_WORKSPACE_BUNDLE
    ),
    ExemptProducer(
        "packages/application/observability/scope.py", EmitterKind.otlp_metric, _REASON_VOCABULARY
    ),
    ExemptProducer(
        "services/api/worker_gateway/app.py", EmitterKind.failure_payload, _REASON_WORKER_GATEWAY
    ),
    ExemptProducer(
        "services/api/worker_gateway/jobs.py", EmitterKind.failure_payload, _REASON_WORKER_GATEWAY
    ),
    ExemptProducer(
        "services/api/worker_gateway/security.py",
        EmitterKind.failure_payload,
        _REASON_WORKER_GATEWAY,
    ),
    ExemptProducer(
        "services/api/worker_gateway/transfer.py",
        EmitterKind.failure_payload,
        _REASON_WORKER_GATEWAY,
    ),
    ExemptProducer("services/worker/__main__.py", EmitterKind.stdout, _REASON_WORKER_PROCESS),
    ExemptProducer(
        "services/worker/deterministic_backend.py", EmitterKind.disk_write, _REASON_WORKER_PROCESS
    ),
    ExemptProducer("services/worker/loop.py", EmitterKind.otlp_metric, _REASON_WORKER_PROCESS),
    ExemptProducer("services/worker/loop.py", EmitterKind.stdout, _REASON_WORKER_PROCESS),
    ExemptProducer("services/worker/reconnect.py", EmitterKind.stdout, _REASON_WORKER_PROCESS),
)

#: **下界**(承 MEM-160):这些受判出口必须在清单里,否则判红。文档点名只是并集的另一半。
REQUIRED_JUDGED_EXITS: tuple[str, ...] = (
    "otlp-traces-wire",
    "otlp-metrics-wire",
    "application-log",
    "read-face-http",
    "failure-payload",
    "disk-run-artifacts",
)

#: 金丝雀**源**(EC-02 注入面):每一源都必须能沿默认路径走到至少一条受判出口。
CANARY_SOURCES: tuple[str, ...] = (
    "task_input",
    "prompt_text",
    "tool_arguments",
    "tool_output",
    "artifact_body",
    "evidence_body",
    "failure_message",
)

#: 本轮**未**机械枚举的发射形态:显式登记 + 理由(不是静默漏掉)。
UNCOVERED_SHAPES: tuple[tuple[str, str], ...] = (
    ("显式文件写入(带 mode 的 open 调用)", "形态未入普查;本轮受判的磁盘面是制品 blob 通道"),
    ("目录镜像(copytree 风格的递归复制)", "workspace 快照面;默认路径用 FakeWorkspaceBackend"),
    ("SQLite / Postgres 数据库文件本身", "canonical / 派生存储,不是非 canonical 出口"),
    ("HTTP 出站请求体(中转站 / 工具 provider)", "默认路径不出网;真实端点面登记为不可本机验证"),
)

#: 形态谓词自检样本:每段源码必须被对应谓词认出来(样本只在内存里 parse)。
_SAMPLE_SOURCES: tuple[tuple[EmitterKind, str], ...] = (
    (EmitterKind.application_log, "import logging\nlogging.getLogger('x')\n"),
    (EmitterKind.stdout, "print('x')\n"),
    (EmitterKind.otlp_span, "with operation(sink, scope=S, name='n'):\n    pass\n"),
    (EmitterKind.otlp_metric, "sink.record_metric(sample)\n"),
    (EmitterKind.disk_write, "blob_path.write_text('x')\n"),
    (EmitterKind.read_face, "@router.get('/x')\ndef f():\n    pass\n"),
    (EmitterKind.failure_payload, "raise ApiError(404, 't', 'd')\n"),
)


def _discovered() -> tuple[Emitter, ...]:
    return discover_emitters(ROOT, PRODUCT_ROOTS)


def test_every_emitter_candidate_is_explicitly_classified() -> None:
    """**没有第三种状态**:每个候选出口要么受判、要么带理由豁免;未分类/重复/陈旧都判红。"""
    problems = partition_findings(_discovered(), EXIT_SURFACES, EXEMPT_PRODUCERS)
    assert not problems, "出口分类清单与普查不符:\n" + "\n".join(problems)


def test_the_registry_itself_is_well_formed() -> None:
    """清单自洽:受判面有观测方式与生产者下界,豁免面有理由。"""
    problems = surface_findings(EXIT_SURFACES, EXEMPT_PRODUCERS)
    assert not problems, "出口清单自身不合规:\n" + "\n".join(problems)


def test_the_required_judged_lower_bound_is_pinned_in_source() -> None:
    """必备受判出口的下界来自**判据源码**(承 MEM-160:并集射程会掩盖清单收缩)。"""
    judged = frozenset(item.id for item in EXIT_SURFACES if item.classification == JUDGED)
    assert not lower_bound_findings(judged, REQUIRED_JUDGED_EXITS)
    assert len(judged) >= 5, f"受判出口太少({len(judged)} < 5),扫描面退化成空真"


def test_the_canary_source_inventory_is_declared() -> None:
    """金丝雀源覆盖 GOAL 要求的六类 + 失败消息。"""
    required = {
        "task_input",
        "prompt_text",
        "tool_arguments",
        "tool_output",
        "artifact_body",
        "evidence_body",
    }
    assert required <= set(CANARY_SOURCES)
    assert "failure_message" in CANARY_SOURCES


def test_uncovered_emitter_shapes_are_registered_with_reasons() -> None:
    """未机械枚举的形态**显式登记 + 理由**;不得留空。"""
    assert UNCOVERED_SHAPES, "未覆盖面登记为空"
    blank = [name for name, reason in UNCOVERED_SHAPES if not reason.strip()]
    assert not blank, f"未覆盖面缺少理由:{blank}"


def test_the_census_is_not_vacuous() -> None:
    """普查面必须非空(承 MEM-156):空集上的「全部已分类」是空真。"""
    discovered = _discovered()
    kinds = {emitter.kind for emitter in discovered}
    assert len(discovered) >= 50, f"候选出口太少({len(discovered)}),普查失效"
    assert len(kinds) >= len(EmitterKind) - 1, f"命中的发射形态不足:{sorted(kinds)}"


def test_a_new_unclassified_emitter_is_red() -> None:
    """反证(合成候选集):未登记的发射点 ⇒ 分区判红并点名 (module, kind)。"""
    synthetic = (
        Emitter("packages/brand_new.py", EmitterKind.application_log),
        Emitter("services/api/app.py", EmitterKind.application_log),
    )
    problems = partition_findings(synthetic, EXIT_SURFACES, EXEMPT_PRODUCERS)
    assert any(
        "packages/brand_new.py" in problem and "未分类" in problem for problem in problems
    ), problems


def test_a_duplicate_classification_is_red() -> None:
    """反证:同一候选被两条分类同时认领 ⇒ 判红(否则清单可以有隐藏的重复口径)。"""
    surfaces = (
        ExitSurface("a", EmitterKind.stdout, JUDGED, "obs", "", ("packages/x.py",)),
        ExitSurface("b", EmitterKind.stdout, JUDGED, "obs", "", ("packages/x.py",)),
    )
    problems = partition_findings((Emitter("packages/x.py", EmitterKind.stdout),), surfaces, ())
    assert any("重复分类" in problem for problem in problems), problems


def test_a_stale_registry_entry_is_red() -> None:
    """反证:登记的生产者在树上消失 ⇒ 判红(否则清单会永远「看起来覆盖」)。"""
    problems = partition_findings((), EXIT_SURFACES, EXEMPT_PRODUCERS)
    assert any("登记陈旧" in problem for problem in problems), problems


def test_a_blank_exemption_reason_is_red() -> None:
    """反证:豁免理由抽空 ⇒ 判红。"""
    blank = ExemptProducer("packages/x.py", EmitterKind.stdout, "  ")
    found = surface_findings(
        (ExitSurface("s", EmitterKind.stdout, EXEMPT, "", "", ()),),
        (blank,),
    )
    assert any("缺少理由" in problem for problem in found), found


def test_a_judged_surface_without_observation_is_red() -> None:
    """反证:受判面不写观测方式(或生产者为空) ⇒ 判红。"""
    found = surface_findings((ExitSurface("s", EmitterKind.stdout, JUDGED, " ", "", ()),), ())
    assert len(found) == 2, found


def test_a_shrinking_lower_bound_is_red() -> None:
    """反证:必备清单少一条(并集里还有别的入口)仍然判红。"""
    findings = lower_bound_findings(frozenset({"application-log"}), REQUIRED_JUDGED_EXITS)
    assert findings, "下界收缩没有被判红 —— 并集射程会掩盖它(承 MEM-160)"


def test_the_shape_predicates_actually_match() -> None:
    """形态谓词自检:七种形态各一段最小样本,必须被认出来(谓词静默失效即判红)。"""
    for kind, source in _SAMPLE_SOURCES:
        assert kind in classify_module(ast.parse(source)), f"形态谓词失效:{kind}"
