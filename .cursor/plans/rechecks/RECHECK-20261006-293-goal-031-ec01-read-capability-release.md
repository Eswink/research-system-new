---
id: RECHECK-20261006-293
slug: goal-031-ec01-read-capability-release
title: 复检：GOAL-031 EC-01 —— 放行面扩容（6 条只读能力逐条放行 + 三条新判据 + 两向反证 + 实跑使用）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-06
updated_at: 2026-10-06
plan_id: PLAN-20261006-293
reviewer: root-agent
parent_goal: GOAL-20261006-031
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/application/preflight
    tests/application/test_m2_audit.py tests/adapters/canonical/test_run_read_onboarding.py
    tests/adapters/openhands/test_session_tool_reaches_executor.py
    tests/e2e/test_granted_read_capabilities_used_in_a_run.py -q ⇒ 93 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters
    tests/architecture tests/loaders -q ⇒ 1607 passed / 4 skipped
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py -q
    ⇒ 1112 passed
  - >-
    as-is m0（独占、仓库 .venv、canonical DSN pin、不接管道）
    ⇒ `PASS: profile=m0; 23 deterministic checks`（FAILED 0 / PASS 24 行含 1 条计数外）
owners:
  - root-agent
---

# RECHECK-20261006-293 — GOAL-031 EC-01（放行面扩容）

## 结论

**PASS_WITH_WARNINGS**。EC-01 的五半（放行 / 镜像同步 / 三条新判据 / 两向反证 / 实跑使用）
**实测到场**；同步集四条既有钉定值按授权**重新定基**并逐条附「强度未降」自证；`deny` 面
**字节级零改动**（`sha256` 前后相等，实测）。两处 WARN 如实登记（见下）。

## 检查结果

| EC-01 要求 | 判据 / 读数 | 实测 |
| --- | --- | --- |
| (a) 6 条只读能力逐条放行、scope `project` | `test_release_expansion_is_read_only.py` 的扩集 + scope 断言 | 逐条在场；扩集 == 声明集（多/少都判红） |
| (b) 镜像表同轮同步、既有镜像判据未改且绿 | `test_m2_audit.py::test_policy_scope_mapping_matches_policy_yaml` | 绿；该判据**逐字节未改**（`git diff` 零命中） |
| (c)① 新增放行项逐条只读 | 词表成员 + 只读后缀 + provider `effect_class` 三谓词 | 6 条全过；受判面 = **策略面实算的扩集**（非 `_RELEASED` 写法） |
| (c)② `deny` + `require_approval` 零改动 | 集合逐条 + 段正文 LF 归一化 `sha256` 两道门 | `bf04fa4e…` 前后**相等**（工作树 vs `HEAD`） |
| (c)③ `default_effect` 仍 `DENY` | 文件逐字 + 真实求值器对未放行能力求值 | `DENY` + `used default policy effect` |
| (d)① 删一条放行 ⇒ run 被拒且点名 | run 面（终态 + 代号逐字）+ preflight 面（能力名逐字） | `FAILED` + `preflight failed: POLICY_DENIED`；`policy denied capability budget.read: used default policy effect` |
| (d)② 非只读能力塞进放行 ⇒ 判红 | 同一谓词（合成清单 + **真实 allow 面注入**） | 两形态都判红；注入臂在全绿 14 条下**曾是假绿**（见 W-1） |
| (e) 实跑 ≥3 条真的被用 | 调用证据（`tool_refs` 逐条）+ 下游消费证据（返回内容含上游 id） | 3 条调用（`run.read`/`budget.read`/`claim.read`）+ 2 条上游证据被 2 个下游各消费一次；`SUCCEEDED` |

## 同步集（被授权状态变化移动的既有钉定值，逐条自证强度未降）

