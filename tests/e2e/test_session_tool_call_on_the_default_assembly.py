"""GOAL-029 EC-01 判据（cycle 2）：**默认装配下会话工具真被调用**（收 `W-2`/`W-3`）。

**它补的是什么**：cycle 1 证到「策略面不再无条件拒绝」+「实现接进了生产组合根」；
但**没有任何判据**证明「模型真的调了这个工具，且它的 executor 真的跑了」。
既有的 e2e 判据（`test_tool_binding_*` / `test_multi_role_*`）用的是**只会回文本**的
mock 端点 —— 全仓 e2e 里**没有一处** mock 会发出 `tool_calls`（实测检索确认），
所以「会话起得来」与「工具跑得动」之间的落差从未被覆盖。本文件补这条。

**三件事逐条取证**：

1. **端到端真跑**（`W-3`）：mock 端点**发出真实工具调用**（OpenAI-compatible 的
   `tool_calls` wire 形状）⇒ 工具的 executor **被触达**，且返回内容**回到模型**
   （读面里出现 `ObservationEvent`）。判据读的是 **executor 被调用**这个事实，
   不是 run 终态（cycle 1 已证终态绿不蕴含工具运行）。
2. **调用参数是平铺的**（本轮实测到的真缺陷）：SDK 把 action 字段渲染成**模型看到的**
   参数 schema。带 `arguments: dict` 包装字段时，模型看到「一个叫 arguments 的对象」⇒
   按常理构造的调用（`{"artifact_id": "x"}`）撞 `extra="forbid"` 得到
   `Extra inputs are not permitted` —— **调用到了桥却在校验处被拒**。
   判据断言：模型可见 schema **没有** `arguments` 包装字段，且**平铺**参数能通过校验。
3. **两条反证合跑**（`W-2`，承 `MEM-20261001-180`）：registry 进程级只增不减 ⇒
   本文件把「未注册的专属名字 ⇒ 点名失败」与「有实现的名字 ⇒ 能解析」放在**同一次运行**里，
   并施加**显式摘除**（`registry._REG.pop`）使断言与用例执行顺序无关。

**为什么必须在这儿而不是在 `test_session_tool_reaches_executor.py`**：那个文件测的是
**策略门**（executor 触达与否由策略决定），用 `TestLLM` 喂脚本；本文件测的是**线上形状**
（真 wire + 真解析 + 真 schema）；两者不是同一件事，**不互相顶替**（承 MEM-159）。
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Iterator

import pytest

from adapters.fakes import FakeCredentialResolver
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_tools import build_session_tools
from adapters.openhands.session_types import AdapterDependencies
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.ports.agent_runtime import AgentSessionSpec
from packages.application.preflight.policy_check import policy_scope_for
from services.api.assembly import policy_bindings
from services.api.runtime_support import session_llm_factory
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

#: 端到端那一半用**出厂已放行**的能力名（会话工具走能力名求值 ⇒ 只有放行的才会到 executor）。
#: 用真名而不是专属名是被**策略面**决定的：专属名没有 `allow` 规则 ⇒ default DENY ⇒
#: 根本到不了 executor（实测：`policy denied tool execution`）。「未注册 ⇒ 点名失败」
#: 那条反证改用下面的专属名，它**不经过**策略门（见 `TestBothRefutationsRunInOneProcess`）。
_CALLED_TOOL = "artifact.read"
_WRITABLE_TOOL = "workspace.read"

#: 仅用于**注册面**反证的专属名字（别处从不使用 ⇒ registry 残留不影响确定性）。
_ABSENT_TOOL = "goal029.e2e.absent"

#: 模型应该发出的**平铺**参数（真实工具调用的形状：参数就是工具自己的参数）。
_FLAT_ARGUMENTS = {"artifact_id": "run-goal029:deliverable.json"}

_REACHED: list[dict[str, object]] = []


class _ToolCallingRelay(BaseHTTPRequestHandler):
    """会**发出工具调用**的最小 OpenAI-compatible 端点（离线、环回）。

    第一轮回 `finish_reason=tool_calls` + 一个真实的 `tool_calls` 条目；
    之后回文本收尾。`arguments` 是**平铺**的（这正是真实模型的形状）。
    """

    rounds = 0
    tool_name = _CALLED_TOOL
    seen: list[dict[str, Any]] = []

    def do_GET(self) -> None:  # noqa: N802
        payload = json.dumps({"data": [{"id": "relay-model", "object": "model"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        _ToolCallingRelay.seen.append(body)
        _ToolCallingRelay.rounds += 1
        if _ToolCallingRelay.rounds == 1:
            message: dict[str, Any] = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-goal029",
                        "type": "function",
                        "function": {
                            "name": _ToolCallingRelay.tool_name,
                            "arguments": json.dumps(_FLAT_ARGUMENTS),
                        },
                    }
                ],
            }
            finish = "tool_calls"
        else:
            message = {"role": "assistant", "content": "Done."}
            finish = "stop"
        response = {
            "id": f"chatcmpl-goal029-{_ToolCallingRelay.rounds}",
            "object": "chat.completion",
            "created": 1755000000,
            "model": body.get("model", "relay-model"),
            "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        }
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


@pytest.fixture
def tool_calling_relay() -> Iterator[str]:
    """本机 mock 端点（threading HTTP 服务器；不出公网），每例重置计数。"""
    _ToolCallingRelay.rounds = 0
    _ToolCallingRelay.seen = []
    _ToolCallingRelay.tool_name = _CALLED_TOOL
    server = HTTPServer(("127.0.0.1", 0), _ToolCallingRelay)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _invoker_returning(payload: dict[str, object]) -> Any:
    """记录触达并返回 JSON 文本的桥（判据读的就是 `_REACHED` 这个事实）。"""

    def _invoke(arguments: dict[str, object], conversation: object = None) -> str:
        _REACHED.append(dict(arguments))
        return json.dumps(payload, ensure_ascii=False)

    return _invoke


def _run_session(base_url: str, tool_name: str) -> tuple[str, list[Any]]:
    """起一次真实会话（真 LLM 客户端 → mock 端点 → 真 SDK 解析），返回 (终态, 事件)。

    **走产品装配**：`session_llm_factory`（受门工厂）+ `build_session_tools`（真实注册面）
    —— 与 `openhands_deps(map_tools=False)` 同一条路径；本函数只把这个装配**单独**起，
    以便判据直接读「executor 是否被触达」而不是绕经 run 编排的读面。
    """
    from tests.api.run_fixtures import make_run_ready_deps
    from tests.e2e.live_run_support import point_catalog_at

    _REACHED.clear()
    deps = make_run_ready_deps()
    point_catalog_at(deps, base_url)
    context = deps.preflight_override
    assert context is not None
    endpoint = context.catalog.endpoints["main"]
    model = context.catalog.models["agnes_flash"]

    credentials = FakeCredentialResolver({"LLM_MAIN_KEY": "sk-goal029-fake"})
    policy_evaluator = policy_bindings().get("policy_evaluator")
    assert policy_evaluator is not None, "policy.yaml must be loadable for this judgment"
    adapter = OpenHandsRuntimeAdapter(
        AdapterDependencies(
            credential_resolver=credentials,
            policy_evaluator=policy_evaluator,
            build_llm=session_llm_factory(credentials, EndpointUrlPolicy(allow_localhost=True)),
            build_workspace=_workspace_builder(),
            register_tools=build_session_tools({tool_name: _invoker_returning({"ok": True})}),
        )
    )
    spec = AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
        frozen_tool_set=(tool_name,),
        endpoint=endpoint,
        model=model,
    )
    handle = adapter.create_session(spec)
    result = adapter.run(handle.session_id)
    events = list(adapter.stream_events(handle.session_id))
    adapter.close()
    return str(result.status), events


def _workspace_builder() -> Any:
    """测试侧 workspace 构造（显式打开 host shell；生产的默认 deny 不放松）。"""
    from adapters.openhands.workspace_adapter import build_local_workspace

    return lambda lease, session_id: build_local_workspace(lease, session_id, allow_host_shell=True)


class TestTheModelCallingTheToolActuallyRunsIt:
    """① 端到端真跑：模型发出工具调用 ⇒ executor 被触达 + 结果回到模型。"""

    def test_the_relay_actually_emits_a_tool_call(self, tool_calling_relay: str) -> None:
        """受判面非空的第一步：端点真的发了 `tool_calls`（否则下面几条是空真）。"""
        _run_session(tool_calling_relay, _CALLED_TOOL)
        assert len(_ToolCallingRelay.seen) >= 1, "端点一轮也没被调用"
        first = _ToolCallingRelay.seen[0]
        assert first.get("tools"), (
            "模型请求里必须带工具面（否则「模型没调工具」不构成对桥的检验）",
            list(first),
        )
        assert _ToolCallingRelay.rounds >= 2, (
            "最少两轮：第一轮回工具调用、第二轮回文本收尾；实测轮数不足",
            _ToolCallingRelay.rounds,
        )

    def test_the_tools_executor_is_reached(self, tool_calling_relay: str) -> None:
        """**主判据**（`W-3`）：executor 被调用，且收到的参数是模型发的那份**平铺**参数。"""
        status, events = _run_session(tool_calling_relay, _CALLED_TOOL)
        assert status.endswith("SUCCEEDED"), status
        assert _REACHED == [_FLAT_ARGUMENTS], (
            "工具的 executor 必须被触达，且参数逐字等于模型发出的平铺参数；实测触达记录",
            _REACHED,
        )
        kinds = [event.kind.value for event in events]
        assert "tool_call.requested" in kinds, kinds
        assert "step.completed" in kinds, kinds

    def test_the_result_travels_back_to_the_model(self, tool_calling_relay: str) -> None:
        """结果**回到模型**：请求里出现 tool 角色的回复（内容经桥返回）。"""
        _run_session(tool_calling_relay, _CALLED_TOOL)
        second = _ToolCallingRelay.seen[1]
        tool_messages = [
            message for message in second.get("messages", []) if message.get("role") == "tool"
        ]
        assert tool_messages, "第二轮请求里必须带回 tool 角色的观察（否则模型没拿到结果）"
        assert "ok" in json.dumps(tool_messages[0]), tool_messages[0]


class TestTheModelFacingSchemaTakesFlatArguments:
    """② 模型可见 schema 必须是**平铺**的（本轮实测到的真缺陷的回归判据）。"""

    def test_the_declared_schema_has_no_arguments_wrapper(self) -> None:
        """`arguments` 包装字段会让模型把真实参数嵌进一层 —— 那是**缺陷**形态。

        实测过的失败：模型平铺发 `{"artifact_id": "x"}` ⇒ 校验处
        `Extra inputs are not permitted`（调用到了桥、却在 schema 被拒）。
        """
        schema = _resolved_action_schema()
        properties = schema.get("properties", {})
        assert "arguments" not in properties, (
            "模型可见参数里不得出现 `arguments` 包装字段（它会让真实工具调用撞 extra=forbid）",
            sorted(properties),
        )
        assert schema.get("additionalProperties") is True, (
            "自由形状的参数必须在 schema 上表达为 additionalProperties: true",
            schema.get("additionalProperties"),
        )

    def test_flat_arguments_validate(self) -> None:
        """平铺参数**必须**能构造出 action（模型发什么就能进什么）。"""
        from adapters.openhands.session_tools import SessionToolAction

        action = SessionToolAction(**_FLAT_ARGUMENTS)
        assert action.arguments() == _FLAT_ARGUMENTS, action.arguments()

    def test_the_bridge_receives_them_unwrapped(self, tool_calling_relay: str) -> None:
        """模型 → 桥的端到端：桥收到的就是平铺那三个键（没有 `arguments` 嵌套）。"""
        _run_session(tool_calling_relay, _CALLED_TOOL)
        assert _REACHED, "executor 未被触达 ⇒ 本判据在空转"
        assert "arguments" not in _REACHED[0], (
            "桥收到的参数不得含 `arguments` 键（那样说明包装又回来了）",
            _REACHED[0],
        )


def _resolved_action_schema() -> dict[str, Any]:
    """按**真实注册面**解析 `_CALLED_TOOL`，取它的模型可见参数 schema。"""
    from openhands.sdk.tool import registry
    from openhands.sdk.tool.spec import Tool

    build_session_tools({_CALLED_TOOL: _invoker_returning({"ok": True})})([_CALLED_TOOL])
    resolved = registry.resolve_tool(Tool(name=_CALLED_TOOL), None)  # type: ignore[arg-type]
    assert len(resolved) == 1, resolved
    schema: dict[str, Any] = resolved[0].action_type.model_json_schema()
    return schema


class TestBothRefutationsRunInOneProcess:
    """③ 两条反证**合跑**（`W-2`；承 MEM-20261001-180：registry 只增不减）。

    本类两个用例在**同一次运行**里成对：先证「有实现 ⇒ 能解析」，再证
    「未注册 ⇒ 点名失败」；且**显式摘除**专属名字，使断言与执行顺序无关
    （不清理的话，同进程里别的装配留下的注册会让「未注册」假绿）。
    """

    def test_a_name_with_an_implementation_resolves(self) -> None:
        from openhands.sdk.tool import registry
        from openhands.sdk.tool.spec import Tool

        with _explicitly_unregistered(_CALLED_TOOL):
            build_session_tools({_CALLED_TOOL: _invoker_returning({"ok": True})})([_CALLED_TOOL])
            resolved = registry.resolve_tool(Tool(name=_CALLED_TOOL), None)  # type: ignore[arg-type]
            assert len(resolved) == 1, resolved
            assert resolved[0].name == _CALLED_TOOL, resolved[0].name

    def test_a_name_without_an_implementation_is_named(self) -> None:
        from openhands.sdk.tool import registry
        from openhands.sdk.tool.spec import Tool

        with _explicitly_unregistered(_ABSENT_TOOL):
            with pytest.raises(KeyError) as excinfo:
                registry.resolve_tool(Tool(name=_ABSENT_TOOL), None)  # type: ignore[arg-type]
        assert _ABSENT_TOOL in str(excinfo.value), (
            "缺实现必须**点名**工具名（不静默降级）",
            str(excinfo.value),
        )

    def test_the_first_refutation_left_its_mark(self) -> None:
        """合跑证据：上一条的注册在执行到这里时仍在（registry 只增不减）。

        若有人把本文件拆成两个进程跑，「未注册」那条会因残留而假绿 ——
        这条断言把「两条确实跑在一次运行里」变成机械事实。
        """
        from openhands.sdk.tool import registry

        assert _CALLED_TOOL in registry._REG, (
            "前一条注册的名字不见了 ⇒ 两条反证不在同一进程（本判据的确定性前提）"
        )


class _explicitly_unregistered:
    """上下文管理器：进入时**显式摘除**名字，退出时恢复原状。

    承 `MEM-20261001-180`：SDK registry 是进程级且只增不减，别的判据（或本文件前面的用例）
    可能已经注册过同名工具 ⇒ 「它未注册」这类断言必须先摘除，否则依赖用例执行顺序。
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._saved_reg: Any = None
        self._saved_usability: Any = None

    def __enter__(self) -> None:
        from openhands.sdk.tool import registry

        self._saved_reg = registry._REG.pop(self._name, None)  # noqa: SLF001 - 判据侧清理
        self._saved_usability = registry._USABILITY_REG.pop(self._name, None)  # noqa: SLF001

    def __exit__(self, *exc: object) -> None:
        from openhands.sdk.tool import registry

        if self._saved_reg is not None:
            registry._REG[self._name] = self._saved_reg  # noqa: SLF001
        if self._saved_usability is not None:
            registry._USABILITY_REG[self._name] = self._saved_usability  # noqa: SLF001


