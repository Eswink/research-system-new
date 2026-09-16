---
id: PLAN-20260915-072
slug: provider-endpoint-binding
title: provider 端点绑定：endpoint_env 从"声明了没人消费"变成"被执法且可见"
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 10 = 相邻长程项（provider 端点/凭据绑定）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-072-provider-endpoint-binding.md
memory_entries:
  - MEM-20260915-047-declared-but-unconsumed-config-is-a-lie
---

# PLAN-20260915-072 — provider 端点绑定（GOAL-003 cycle 10）

## 目标

`ToolProviderSpec.endpoint_env` 是一个**声明了但没有任何消费者**的字段：

```text
声明面：packages/domain/tools.py:105（字段）
        schemas/tool-provider.schema.json:13（{"type": "string", "minLength": 1}，无 description）
        adapters/contracts/resource_loaders.py:143（从 YAML 读入）
消费面：**零**（全仓 grep：唯一构造 McpConnectionSpec 的地方是
        adapters/mcp/provider.py::_resolved_spec，用的是构造时注入的 spec，与 endpoint_env 无关）
现实用法：examples/config/tool_providers.yaml 给 REST provider 写了
        `endpoint_env: NCBI_API_KEY` —— 字段名说"端点"，值却是**凭据**名，
        而且没有任何东西会因此报错
```

于是：配置作者写下的"这个 provider 的端点来自环境变量 X"**既不被执行、也不被看见**，
写错（甚至写成凭据名）与写对没有区别。

## 口径

1. **语义定死并写进 schema/文档**：`endpoint_env` = 环境变量名，其值是该 provider 的
   **端点 URL**。**env-only**：只读 `os.environ`，不读文件、不落盘、不进日志/异常/repr。
2. **凭据不变**：凭据仍只经 `CredentialResolver` 解析（`credential_ref`），
   本轮**不**把 `endpoint_env` 变成凭据通道，也不新增凭据转发。
3. **执法而不只是显示**：声明了 `endpoint_env` 的 provider，若该环境变量未设置，
   健康探测**不得**报 HEALTHY——如实 UNKNOWN + 原因（点名变量，不点值）。
   未声明该字段的 provider 行为不变（证明门槛确实挂在"声明"上）。
4. **可见且不泄漏**：绑定状态进注册读面（state / env 名 / 端点 **digest**），
   **绝不出现端点明文**；digest 用既有 `Digest` 口径。
5. **不夸大**：本轮把 `endpoint_env` 变成**准入条件 + 可见状态**；
   "把解析出的 URL 注入 adapter 实例"需要按 spec 重建 provider（composition 级），
   如实登记为下一轮候选。

## 范围

- 修改：`services/api/tool_provider_endpoints.py`（新增：`EndpointBinding` + `resolve_endpoint_binding`）、
  `services/api/preflight_support.py`（探测前置门槛）、`services/api/dto/tool_providers.py` +
  `services/api/tool_registry_support.py`（读面投影）、`schemas/tool-provider.schema.json`（description）、
  `examples/config/tool_providers.yaml`（修掉凭据名误用）、相关文档。
- 新增：`tests/api/test_tool_provider_endpoint_binding.py`（env-only / 不泄漏 / 三态 / 门槛反证）。
- **不改**：任何 adapter、`CredentialResolver`、策略面、console（UI 面留给下一轮）。

## 验收条件

- [x] AC-01：三态解析（未声明 / 环境变量未设置 / 已设置），且**只**读 `os.environ`
      ——同名值放在文件里不被采信（用例显式构造）。
- [x] AC-02：**不泄漏**——端点明文不出现在 DTO 序列化结果、健康 detail、`repr(binding)`
      与异常消息里；读面只有 env 名 + digest。
- [x] AC-03：**执法**——声明了 `endpoint_env` 且未设置 ⇒ 健康探测 UNKNOWN + 点名原因；
      同一 fixture 去掉声明 ⇒ 仍 HEALTHY（门槛挂在声明上，不是全局收紧）。
- [x] AC-04：**可见**——注册读面 DTO 带绑定三态（含 digest），OpenAPI 同步重生成；
      注册写入/存储往返/旧行解码全线贯通。
- [x] AC-05：**配置/规格对齐**——示例配置不再把凭据名写进 `endpoint_env`；
      schema 有 description；文档写明 env-only 与"凭据不走这里"；用例钉住示例约定。
- [x] AC-06：全量门禁（m0）+ 记录（RECHECK-072 + MEM-047 + GOAL 记账 + ALL_PLAN）。

## 实施清单

