---
id: PLAN-20260920-125
slug: credential-lifecycle-runbook
title: 凭据生命周期落成同源判据：注入 / 轮换 / 撤销 / 可弃用额度按「构造时快照」的实测语义写清楚并钉住（EC-05）
status: DONE
created_at: 2026-09-21
updated_at: 2026-09-21
parent_goal: GOAL-20260920-009
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-009 cycle 5 = EC-05（凭据生命周期 runbook）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (2) 条凭据纪律与第 (5) 条（把 `.env` 注入 / `set -a; . ./.env; set +a` / 轮换 / 撤销写成同源判据，含「免费可弃用额度」说明）。**本 PLAN 不发起任何真实调用**：全部判据离线，只用**虚构值**测解析器语义，**不读取、不打印、不写入**真实凭据值；不改 Policy/门禁/断言强度、不新增依赖、不改 pin、不把凭据写进 CI。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-125-credential-lifecycle-runbook.md
memory_entries: MEM-099
---

# PLAN-20260920-125 — 凭据生命周期落成同源判据（GOAL-009 cycle 5 = EC-05）

## 目标

把凭据的**注入 / 轮换 / 撤销 / 可弃用额度处置**四件事写成**同源判据**：

1. **注入**：`set -a; . ./.env; set +a`（POSIX 形态）+ 「只经环境变量」的纪律；
   写明本机由**导入栈的 litellm `load_dotenv`** 自动加载（跑 pytest 无需手工导出），
   但显式导出是更可移植的形态。
2. **轮换**：生效边界**按实测写**——两个解析器都在**构造时**拷贝 `os.environ`，
   所以「同一进程内改环境变量即生效」**不成立**；**已构造的实例是快照**，只有**新构造**的实例看到新值。
3. **撤销**：清空/删除来源 ⇒ **新构造**的解析器 `has()` 为 `False` ⇒ `evaluate_live_run_gate`
   **fail-closed 关闭**且理由**点名**凭据不可解析。
4. **可弃用额度**：如实写明本 key 为**免费可弃用额度**（泄露风险由用户明示接受），
   **以及**「这**不**降低凭据纪律」——值仍不得落任何 tracked 文件 / DB / 记录 / 日志 / 回显。

## 先探明再动手（实测，2026-09-21）

用**虚构值**（`fabricated-probe-value`，非真实凭据）实测六个命题：

| # | 命题 | 实测 |
| --- | --- | --- |
| M-1 | 来源存在 ⇒ `EnvCredentialResolver().has(ref)` | **True** |
| M-2 | **撤销来源后，已构造的同一实例** | **True**（快照 ⇒ **不**跟随） |
| M-3 | 撤销来源后，**新构造**的实例 | **False** |
| M-4 | 已 `register()` 的注册表面，撤销环境变量后 | **True**（注册表命中优先于环境快照） |
| M-5 | 轮换来源后，**已构造的同一实例** | **True**（仍是旧快照） |
| M-6 | 轮换来源后，**新构造**的实例 | **True** |

⇒ **GOAL-009 的 EC-05 判定细则原文（「`EnvCredentialResolver` 每次读 `os.environ` ⇒ 同一进程内
改 `os.environ` 即生效」）是错的**，已按 M-2/M-3 更正为「构造时快照」。

**其它既有事实**（只读）：

- 既有 runbook §2 已有两套面（环境变量面 / API 注册面）与「轮换 → 重启 API」；
  §3 已有「注册表活在进程内、重启需重输」；§4 有 `RESEARCHOS_AGENT_RUNTIME` 的三态表。
  **本 PLAN 不重写这些**，只补齐 EC-05 要的四件事并让它们**可判**。
- `EnvCredentialResolver.has` 是 `bool(self._environment.get(ref, ""))` ⇒ **空串 == 不可解析**
  （与 `test_ec04_live_gate_offline.py` 的既有断言一致）。
- 「明文凭据不进仓库/记录/日志」由 `tools/credential_audit.py` 四面扫描把守（既有）。

## 口径（先写死）

- **判据离线**：全部用**虚构值**驱动解析器与门，**不**读真实 `.env` 的值、**不**发起调用。
- **写实测、不写假设**：轮换/撤销的语义一律以 M-1…M-6 为准；**不得**为了迁就原假设而写判据。
- **同源**：文档里的仓库路径 / 变量名 / pytest 目标必须**可解析**（沿用既有 runbook 判据形态）。

## 验收条件

