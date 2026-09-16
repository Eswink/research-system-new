---
id: RECHECK-20260915-074
plan_id: PLAN-20260915-074
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-003-cycle11
baseline_ref: e785672
checked_head: e785672+worktree
---

# RECHECK-20260915-074 — provider 凭据绑定（GOAL-003 cycle 11）

## 检查范围

PLAN-20260915-074 声称的交付面：`CredentialResolver.has` 作为 Port 成员与全部实现的
补齐、`ToolProviderSpec.credential_ref` / `ProviderRegistration.credential_ref` /
`spec()` / SQLite 往返（含旧行解码）、`services/api/tool_provider_credentials.py`
（四态判定 + 只读投影）、`services/api/preflight_support.py` 的凭据门槛、注册面
**写入 → 存储 → 读面**贯通（DTO + 路由 + OpenAPI 重生成 + TS 类型镜像）、
schema/示例配置/文档对齐，以及新增/补充的四个测试文件。

**未覆盖**（见告警 W-1）：按声明给 adapter 接线（凭据仍由 composition 构造参数注入）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 只查存在性，不物化明文（AC-02） | `test_binding_states_and_presence_only_lookup`：替身 `_PresenceOnlyResolver.resolve()` **一被调用就 `raise AssertionError`**，探测/投影路径全程只调 `has`（`has_calls == [ref]`）；未声明时**连 `has` 都不调**（门槛挂在声明上） | PASS |
| 四态判定与不猜（AC-02） | 同用例：`NOT_DECLARED` / `ABSENT` / `PRESENT` / 存在性检查抛错 ⇒ `UNCHECKED`；空白引用等同未声明；`missing_reason` 对三种非 PRESENT 状态各自给出点名引用的原因 | PASS |
| 读面字段自洽（AC-02） | `test_credential_binding_rejects_inconsistent_states`：只有 `PRESENT` 允许 `present=True`；`ABSENT` 不许带 `present=True`；`NOT_DECLARED` 不许带引用名；未知状态拒绝 | PASS |
| 不泄漏（AC-04） | `test_binding_projection_never_carries_the_secret`：绑定对象 / DTO / `model_dump()` / 原因文本四段字符串里都没有值；`test_registration_read_surface_carries_the_credential_binding` 在注册读面响应整体字符串里再查一次 | PASS |
| 执法（AC-03） | `test_declared_but_absent_credential_blocks_the_probe`：声明 + 解析不到 ⇒ 不探测、UNKNOWN、detail 点名引用且无 schema 指纹；**去掉声明** ⇒ 同一 fixture 回到原路径（HEALTHY）；凭据出现 ⇒ 回到正常探测；凭据边界抛错 ⇒ UNKNOWN（不伪装） | PASS |
| 与端点门槛的不对称是**有意的**且被钉住 | `test_credential_gate_applies_to_native_too`：NATIVE 未声明 ⇒ HEALTHY 且 detail 是 `NATIVE_PROBE_DETAIL`；NATIVE **声明了**且不在 ⇒ UNKNOWN 点名引用（凭据事实与传输形态无关） | PASS |
| 可见（AC-05） | `test_registration_read_surface_carries_the_credential_binding`：注册 → `ABSENT`；凭据出现 → **同一份注册**立刻 `PRESENT`；凭据消失 → 立刻回 `ABSENT`；未声明 → `NOT_DECLARED`；响应里无值 | PASS |
| 写面与读面同一事实（AC-03/05） | `test_health_check_writes_the_credential_gap_into_the_registration`：`POST …/health-check` 写回的 `last_health=UNKNOWN` + detail 点名引用，与读面 `credential_binding.state=ABSENT` 一致（禁止两套真相） | PASS |
| 存储往返与旧行（AC-01） | `test_credential_ref_round_trips_and_legacy_rows_stay_undeclared`：声明入库往返一致、**随 `spec()` 进入目录面**；抹掉键的历史行解码为 `None`；原「加字段前的老行」用例补一条 `credential_ref is None` | PASS |
| Port 契约（AC-02） | `tests/contracts/test_ports_semantics.py`：`has` 为真 ⇔ `resolve` 成功（两个方向）、`has` 的记录里没有值、`deny_scope` 后 `has` 为假且 `resolve` 抛 `InvalidInputError`；mypy 用协议检查抓出 6 处未补齐的老替身（`tests/` 下 5 个文件），全部补齐而**未放宽类型** | PASS |
| 配置对齐（AC-05） | `test_example_config_keeps_the_optional_ncbi_key_undeclared`：示例不给 `ncbi_eutils` 声明 `credential_ref`（**声明即必需**，而 NCBI 无 key 也能用——`tests/contracts/test_ncbi_provider_contract.py::test_no_credential_means_no_api_key_param` 钉着这一点）；示例里新增的参考形态是**注释**，未启用 | PASS |
| 定向套件（AC-06） | `tests/api` **422 passed**；`tests/adapters/sqlite` + `tests/loaders` + `tests/api` **525 passed**；`tests/contracts + tests/application` **955 passed / 57 skipped**；`tests/observability` **58 passed / 1 skipped**（canary 替身补齐 `has`） | PASS |
| 端到端（stub / live） | stub e2e **83 passed**（结构与像素基线均未变）；live e2e **36 passed**（+1：`live: 声明的必需凭据不在时如实 UNKNOWN`，真实 uvicorn + 真实 SQLite 上验证读面 `ABSENT` 与 health-check 写回一致） | PASS |
| 全量门禁 + 记录（AC-06） | 完整 m0 跑到 `framework/validate` 前全绿（`python/tests` = 全量 pytest、`typescript/web-*` 四项均 PASS）；`framework/validate` 的两条报错**都是本轮记录尚未落盘**（PLAN-074 未登记 ALL_PLAN、MEM-049 指向尚不存在的 RECHECK-074）——本文件与 ALL_PLAN 行落盘后框架档 8/8 复跑通过；ruff/format 干净、mypy **867 files clean** | PASS |

