---
id: MEM-20260915-049
title: 状态判定要的是"在不在"，不是"值是什么"——给 Port 加 has() 而不是偷偷 resolve()
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-074-provider-credential-binding.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-074-provider-credential-binding.md
supersedes: []
tags:
  - credentials
  - ports-and-adapters
  - supply-chain
  - tool-provider
  - presence-check
---

# 状态判定要的是"在不在"，不是"值是什么"

## 做了什么

`ToolProviderSpec` 此前**无法表达**"这个 provider 需要哪个凭据"——要求只活在 adapter
的构造参数里（`adapters/mcp/provider.py` 的 streamable_http 构造期就要求 `credential_ref`，
不满足直接 `raise`），注册面写不了、读面看不见、健康探测也从不问。本轮把它接成
真实能力（与 [[MEM-20260915-047]] 的 `endpoint_env` 同形）：

```text
声明              ToolProviderSpec.credential_ref / ProviderRegistration.credential_ref
                  + spec() 携带 + SQLite 往返（旧行 ⇒ 未声明）+ 注册/更新写面
存在性判定        CredentialResolver.has(ref)  ← 新增 Port 成员（全实现补齐）
四态              NOT_DECLARED | ABSENT | PRESENT | UNCHECKED（检查本身不可用时不猜）
执法              probe_provider_spec：声明了但解析不到 ⇒ 不探测、UNKNOWN、点名引用
可见 + 不泄漏     注册读面 DTO.credential_binding（状态 / 引用名 / present，无值）
```

**字段语义定为"声明即必需"**：写了就是"没有它这个 provider 不可用"。因此**可选**凭据
不声明——NCBI E-utilities 无 key 也能用（只是从 10 req/s 降到 3 req/s），它的
`credential_ref` 是适配器构造参数，示例配置**不**给它声明（声明了会把可用 provider
误判为不可用）。

## 为什么这样做

1. **不要为了状态判定去取值**。最省事的写法是"试着 `resolve()`，成功就是在场"——那会
   把明文凭据物化进内存、进得了异常栈/日志/repr 的机会面，而调用方其实只要一个布尔。
   正确做法是让 Port 多一个**只回答布尔**的能力：`has()` 为真 ⇔ `resolve()` 会成功。
   本仓 `RegistryCredentialResolver.has` 早就存在但**没有任何消费者**（死代码），
   本轮它第一次被接上，语义同时收紧为"可解析"（原实现把"键存在但值为空"也算在场，
   与 `resolve` 的行为不一致）。
2. **Port 变更由实现补齐，不靠鸭子类型**。`has` 加进 `CredentialResolver` 后，
   mypy 立刻列出 6 个结构上不再满足协议的老替身（`tests/` 下 5 个文件）——
   这类"编译期就能发现的漏实现"正是把能力放进 Port 而不是 `getattr` 兜底的价值。
3. **不猜**。存在性检查自己抛错时返回 `UNCHECKED` 而不是 `ABSENT`：读面显示"检查不了"，
   探测按不可证明收敛——把"不知道"和"不在"分开，与 [[MEM-20260915-044]] 同族口径。
4. **门槛挂在声明上**（与 `endpoint_env` 同一哲学，但**故意有一处不对称**）：
   端点门槛跳过 NATIVE（NATIVE 没有外部端点可解析），凭据门槛对所有 kind 成立
   ——"声明的必需凭据不在"是凭据事实，与传输形态无关。

## 怎么做与复现

```bash
python -m pytest tests/api/test_tool_provider_credential_binding.py -q   # 8 passed
python -m pytest tests/adapters/sqlite/test_tool_provider_registry_store.py -q
python -m pytest tests/contracts/test_ports_semantics.py -q              # has ⇔ resolve
```

判定"只查存在性"是**可执行**的：用例里的替身 `resolve()` 一被调用就
`raise AssertionError`，探测与投影路径若偷偷取值立刻红——口径不靠人读代码守。

改凭据面时的检查清单：① 判定只调 `has`，永不 `resolve`；② 读面只有状态/引用名/布尔；
③ 值不进 DTO/detail/repr/异常/存储；④ 未声明的 provider 行为不变；⑤ 旧行解码为"未声明"；
⑥ `has` 为真 ⇔ `resolve` 成功（两个方向都要钉）。

## 适用边界（踩过的坑）

- **声明即必需 ⇒ 可选凭据别声明**：这是本轮最容易误用的点（把"可选"写成"必需"会让
  可用 provider 判红）。示例配置用注释钉住了 NCBI 这个具体例子。
- **PATCH 清不掉声明**：更新 DTO 用 `exclude_none=True`，`credential_ref: null` 被当作
  "没提供"（与 `endpoint_env` 同一既有行为）——想撤销声明要改成非空值再改回。
- **还没有"用上凭据"这一步**：本轮的凭据仍由 composition 在构造 adapter 时注入，
  spec 里的声明只做准入与可见；"按声明给 adapter 接线"是下一轮候选。
- **`has` 只回答调用方已经持有的 ref**，不提供枚举能力——不存在"遍历凭据"的口子。
- 相邻缺口：`ToolProviderRegistration` 的凭据声明目前**不参与** preflight 的
  `TOOL_HEALTH_UNPROVEN` 之外的判据（健康是警示不阻断，见既有口径）。

## 来源

- PLAN-20260915-074 / RECHECK-20260915-074（GOAL-20260915-003 cycle 11，续期后首轮）。
- 相关：[[MEM-20260915-047]]（声明了却没人消费的字段等于谎言）、
  [[MEM-20260915-044]]（没观测到 ≠ 没有变化）。
