---
id: PLAN-20260915-074
slug: provider-credential-binding
title: provider 凭据绑定：credential_ref 从"无法表达"变成"被执法且可见"（只查存在性，不碰明文）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 11（续期后首轮）= RECHECK-20260915-073 后继② / RECHECK-20260915-072 W-4。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE，从 cycle 11 续跑）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-074-provider-credential-binding.md
memory_entries:
  - MEM-20260915-049-presence-check-is-not-a-resolve
---

# PLAN-20260915-074 — provider 凭据绑定（GOAL-003 cycle 11）

## 目标

`ToolProviderSpec` **无法表达"这个 provider 需要哪个凭据"**：凭据只在 adapter 的
构造函数里以 `credential_ref` 存在（`adapters/mcp/provider.py:63`、
`adapters/research_tools/ncbi.py:69`），Domain/spec/注册面/读面全都没有这个字段。
后果与 cycle 10 修掉的 `endpoint_env` 同类，但方向相反：

```text
MCP streamable_http：构造时就要求 credential_ref（provider.py:70 直接 raise）
                     —— 但这条要求**进不了** spec，注册面/读面看不见，
                        注册一个需要凭据的 provider 时没人知道它能不能用
注册面：能写 kind/transport/capabilities/pin/endpoint_env，写不了"需要什么凭据"
读面：健康探测只看 endpoint 与 health_check，从不问"凭据在不在"
```

于是"provider 需要凭据"这件事只存在于进程内构造参数里：**既不被执行、也不被看见**。

## 口径

1. **语义定死**：`credential_ref` = 该 provider **必需**的凭据引用（名字）。
   **声明即必需**——写了就表示"没有它这个 provider 不可用"，因此执法（拦探测）
   有明确依据；反过来，可选凭据（例如 NCBI E-utilities 无 key 也可用、只是限速更严）
   **不声明**，示例配置按此对齐。
2. **只查存在性，不碰明文**：判定走**存在性检查**（`CredentialResolver.has`），
   **不调用 `resolve`**、不物化 `SecretValue`、不落盘、不进日志/异常/repr。
   读面只有 `state / credential_ref / present`，**没有值**。
3. **凭据边界不变**：不新增凭据通道、不做凭据转发、不做 secret 枚举
   （`has` 只回答调用方已经写在 spec 里的那个 ref）——与 AGENTS.md §9 一致。
4. **执法而不只是显示**：声明了 `credential_ref` 的 provider，若该凭据当前不可解析，
   健康探测**不得**报 HEALTHY——如实 UNKNOWN + 原因（点名 ref，不点值）。
   未声明该字段的 provider 行为不变（证明门槛确实挂在"声明"上）。
5. **可见**：绑定状态进注册读面，且在凭据从不在于在（`register()`/`unregister()`）时
   立刻反映——读面回答的是"此刻能不能用"，不是"注册时是什么样"。
6. **NATIVE 也适用**（与 `endpoint_env` 故意不同）：端点门槛跳过 NATIVE 是因为
   NATIVE 没有外部端点可解析；凭据门槛对 NATIVE 同样成立——"声明的必需凭据不在"
   是凭据事实，与传输形态无关。此不对称在代码与文档里都写明。

## 范围

- 修改（Port/Domain）：`packages/application/ports/credential_resolver.py`（新增
  `has`）、`packages/domain/tools.py`、`packages/domain/tool_registry.py`、
  `adapters/sqlite/tool_provider_registry.py`。
- 修改（adapter 实现补齐 `has`）：`adapters/relay/credential_resolver.py`、
  `adapters/relay/registry_credential_resolver.py`（收紧为"可解析"语义）、
  `adapters/fakes/credential_resolver.py`、`tests/application/relay_fakes.py`、
  `tests/observability/canary_support.py`。
- 修改（控制面）：`services/api/tool_provider_credentials.py`（新增）、
  `services/api/preflight_support.py`、`services/api/dto/tool_providers.py`、
  `services/api/tool_registry_support.py`、`services/api/routers/tool_registrations.py`。
