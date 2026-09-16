---
id: MEM-20260915-047
title: 声明了却没人消费的配置字段等于谎言；要么接线（执法+可见），要么删掉
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-072-provider-endpoint-binding.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-072-provider-endpoint-binding.md
supersedes: []
tags:
  - configuration
  - supply-chain
  - tool-provider
  - honesty
  - env-only
---

# 声明了却没人消费的配置字段等于谎言

## 做了什么

`ToolProviderSpec.endpoint_env` 在域、schema、YAML 装载器里都存在，但**全仓零消费者**：
唯一构造 `McpConnectionSpec` 的地方用的是构造时注入的规格。后果是配置作者写下的
"这个 provider 的端点来自环境变量 X"既不被执行也不被看见——示例配置甚至写了
`endpoint_env: NCBI_API_KEY`（字段名说端点、值是**凭据名**），没有任何东西报错。

本轮把它接成真实能力：

```text
解析（env-only）  services/api/tool_provider_endpoints.py
                  NOT_DECLARED | ENV_UNSET | BOUND（BOUND 才带 sha256 指纹）
执法              probe_provider_spec：声明了但未设置 ⇒ 不探测、UNKNOWN、点名变量
可见 + 不泄漏     注册面 DTO.endpoint_binding（状态 / 变量名 / 指纹，无端点明文）
贯通              域实体字段 + spec() 重建 + SQLite 往返（旧行 ⇒ 未声明）+ 注册/更新 DTO
```

## 为什么这样做

1. **没有消费者的字段是"配置幻觉"**：它给运维一个"我配了"的错觉，而系统行为完全不变；
   更糟的是**写错也没有反馈**（凭据名写进端点位，一路静默）。
2. **接线的两个动作缺一不可**：只做"可见"（塞进 DTO）仍是装饰；只做"执法"（不设置就
   判红）则运维看不到为什么红。本轮两者都做，并且**门槛挂在声明上**——
   没声明 `endpoint_env` 的 provider 行为一字不变（用同一 fixture 去掉声明即可证明）。
3. **env-only + 只暴露指纹**：端点可能含内网主机名或带 token 的查询串，所以读面只给
   状态、变量名与 `sha256` 指纹；凭据一律不走这里（仍只经 `CredentialResolver`）。
4. **旧数据按"未声明"解码**，不补假值——与 [[MEM-20260915-044]] 同族口径：
   没观测到 ≠ 没有。

## 怎么做与复现

```bash
python -m pytest tests/api/test_tool_provider_endpoint_binding.py -q   # 7 passed
python -m pytest tests/adapters/sqlite/test_tool_provider_registry_store.py -q
# 三态 + 文件里的同名值不算数 + 明文不泄漏 + 门槛挂在声明上 + 示例配置不带凭据名
```

改这个字段时的检查清单：① 解析只在进程边界（`os.environ`）；② 读面只出现状态/变量名/指纹；
③ 未设置时的健康状态必须是 UNKNOWN 且**点名变量**；④ 未声明的 provider 行为不变；
⑤ 旧行解码为"未声明"。

## 适用边界（踩过的坑）

- **本轮只到"准入 + 可见"**：adapter 仍用构造时的连接规格，端点尚未真正由配置驱动
  （要按 spec 重建 provider 实例）。
- **会让"声明了但没配"的部署变红**：这是有意的诚实化，必须写进 schema description 与文档，
  否则会被读成回归。
- **指纹的取舍**：读面看不到端点明文 ⇒ 运维要知道具体值得查环境变量本身；
  对可猜测的 URL，指纹存在"确认猜测"的理论空间。
- **示例命名检查是定点回归钉子，不是通用门禁**：只覆盖随仓库发布的示例配置，
  避免用启发式规则误伤合法命名。
- 相邻缺口：`ToolProviderSpec` 无法表达 `credential_ref`（凭据绑定面）。

## 来源

- PLAN-20260915-072 / RECHECK-20260915-072（GOAL-20260915-003 cycle 10）。
- 相关：[[MEM-20260915-044]]（漂移是状态不是事件）、
  [[MEM-20260915-046]]（语句级串行不等于读原子——同族"把语义边界写清楚"）。