| # | 判据 | before → after | 强度自证 |
| --- | --- | --- | --- |
| 1 | `POLICY_SURFACE_AUDIT.md` 差集表 | 35 行 → 29 行；该登记 15 → 9；交集 9 → 15 | 输入登记面（`expected_state` 的**输入**），机械判据 `test_policy_surface_difference_set` 未改一字 |
| 2 | `EXPECTED_REGISTERED` | 15 → 9 | **精确计数谓词形态不变**；成类禁止由同文件其余三条断言（逐条命名 / 无通配 / 无段前缀）继续钉住 |
| 3 | `_REGISTERED_NOT_GRANTED` | `claim.read` → `citation.inspect` | **三态归属谓词不变**；新示例仍是「provider 目录里声明、`policy.yaml` 里无 allow」的同一形态 |
| 4 | `test_run_read_onboarding` 未放行断言 | `DENY` + `used default policy effect` → `ALLOW` + `matched allow rule` | 翻转**双向保留**：目录声明侧断言逐字未动，另加一条 scope 断言（只 3 个 test 名变，无删除） |

**任何断言形态/强度变化、skip、删除**：零命中（见下）。

## 按压（三处，逐字节复原）

1. **判据自缺口（本轮抓到，重要）**：只读面判据初版只校验写死的 `_RELEASED` 清单 ⇒ 把
   `workspace.delete` 插进**真实 `allow` 段**后 14 条断言**全绿**。修法：从**文件**算扩集
   （`allow − 建档基线`）并与声明集相等断言 ⇒ 再按压即判红，且另加一条**
   在内存副本上注入**的用例（产品文件零改动）。
2. **两向反证按压**（判词原文归档 `.cursor/plans/goals/evidence/GOAL-20261006-031-ec01-refutation-verdicts.txt`）：
   `workspace.delete: 末段不是只读后缀 ('read', 'inspect', 'validate')`；扩集注入后
   `['budget.read', …, 'workspace.delete']`；删掉放行后求值器 `DENY: used default policy effect`；
   preflight `[POLICY_DENIED] phase:probe: policy denied capability budget.read: …`。
3. **run 级反证按压**：删掉 `budget.read` 放行 ⇒ 同一 run 判 `FAILED`，判词
   `preflight failed: POLICY_DENIED`；反面对照（放行在场）同一读数 `SUCCEEDED` 且无该代号。

## 复检发现（W-NN，如实登记）

- **`W-1`｜判据初版的受判面是写法清单（自我掩蔽形态）** —— 与 `MEM-20260922-160` 同族，
  出现在**本轮新判据**上：只校验 `_RELEASED` 时，「额外塞进一条非只读能力」在构造上不可见。
  **本轮已修**（扩集从文件算 + 注入臂），但它说明：**新判据第一版通过 ≠ 判据咬得住**，
  每条新判据都必须按压一次才能记入证据。归档进 `MEM`（见 GOAL 的 `memory_entries` 计划）。
- **`W-2`｜run 级失败消息**只带 finding **代号**（`preflight failed: POLICY_DENIED`），
  **不**逐字点名能力；逐能力点名在 preflight 报告面（`policy denied capability {cap} …`）。
  本轮判据**两个面都断言**（只读一个都会漏掉一半），但这条口径**没有**产品级统一
  —— 若将来要求 run 级消息也点名，属**改产品行为**（不在本 GOAL 授权内），登记为残余。
- **`W-3`｜`citation.inspect` 成为新的「已注册未放行」示例**：它与三态归属表的绑定是
  **示例名字**级的（形态不变）。若将来它也被放行，该示例必须换名——判据会**立刻判红**
  （不是静默过期），这正是该判据的预期行为。

## m0 首跑的四红（逐条归因，全部处置完毕）

cycle 1 本地 m0（as-is、独占、仓库 `.venv`、canonical DSN pin、不接管道）首跑 **4 红**，
逐条归因如下 —— **没有一条靠改判据/降强度消红**：