- 修改（规格/配置/文档）：`schemas/tool-provider.schema.json`、
  `examples/config/tool_providers.yaml`、`docs/integration/MCP_TOOL_PROVIDERS.md`、
  `apps/web/src/api/types.ts` + `apps/web/tests/e2e/stub-routes-registry.ts`、
  `docs/api/openapi.m13.json`（重生成）。
- 新增：`tests/api/test_tool_provider_credential_binding.py`；
  在 `tests/adapters/sqlite/test_tool_provider_registry_store.py` 与
  `tests/contracts/test_ports_semantics.py` 内补用例。
- **不改**：任何 adapter 的凭据注入方式（仍由 composition 构造参数决定）、
  策略面、console UI 列（UI 展示留给后续轮次，读面先就位）。

## 验收条件

- [x] AC-01 **声明面贯通**：`ToolProviderSpec.credential_ref` + `ProviderRegistration.credential_ref`
      + `spec()` 携带 + SQLite 往返 + **旧行解码为未声明** + schema 描述 + 注册/更新写面
      DTO 接受该字段（OpenAPI 重生成、TS 类型镜像）。
- [x] AC-02 **存在性检查，不物化**：`CredentialResolver.has` 成为 Port 成员并被**全部**实现
      补齐（env / registry / fake / 测试替身 / canary）；三态判定
      `NOT_DECLARED / ABSENT / PRESENT`（外加"存在性检查不可用"的诚实收敛态），
      **不调用 `resolve`**（用例以"resolve 会抛错的 resolver"证明这一点）。
- [x] AC-03 **执法**：声明了 `credential_ref` 且当前不可解析 ⇒ 探测 UNKNOWN + 点名 ref；
      注册/去掉凭据（`register`/`unregister` 或 env 变化）⇒ 同一 fixture 结论随之改变；
      **去掉声明** ⇒ 行为回到从前（门槛挂在声明上）。
- [x] AC-04 **不泄漏**：凭据值不出现在 DTO 序列化、健康 detail、`repr`、
      异常消息与存储行里（用例显式放入可识别的哨兵值并全路径搜索）。
- [x] AC-05 **可见**：注册读面 DTO 带 `credential_binding`（state/ref/present），
      环境或注册表变化立刻反映；示例配置按"声明即必需"对齐（NCBI 不声明 + 注释说明原因）。
- [x] AC-06 **全量门禁 + 记录**：m0 23 项 + 受影响定向套件 + web 门 + RECHECK-074 +
      MEM + GOAL cycle 11 记账 + ALL_PLAN 行。

## 实施清单