## 告警

- **W-1（还没"用"上凭据）**：本轮把 `credential_ref` 变成**准入条件 + 可见状态**，但
  凭据仍由 composition 在构造 adapter 时注入（`McpToolProvider(credential_ref=…)`、
  `NcbiEutilsProvider(credential_ref=…)`）。spec 里的声明与 adapter 的构造参数目前是
  **两处**，还没有"按声明接线"这一步——不要读成"凭据已由 spec 驱动"。
- **W-2（声明即必需是**语义**，会让误声明变红）**：把可选凭据写成必需声明，会让本来可用的
  provider 判 UNKNOWN。这是有意的（否则"必需"无从执行），已写进 schema description、
  示例配置注释与文档 §6.2；NCBI 这个具体例子被用例钉住。
- **W-3（`UNCHECKED` 是防御态）**：仓储内所有 resolver 的 `has` 都是全函数（不会抛），
  所以 `UNCHECKED` 在正常部署里不会出现；它的用途是"凭据边界故障时不把不知道说成不在"。
  读面多一个状态是这条诚实口径的代价。
- **W-4（PATCH 清不掉声明）**：更新 DTO 用 `exclude_none=True`，`credential_ref: null`
  被当作"没提供"（与 `endpoint_env` 既有行为一致）——撤销声明要改成非空值再改回。
  这是既有口径，本轮**没有**顺手改（改了会影响两个字段的语义，需要单独一轮）。
- **W-5（`has` 是新 Port 成员，第三方 resolver 需跟进）**：加进 `CredentialResolver`
  协议后，任何外部实现都要补 `has`（mypy 会报）。本仓 6 处实现已全部补齐，
  但这是一次**破坏性 Port 变更**，应写进给下游的说明。

## 结论

`ToolProviderSpec` 此前**无法表达**的"这个 provider 需要哪个凭据"，本轮被接成真实能力：
存在性判定只调 `has`（不物化明文，用例用会炸的 `resolve` 把这条口径变成可执行断言）、
声明即必需（解析不到 ⇒ 不探测、UNKNOWN、点名引用）、读面只有状态/引用名/布尔、
写入/存储（含旧行）/读面/OpenAPI/TS 全线打通，并有真实 HTTP 的 live 链佐证。
结果为 **PASS_WITH_WARNINGS**：W-1（还没按声明给 adapter 接线）如实标为下一轮候选，
W-2/W-3/W-4/W-5 是这条"存在性 + 声明即必需"路线的代价与边界。