- **AC-1 四件事有明文**：runbook 里能按**固定标签**读出注入 / 轮换 / 撤销 / 可弃用额度四条，
  且 `set -a; . ./.env; set +a` 的 POSIX 形态与实际命令在场。
- **AC-2 轮换边界可判**：判据实测「**已构造的实例是快照**」（撤销或轮换来源后仍报旧结论），
  并**配对**断言「**新构造**的实例看到新值」——两条一起才钉住「构造时快照」。
- **AC-3 撤销 fail-closed 可判**：撤销后 `evaluate_live_run_gate` 为 `open=False`，
  且理由**点名**凭据不可解析；并与「来源存在 ⇒ 门开」成对断言。
- **AC-4 注册表面边界可判**：`register()` 命中**优先于**环境快照 ⇒ 撤销环境变量**不**关该面的门，
  必须 `unregister()`——这一条**必须**判，否则 runbook 的撤销说明会被误读成「清空环境变量万能」。
- **AC-5 可弃用额度 + 纪律**：明文**同时**含「免费可弃用额度」与「**不**降低凭据纪律」两条，
  判据对两条**只判在场**（不判文笔）。
- **AC-6 本地门禁绿**：定向套件 + `make validate-all`（m0，CI 同形配置）+ 治理 `validate.py`。

## 实施清单

- [x] WP1 更正 GOAL 的 EC-05 判定细则（按 M-2/M-3 的实测）——**已在 derive 提交内**。
- [x] WP2 runbook 补四件事的明文（AC-1/5）。
- [x] WP3 同源判据 `tests/architecture/python/test_credential_lifecycle_same_source.py`（AC-1…AC-5）。
- [x] WP4 压判据（改坏一条 ⇒ RED；复原 ⇒ GREEN），两次输出留证。
- [x] WP5 本地验证（AC-6）→ RECHECK → DONE → ALL_PLAN → 回写 GOAL-009 → commit/push/CI。

## 证据

（执行时逐条填入。）

### WP1 GOAL 更正

已在 derive 提交内：EC-05 判定细则的「轮换」与「撤销」两条改写为**构造时快照**语义，
并写明注册表面命中优先于环境快照；实测表 M-1…M-6 记在本 PLAN。

### WP2 明文

`docs/integration/LIVE_MODEL_RUNBOOK.md` 新增 **§8 凭据生命周期**：四行固定标签表
（`| 注入 |` / `| 轮换 |` / `| 撤销 |` / `| 可弃用额度 |`）+ 三种构造方式的语义表 +
`set -a; . ./.env; set +a` 的 POSIX 形态逐字给出 + 「名字必须逐字一致」的大小写边界 +
撤销的两条边界 + 可弃用额度与纪律声明。**新增 59 行，0 删除**（§1–§7 未被触碰）。

### WP3 判据

`tests/architecture/python/test_live_credential_lifecycle_same_source.py`（新增，**20 个用例，全绿**）：

| 断言 | 用例 |
| --- | --- |
| 无参 `EnvCredentialResolver()`（生产路径）是**快照** | `test_the_production_resolver_keeps_its_snapshot` |
| **配对**：新构造的实例看到撤销 | `test_a_freshly_constructed_resolver_sees_the_revocation` |
| 传 `environment=` 的形态**按引用**持有（不是快照） | `test_an_injected_mapping_is_held_by_reference` |
| `RegistryCredentialResolver` 拷贝其映射 | `test_the_registry_resolver_copies_its_mapping` |
| 名字大小写：拷贝后是普通 dict（大小写敏感） | `test_the_lookup_is_case_sensitive_on_the_copied_mapping` |
| 来源在 ⇒ 门开；撤销 ⇒ 门关且**点名**；空串 ⇒ 门关 | `TestRevocationClosesTheGateFailClosed`（3 条） |
| 注册表面：`register()` 优先、`unregister()` 才关、未注册仍回退环境 | `TestTheRegistryFaceNeedsItsOwnRevocation`（3 条） |
| §8 四行在场 + 各行指向**它的**依据 + POSIX 形态 + 快照边界 + 注册表边界 + 额度与纪律 | `TestTheFourItemsAreWrittenDown`（8 条） |
| **行内**语义：「轮换」「撤销」两行必须含「新构造」 | `test_the_rotation_and_revocation_rows_carry_the_snapshot_semantics` |

与既有 `test_runbook_same_source.py` 同跑 ⇒ **30 passed in 1.26s**。

### WP4 压判据

