---
id: MEM-20260915-036
title: Tool Provider 注册：信任级别由状态推导，pin 是硬门，目录合并即消费
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.90
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-060-tool-provider-registration-and-governance-write-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-060-tool-provider-registration-and-governance-write-surface.md
supersedes: []
tags:
  - tool-provider
  - supply-chain
  - registration
  - trust-level
  - write-surface
---

# Tool Provider 注册治理：怎么让"可写"不等于"可自我授权"

## 做了什么

`ops/integrations` 的 G15 治理写面：`GET/POST /tool-provider-registrations`、
`PATCH /tool-provider-registrations/{id}`、`/{id}/approve`、`/{id}/revoke`、
`/{id}/health-check`。域是 `packages/domain/tool_registry.py` 的 `ProviderRegistration`
（PENDING → ACTIVE → REVOKED，REVOKED 终态），持久面 `adapters/sqlite/tool_provider_registry.py`
单表 `tool_provider_registrations`。

## 为什么这样做

供应链治理面一旦可写，就同时打开了三条滥用路径，本轮的三个"硬门"分别堵一条：

1. **自我授权**：用户不能声明自己带来的 provider 是 `BUILT_IN`/`VERIFIED`。
   因此 `trust_level` **不进入请求 DTO**，而是 `ProviderRegistration.spec()` 用
   `trust_for(state)` 推导：PENDING→UNTRUSTED、ACTIVE→USER_APPROVED、REVOKED→REVOKED。
   接口层面就没有"传入信任级别"这个字段。
2. **未 pin 就可用**：AGENTS.md §9「默认 deny：unpinned plugin」被落成构造期校验——
   `pinned_revision` 必须通过 `Digest.parse`（`sha256:<64hex>`），tag/分支名这类可漂移
   字面量 422。并且这个 pin 会作为 `tool_pack_digests[provider_id]` 合入目录，
   于是 `preflight._is_pinned_digest` 通过 = "用户 pin 的那份就是 preflight 看到的那份"
   （不新造第二套 pin 语义）。
3. **影子覆盖**：注册 id 若已被 examples 契约占用（`openhands_workspace` 等）→ 409；
   重复注册同一 id → 409，不改写既有行。

## 怎么做与复现

消费关系写在一个地方：`services/api/catalog_merge._merge_registered_providers()` 只把
`state == ACTIVE` 的注册合并进 `CatalogSnapshot.tool_providers` 与 `tool_pack_digests`。
下游全是**既有链路**，无需新造：`protocol_compile.requirements.tool_requirements()` 派生
`provider_ids` → `preflight.checks.check_tools()` 判可用性与 pin →
`tool_plane.resolver` 按 trust/health 过滤 → `GET /tool-providers` 目录。

证明"被消费"用的是**同一份输入在不同状态下结论不同**：用一个 examples 三个 provider
都不声明的能力（`dataset.read`），对同一份草稿协议跑 `POST /projects/{id}/preflight`：

```
未注册 / PENDING → TOOL_UNAVAILABLE
ACTIVE           → TOOL_UNAVAILABLE 消失、无 SUPPLY_CHAIN_UNPINNED、出现 TOOL_HEALTH_UNPROVEN
REVOKED          → TOOL_UNAVAILABLE 回归
```

健康复核与读面**共用同一探测体**（`preflight_support.probe_provider_spec()`），
否则会出现"复核说健康、目录说不可证明"的两套真相。

```
python -m pytest tests/api/test_tool_registrations_api.py -q    # 18 passed
cd apps/web && pnpm exec playwright test registry-write.spec.ts          # 5 passed（stub）
cd apps/web && pnpm run test:e2e:live                                    # 30 passed（含 2 条真实注册链）
```

## 适用边界

- `capabilities` 只校验非空与长度，**不校验取值域**；能力名由 provider 声明，
  不是授权边界——放行仍由 policy 与 resolver 决定。
- pin 只校验**形态**，控制面不取 provider 内容，无法自证 digest 与实际交付物一致；
  真正的供应链证明在仍未提供的 ToolPack install/approve 面。
- 健康复核不落 `observed_schema_digest`，因此**看不出 schema 漂移**。
- provider 凭据绑定无写面（凭据域独立，不经控制面转发）。
- 目录只含 ACTIVE + examples 契约：`GET /tool-providers` 的 `management_available`
  现在表示"注册表是否装配"，不再是"治理面是否缺失"。
- live 装配（`run_fixtures._run_ready_sqlite_stores`）已带注册表；需要"未装配"语义的
  用例必须显式置 `None`（`test_tool_registrations_api.py` 有先例）。

## 来源

- PLAN-20260915-060 / RECHECK-20260915-060（GOAL-20260915-002 cycle 6 / EC-05）。
- 相关：[[MEM-20260915-035]]（同一条"写面必须被消费"的判据，这是它的第二个实例）、
  [[MEM-20260915-034]]（digest/adressed 读取面的同族思路：pin 即内容寻址身份）。