def test_the_probe_names_are_scoped_deliberately() -> None:
    """射程自检（两半各自的前提）：

    - 端到端那半用**出厂绑定表里的真名**（否则策略面不会放行到 executor —— 实测过）；
    - 注册面反证那半用**专属名**（它不经过策略门，且必须与出厂表不相交，
      否则「未注册」断言会被别的装配的注册活动搅乱）。
    """
    from services.api.session_tool_support import DEFAULT_SESSION_TOOL_BINDINGS

    declared = {tool_name for tool_name, _provider, _tool_id in DEFAULT_SESSION_TOOL_BINDINGS}
    assert _CALLED_TOOL in declared, ("端到端必须用出厂声明的能力名", sorted(declared))
    assert _ABSENT_TOOL not in declared, ("注册面反证的专属名不得与出厂表重合", _ABSENT_TOOL)


def test_the_allow_localhost_scope_is_the_one_the_face_uses() -> None:
    """受判面非空：本文件用的能力名在出厂策略里有**真实**归属（否则判据在空集上恒真）。"""
    from packages.application.policy.native import NativePolicyEvaluator
    from packages.application.ports.policy_evaluator import PolicyRequest
    from services.api.catalog import load_policy_definition

    policy = load_policy_definition()
    assert policy is not None
    evaluator = NativePolicyEvaluator(policy)
    capability = "artifact.read"  # 出厂放行的读能力（会话工具走同一能力名求值）
    decision = evaluator.evaluate(
        PolicyRequest(
            actor="agent:goal029",
            capability=capability,
            action="execute",
            scope=policy_scope_for(capability),
            resource=capability,
        )
    )
    from packages.domain.enums import PolicyDecision

    assert decision.decision is PolicyDecision.ALLOW, (
        "端到端那半用的能力必须是**显式放行**（否则到不了 executor）；若它变了需同轮复核",
        decision.decision,
        decision.reason,
    )
    assert decision.reason == "matched allow rule", (
        "必须是**匹配到 allow 规则**（而不是别的路径偶然放行）",
        decision.reason,
    )


def test_the_repo_has_no_other_tool_call_emitting_fixture() -> None:
    """**缺口取证**：本文件是仓内**唯一**会发 `tool_calls` 的 e2e 探针。

    这条断言服务的是「为什么 `W-3` 此前没被覆盖」这个事实本身：既有 e2e 的 mock 端点
    一律只回文本 ⇒ 「会话起得来」与「工具跑得动」之间的落差在仓内**没有被任何东西看着**。
    若将来有人加了第二个发工具调用的夹具，这条会红 —— 那时应把它并入本文件的口径，
    而不是让两处各测一套。
    """
    root = Path(__file__).resolve().parents[2]
    emitters: list[str] = []
    for path in sorted((root / "tests").rglob("*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        if '"tool_calls"' in text and "finish_reason" in text:
            emitters.append(path.relative_to(root).as_posix())
    assert emitters == [], (
        "出现了第二个会发工具调用的夹具 ⇒ 请与本文件统一口径（别让两处各测一套）",
        emitters,
    )