| # | check | 归因 | 处置 |
| --- | --- | --- | --- |
| 1 | `python/product-lint` | **真缺陷（我的）**：`tests/e2e/granted_reads_support.py:63` 的 import 块未排序（`Digest, ID` → `ID, Digest`） | `ruff check --fix`（1 file changed） |
| 2 | `python/format-check` | **真缺陷（我的）**：`test_release_expansion_is_read_only.py` 与 `test_granted_read_capabilities_used_in_a_run.py` 各一处行宽格式 | `ruff format`（2 files reformatted） |
| 3 | `framework/validate_bundle` | **真缺陷（我的）**：新协议的 `version:` 字段写了过期的次版本字面量，命中 bundle 校验器的**旧项目版本引用**规则（该规则按正则匹配旧项目版本的次版本号） | 协议版本改 `0.1.0`（与同族新协议 `capabilities_used_in_a_run_v1` / `scientific_action_depth_v1` 一致） |
| 4 | `framework/run_cursor_framework_evals` | **已知 flake**（`MEM: evolution-state-winerror5-flake`）：`evolution_gate.py` 写 `evolution_state.json` 时 `PermissionError WinError 5`（并发/残留 tmp 类） | 按既有配方**单跑取证 → 独占重跑**；**不改 check、不查产品代码**。**单跑取证**：`run_cursor_framework_evals.py` 单独运行 ⇒ `FRAMEWORK EVAL PASS` / exit 0；旁证：`.cursor/runtime/evolution_state.json` 的 mtime（`05:24` 本地）落在 m0 运行窗口内 = 并发写者 ⇒ 与本 flake 的已知形态一致 |

**第二次 m0 的读数（fix 之后）**：`python/product-lint` / `python/format-check` **转绿**
（三处真缺陷已修）；余 2 红 = ① `framework/validate_bundle` —— **本复检记录自身**引用了
过期次版本字面量（记录面也在扫描面内，与 `MEM: record-face-gates-catch-your-own-record`
同族），改述后单独复跑 `validate_bundle.py` ⇒ **验证通过**；② `framework/run_cursor_framework_evals`
—— 与首跑**同一签名**（`evolution_state.json` 的 `WinError 5`），单跑取证 PASS ⇒ 按 flake
配方处置。第三次 m0（独占，记录定稿后）的终局读数见本文件「复检验证路径」与 GOAL 迭代日志。

**终局 m0（独占、**本批记录定稿之后**、仓库 `.venv`、canonical DSN pin、不接管道）**：
`FAILED [` **0** / `PASS [` **24**（23 条计数内 + `release-assets-immutable`）/ 终局行
`PASS: profile=m0; 23 deterministic checks`；零 python 进程残留。（`PASS [` 行数为 24 属
既有口径：**终局行才是判据**。）该终局行是在**本文件与 PLAN / GOAL 的全部记录写入之后**
取得的读数 —— 其后到提交之间**不再有任何树内改动**（提交不改内容）。

**为什么前三红本地定向套件没抓到**：① 我只跑了受判面的 pytest，没跑 `ruff check` / `ruff format`
（它们是**另外两道门**，承 `MEM: m0-profile-roots-and-count` 的同一教训）；② `validate_bundle`
的旧版本规则扫的是**全仓字面量**，新协议文件的 `version:` 字段正是它的扫描面 —— 这属于
「新增资产要过的不止是它自己的判据」。⇒ 已把三者并入本轮 fix，并在 m0 复跑中验证。

## 未覆盖范围（原样保留）

EC-01 只覆盖**3 条**新放行能力被真的使用（`run.read` / `budget.read` / `claim.read`）；
`deliverable.read` / `experiment.read` / `experiment_plan.read` 的**放行面**逐条受判，但
**未被一次 run 使用**（协议不构造交付物 / 实验事实，见 GOAL 的 `W31-1`）。
读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 /
D 组审批通道未接通 / exactly-once 未实现（**明确否认**；口径只能是 at-least-once +
idempotency + deduplication）。**不得**据此宣称项目安全。