- [x] WP-A Port：`CredentialResolver.has` + 全部实现补齐（含语义统一为"可解析"）
- [x] WP-B Domain/存储：spec/registration/spec()/SQLite 往返/旧行解码
- [x] WP-C 判定与执法：`tool_provider_credentials.py` + 探测门槛 + 读面投影
- [x] WP-D 规格/配置/文档/TS 对齐 + OpenAPI 重生成
- [x] WP-E 用例（新文件 + 两处补用例）
- [x] WP-F 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
$ python -m pytest tests/api/test_tool_provider_credential_binding.py -q
8 passed
$ python -m pytest tests/api -q
422 passed
$ python -m pytest tests/adapters/sqlite tests/loaders tests/api -q
525 passed
$ python -m pytest tests/contracts tests/application -q
955 passed, 57 skipped
$ python -m pytest tests/observability -q
58 passed, 1 skipped
$ python -B tools/gen_openapi.py
wrote docs/api/openapi.m13.json (211649 chars)   # +1276 字符
$ (cd apps/web && pnpm exec playwright test)
83 passed (4.6m)          # 结构与像素基线均未变
$ (cd apps/web && pnpm exec playwright test --config playwrightLive.config.ts)
36 passed (49.3s)         # +1：live: 声明的必需凭据不在时如实 UNKNOWN
$ python -m mypy
Success: no issues found in 867 source files
$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks
```

m0 首轮红于 `python/typecheck`：把 `has` 加进 Port 后，mypy 用协议检查列出 6 处
结构上不再满足协议的老替身（`tests/application/protocol_fixtures.py`、
`tests/application/model_relay/test_live_probe_not_verified.py`（2 个类）、
`tests/loaders/test_example_protocol_integration.py`、`tests/application/m12_clean_run_fixtures.py`、
`tests/distributed/test_gpu_research_slice.py`）——**全部补实现，未放宽类型**。
第二轮红于 `framework/validate`，两条报错都是**记录尚未落盘**（本 PLAN 未登记 ALL_PLAN、
MEM-049 指向尚不存在的本 RECHECK），落盘后复跑通过（与 cycle 8 同类，属记账漏项）。

## 状态历史

- 2026-09-17 创建（IN_PROGRESS）：derive 时核对了两件事——① MCP streamable_http
  在构造期就要求 `credential_ref`，而这条要求进不了 spec；② NCBI 的凭据是**可选**的
  （`_api_key()` 在 `InvalidInputError` 时返回 None，无 key 也能用），因此本轮把
  字段语义定为"声明即必需"，示例配置**不**给 ncbi 声明凭据（否则会把可用 provider
  误判为不可用）。
- 2026-09-17 WP-A…E 完成：Port 加 `has` 并由 mypy 逼出 6 处老替身补齐；域/存储/写面/
  读面/OpenAPI/TS 全线打通；判定只查存在性（用会炸的 `resolve` 变成可执行断言）；
  门槛对所有 kind 成立（与端点门槛的不对称有专门用例）；新增 8 条用例 + store 往返 +
  Port 语义用例全绿。
- 2026-09-17 DONE：全量门禁通过（m0 **PASS: profile=m0; 23 deterministic checks**，
  定向 **8 + 422 + 525 + 955 + 58** passed，stub e2e **83** / live e2e **36**，
  ruff/format 干净，mypy **867 files clean**，OpenAPI 已重生成），记录落盘
  （RECHECK-074 PASS_WITH_WARNINGS + MEM-049 + GOAL cycle 11 记账 + ALL_PLAN）。

## 影响报告

- **Domain/API/schema**：`ToolProviderSpec` 新增 `credential_ref`（**必需性声明**，
  只存引用名）；`ProviderRegistration` 同步新增；schema 新增同名字段（含语义描述）；
  注册/更新写面 DTO 接受 `credential_ref`；注册读面 DTO 新增 `credential_binding`；
  OpenAPI 已重生成，TS 类型已镜像。
- **Port 变更（破坏性）**：`CredentialResolver` 新增 `has(credential_ref) -> bool`
  ——所有实现（本仓 6 处）必须补齐，第三方实现同样受此约束（mypy 会报）。
- **安全/凭据**：**不**新增凭据通道、不做凭据转发、不做枚举；判定只回答布尔、
  不物化明文；读面只有状态/引用名/布尔。凭据值与端点值一样永不入库。
- **兼容性/迁移风险**：声明了 `credential_ref` 而凭据不在的部署，其 provider 健康状态会
  如实变 UNKNOWN（有意的诚实化，已写进 schema 与文档）；旧存储行解码为"未声明"，
  行为与从前一致；未声明该字段的 provider 行为一字不变。
- **可观测性**：健康 detail 点名**引用名**（名字不是秘密），不记值。
- **下一项任务**：按声明给 adapter 接线（凭据与端点都还没"被用上"）；
  或 `conn.cursor()` 收口 / 锁粒度（每线程连接）。

## 已知风险

- **"声明即必需"会被误用**：把可选凭据声明成必需，会让本来可用的 provider 判 UNKNOWN。
  这是字段语义的直接后果（不这样，"必需"无从执行），已用示例注释与用例钉住 NCBI 这个例子。
- **`UNCHECKED` 是防御态**：仓储内 `has` 都是全函数，正常部署不会出现；它保证"凭据边界
  故障"不会被说成"凭据不在"。
- **PATCH 清不掉声明**：`exclude_none=True` 使 `credential_ref: null` 等同"没提供"
  （与 `endpoint_env` 既有行为一致），本轮未改（要改需单独一轮处理两个字段的语义）。
- **仍未"用上"凭据与端点**：spec 的声明与 adapter 的构造参数目前是两处，
  "按声明接线"（含受控出网）是下一轮候选。