- [x] WP-A `EndpointBinding` + `resolve_endpoint_binding`（env-only、digest、无明文）
- [x] WP-B 健康探测门槛（声明 + 未设置 ⇒ UNKNOWN；未声明不变）
- [x] WP-C 读面投影 + 注册/更新写面 + 存储往返 + OpenAPI 重生成 + TS 类型镜像
- [x] WP-D 示例配置/schema/文档对齐 + 用例
- [x] WP-E 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
$ python -m pytest tests/api/test_tool_provider_endpoint_binding.py -q
7 passed
$ python -m pytest tests/adapters/sqlite -q
97 passed（含端点声明往返 + 旧行解码为未声明）
$ python -m pytest tests/api -q
380 passed
$ python -m pytest tests/contracts tests/loaders -q
398 passed, 56 skipped
$ python -B tools/gen_openapi.py
wrote docs/api/openapi.m13.json (210373 chars)   # +66 行
$ npx tsc -p apps/web/tsconfig.json --noEmit
（空输出）
$ python -m mypy <5 个改动模块>
Success: no issues found in 5 source files
$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks
```

## 随本轮入库的 cycle 9 红项更正

CI run **35115260874**（cycle 9 收口 `cb61f41`）中 `quality-ubuntu-latest` 判红：
cycle 9 的**负载型反证**在 2 vCPU runner 上复现不出竞态（本地 8+ 核每次 10~20/96，
CI 0/288）。确定性做法经实验不成立（拿住游标 + 另线程写提交不触发：竞态需要两个线程
**同时**在 sqlite3 的 C 调用里）。处置：反证换成**结构判据**（读结果是否在锁内取尽），
负载型复现器降级为记录；细节见 RECHECK-071「更正」段与 RECHECK-072 的同名小节。

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：derive 时先全仓 grep 确认"零消费面"，
  并定位到唯一现实用法是**误用**（示例配置把凭据名写进端点位）。
  范围刻意收窄成"执法 + 可见 + 不泄漏"，把"URL 注入 adapter"留给下一轮，
  避免把 composition 级重建塞进本轮。
- 2026-09-16 WP-A/B/C/D 完成：解析、门槛、读面/写面/存储贯通、配置与文档对齐、
  7 条新用例全绿；期间发现 `ProviderRegistration.spec()` 会把 `endpoint_env` **丢掉**
  （同一缺陷的另一半），一并在本轮补齐。
- 2026-09-16 DONE：全量门禁通过（m0 **PASS: profile=m0; 23 deterministic checks**，
  定向 **97 + 380 + 398** passed，ruff/format/mypy 干净，OpenAPI 已重生成），
  记录落盘（RECHECK-072 PASS_WITH_WARNINGS + MEM-047 + GOAL cycle 10 记账 + ALL_PLAN），
  并随本轮入库 cycle 9 的 CI 红项更正。

## 影响报告

- **Domain/API/schema**：`ToolProviderSpec` 字段语义**不变**（只是终于有人消费）；
  `ProviderRegistration` 新增 `endpoint_env`（端点**声明**，不是端点值）；
  schema 增 description；注册写面 DTO 接受 `endpoint_env`；注册读面 DTO 新增
  `endpoint_binding`；OpenAPI 已重生成，TS 类型已镜像。
- **安全/凭据**：端点值 env-only + 只暴露 `sha256` 指纹；**不**新增凭据通道，
  凭据仍走 `CredentialResolver`（本模块不解析、不转发密钥，也不读文件）。
- **兼容性/迁移风险**：声明了 `endpoint_env` 而环境变量未设置的部署，其 provider
  健康状态会从"不报错"变成 UNKNOWN（有意的诚实化，已写进 schema 与文档）；
  旧存储行解码为"未声明"，行为与从前一致。
- **可观测性**：健康 detail 点名环境变量（名字不是秘密），不记值。
- **下一项任务**：把解析出的端点注入 adapter 实例（按 spec 重建 provider）；
  或补 `ToolProviderSpec` 的 `credential_ref` 表达面。

## 已知风险

- **门槛会让"声明了但没配"的 provider 变红**：这正是目的；示例配置已先修好，
  避免开箱即红。
- **digest 不是可观测的端点**：读面看到的是"绑定了 / 没绑定 + 指纹"；
  对可猜测的 URL 存在"确认猜测"的理论空间（取舍已写进模块 docstring）。
- **仍未做到"用解析出的端点"**：adapter 侧仍用构造时注入的 spec（见口径 5）。
- **`ProviderRegistration.spec()` 重建仍有边界**：信任级别由状态推导（既有口径），
  端点声明随实体存储；本轮未把 `credential_ref` 纳入注册面。