**第一次压测暴露判据太松（本轮最有价值的发现）**：把 §8 的**撤销行**改写成
「清空或删除来源 ⇒ **每次调用**都读一次环境，所以立即生效」⇒ 判据**仍然全绿**——
因为当时只断言「§8 里出现过『快照』」，而 §8 别处还有这个词。
处置是**收紧判据**（`assert "新构造" in _row(label)`，逐行判），**不是**放过改写。

**第二次压测**（收紧后）：同一处改写 ⇒ **RED**：
`AssertionError: §8 的 '撤销' 行必须写明生效边界是「新构造」…`；复原 ⇒ **GREEN**（`30 passed`），
`git diff docs/integration/LIVE_MODEL_RUNBOOK.md` = `59 insertions, 0 deletions`。

**判据自己的返工（也如实登记）**：第一版把「快照」写成「传 `environment=` 的形态也是快照」，
实测**红了**（该形态**按引用**持有 ⇒ 看得到改动）⇒ 把语义按**构造方式**拆成三种，
并把「大小写敏感」这条也补成断言（第一版用小写名查环境变量，在 Windows 上直接红）。
两次返工都是**让判据更对**，没有放宽任何断言。

### WP5 本地验证

- 定向套件：本判据 **20 passed**；+ 既有 runbook 判据 **30 passed**；
  `ruff check` / `ruff format --check` / `mypy` 绿。
- 全量 m0（**CI 同形配置**）：第一轮 **`FAILED: 1 check(s): framework/validate=1`** ——
  治理 validator 报 `工程记忆来源不存在: MEM-20260920-099: …RECHECK-20260920-125-….md`
  （**引用先于记录**）。处置：**把 RECHECK 写出来**（记录先于引用），**不是**删来源字段或放宽 validator。
  `python/tests` 同轮 **4260 passed / 13 skipped**（无红）。复跑结果见 GOAL 迭代日志。
- 治理 `validate.py`：补齐记录后**绿**。


## 验收条件对照

| AC | 判据 | 结论 |
| --- | --- | --- |
| AC-1 四件事有明文 | §8 四行 + POSIX 形态 | ✅ 8 条在场断言 |
| AC-2 轮换边界可判 | 快照 + 配对（新实例看到新值），按**构造方式**分三种 | ✅ 4 条实测（判据两处返工后） |
| AC-3 撤销 fail-closed 可判 | 撤销 ⇒ 门关且点名；与「来源在 ⇒ 门开」成对 | ✅ 3 条 |
| AC-4 注册表面边界可判 | `register()` 优先、`unregister()` 才关 | ✅ 3 条 |
| AC-5 可弃用额度 + 纪律 | 两句都在场 | ✅ 1 条 |
| AC-6 本地门禁绿 | 定向 + m0（CI 同形）+ 治理 | ✅ 30 passed；m0 首轮红在「引用先于记录」⇒ 补 RECHECK 后治理绿；`python/tests` 4260 passed / 13 skipped |

## 状态历史

- 2026-09-21 建档：`driver=client-goal / owner=root-agent`。承接 GOAL-009 cycle 5（EC-05）。
  **不发起任何真实调用**；只用虚构值测语义，不触碰真实凭据值。
- 2026-09-21 **DONE**：WP1→WP5 全部完成，AC-1…AC-6 全中。
  `RECHECK-20260920-125` = **PASS_WITH_WARNINGS**（W-1…W-6）。
  **未改任何门禁或断言强度**（第一次压测的处置是**收紧**判据）；
  **未读 / 未打印 / 未写入任何真实凭据值**（全部用虚构值）；**未新发真实调用**。

## 影响报告

**Domain / API / Schema**：**无变化**。不新增/修改域实体、DTO、路由或迁移；本 PLAN 只改
**文档**、新增**判据**，并更正 **GOAL 自己的**判定细则文本（不是产品行为）。

**安全 / 凭据**：**无新增信任面**，且**不读取真实凭据值**。判据用**虚构值**驱动解析器与门，
断言的是**布尔语义**。**默认 deny 姿态不放松**：不改 URL 策略、不改门、不改 Policy。

**兼容性 / 迁移风险**：无迁移。**风险**：判据若把「构造时快照」写成「每次读环境」，
会在**未来的合法重构**下误红 —— 处置是**按实测写**（M-1…M-6），并在文档里写明该语义是
**实现细节还是契约**：本 PLAN 把它当**契约**钉住（变更须同步改文档与判据）。

**上游版本影响**：无。不新增依赖、不改任何 pin。

**下一项任务**：WP2 明文 → WP3 判据 → WP4 压判据 → WP5 收口并回写 GOAL-009 的 EC-05。
