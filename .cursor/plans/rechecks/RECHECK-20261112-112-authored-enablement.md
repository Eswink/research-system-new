---
id: RECHECK-20261112-112
slug: authored-enablement
title: GOAL-112 复检 —— 实验生成级的启用面（只交付可启用的网）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-12
updated_at: 2026-11-12
plan_id: PLAN-20261112-112
parent_goal: GOAL-20261111-112
owners:
  - root-agent
verify_paths:
  - packages/application/experiments/constraint_table.py
  - packages/application/experiments/script_authority.py
  - packages/application/tool_plane/resolver.py
  - packages/application/preflight/policy_check.py
  - tests/application/experiments/test_constraint_table.py
  - tests/application/tool_plane/test_resolver_carries_constraints.py
  - tests/application/preflight/test_policy_check_reads_constraints.py
  - tests/application/experiments/test_authored_profile.py
---

# RECHECK-20261112-112

## 复检范围

GOAL-20261111-112 的六条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

| 面 | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- |
| 约束 | 同一张表的判定在**三个执行面**一致 | **不**宣称「所有执行面都读了约束」：只覆盖实测可达的三处 |
| `AUTHORED` | 具名安全 profile 作为唯一放行口 | **不**打开 `AUTHORED_ALLOWED_BY_DEFAULT`（仍 `False`） |
| 安全 | 无沙箱 / 越界路径 / 超时 / digest 不匹配各点名拒绝 | **不**宣称「沙箱不可逃逸」——本仓无此证据 |
| 生成级 | `script_source: authored` 的**声明面与闸门** | **不**宣称已跑过一次真实 `authored` 实验 |

## 检查结果

### EC-01 同一张约束表（PASS）

`experiments/constraint_table.py`：四键闭集、每键声明类型、`ENFORCED_KEYS`（三个）与
只过形状的第四键分开。**三处消费点都调它**：`script_authority.check_constraints`
（原分支改调表）、`tool_plane/resolver`（新接）、`preflight/policy_check`（新接）——
判据按**源码**断言三处引用同一模块，且判定里**没有**第二份 `isinstance` 链。

**一处必须如实写下的修正**：第四键 `requires_workspace_lease` 是
`examples/config/policy.yaml` 里**早已声明**的（全仓除该 YAML 外零命中）。我第一版把它
判成「未知键」⇒ 真实控制面 preflight 直接 **FAIL**（`policy_surface_consistency` 三条判据
当场红）。修法不是放宽判据，而是**把出厂文件里写着的键纳入闭集**：它过形状校验，
但**不在** `ENFORCED_KEYS` 里（执行语义需要「租约是否已持有」这个事实，实验边界拿不到）。

### EC-02 工具面读约束（PASS）

`CapabilityResolution` 新增 `constraints` 字段（缺省空映射 ⇒ 既有行为逐字不变）+
`constraint_keys` 读面属性。`ResolutionInput.capability_constraints` 传入声明；
形状错 ⇒ **findings 点名**且**原始声明仍可读**（不替调用方挑「合法子集」）。
判据 `test_resolver_carries_constraints.py` ⇒ **4 passed**。

### EC-03 preflight 读约束（PASS）

`ALLOW_WITH_CONSTRAINTS` 分支从「只把键名拼成一句话」改为**核验形状**：未知键 / 类型错
⇒ `POLICY_CONSTRAINTS_INVALID` finding 并点名。新增枚举成员（`PreflightFindingCode`）。
判据 `test_policy_check_reads_constraints.py` ⇒ **7 passed**（四种形状错误各一臂 + 零回归两臂）。

### EC-04 `authored` 声明 + 具名安全 profile（PASS）

- `script_source` 闭集 `shipped` / `authored`；**缺席 ⇒ `shipped`**（逐字回到今天）；
  非法取值**点名拒绝、不回落**（回落会把「模型说要用自己写的脚本」静默改写成「跑出厂脚本」）；
- `AUTHORED_SAFETY_PROFILE = "authored-experiments-v1"`：值必须**逐字相等**
  （`1` / `true` / 空 / 大小写不同都不算，与 `RESEARCHOS_LIVE_E2E` 同一条纪律）；
- **两道门**：`authored_allowed=True` **且** profile 在场才放行；缺一即点名拒（缺哪道可读）；
- **`AUTHORED_ALLOWED_BY_DEFAULT is False` 逐字未动** —— 即使 profile 在场，
  不显式传 `authored_allowed=True` 仍拒。判据 `test_authored_profile.py` ⇒ **23 passed**。

### EC-05 对抗性反证 4 条 × 三面（PASS）

`test_constraint_table.py` ⇒ **23 passed**，其中：

| 对抗面 | 实验边界 | 工具面 | preflight |
| --- | --- | --- | --- |
| 无沙箱 | `AuthorityError: sandbox_required` | 形状 findings 同源 | `POLICY_CONSTRAINTS_INVALID` 同源 |
| 越界路径 | `AuthorityError: escapes upward` | 同上 | 同上 |
| 超时 | `AuthorityError: exceeds the policy limit` | 同上 | 同上 |
| digest 不匹配 | `表 digest_violation` + 边界拒无摘要 shipped | — | — |

（工具面与 preflight 只判**形状**——它们拿不到执行事实；判据判的是「同一张表给出的
形状结论一致」，不是「三面都能判执行事实」。这个边界在判据 docstring 里写明。）

### EC-06 收口资产与宪章记账（PASS）

- `tools/verify_goal112_closeout.py` + `tools/goal112_closeout_assertions.py`
  ⇒ **92 PASS / 0 FAIL**（本轮首推时是 66 —— 差额 26 条来自 CI 判红后的三处补强：
  其余六行「各自边界锚」6 条、把 60 行的 `_adversarial_verdicts` 拆成两个函数时保留的
  全部判词、以及 EC-06 点名的**五轮程序完成报告** 8 条）；断言集**重放**三面同判
  （在断言集里同时调表与实验边界）；
- 登记 `_VERIFIERS` 与 `IN_SCOPE`；宪章程序表 / 阶梯 / 进展 / 修订按实际改；
- 阶梯只改「实验」一格，其余六格逐字未动。

## CI 三轮判红与本轮的修法（如实登记）

| 轮次 | 提交 | 判负 | 分类 | 修法 |
| --- | --- | --- | --- | --- |
| 1 | `b109936f` | 9 | 产品面 3（应用层读环境 / 开关名新增字面量 2 处 / 两条夹具失配）+ 记录面 6 | 产品面 → `250c35a2`；记录面 → 本轮 |
| 2 | `250c35a2` | 7 | **零产品缺陷**：规模面 2（`settings.__init__` 53 行、断言集 60 行）+ 旧阶梯锚点 3 + 台账空 + 见证过期 | 本轮 |
| 3 | `ab97a4b9` | 1 | **零产品缺陷**：唯一判负是见证过期 —— 新建的程序完成报告跑 m0 时还是**未跟踪**文件，而见证入口按 `git ls-files` 取受判面 | 报告入树后重跑 m0 并提交见证（见 `MEM-20261112-242`） |

**三条可复用事实**（写进 `MEM` 级）：

1. **规模门只在全量 m0 抓得到**：`settings.py` 的 `__init__` 因新增一个参数 + 一行赋值
   越过 50 行，定向套件全绿 —— 与 `judgment-file-defects-only-full-m0-catches` 同形。
   修法是**腾等量行**（压缩两处既有注释），不是拆方法（那是公开构造面）。
2. **旧轮次的「逐字不动」锚点会被后一轮的合法推进咬红**：GOAL-110/111 的阶梯夹具与
   `verify_goal107_closeout.py` 都把「实验」行 `下一级` 钉在「脚本也从计划里选」。
   本轮合法改写后三处同红。修法是**把锚换到改写后的形态**并写明换的理由（不是放宽：
   越级推广那条判词逐字未动，且本轮自己的断言集新增「其余六行各自边界锚」6 条），
   同时 `verify_goal107` 的判词从「逐字保持某一串」改成「仍是认可形态之一」，
   两形态都保留「生成级未启用」。
3. **首推携带空台账必红**（序 78 / 79 之后第三次），且**空台账的红会连带见证过期**：
   补记录 ⇒ 见证失效 ⇒ 必须重跑全量 m0。健康顺序仍是「记录 → 判据 → m0 → 提交」。

## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 反证臂 | 结果 |
| --- | --- | --- |
| `test_constraint_table` | 四种形状错误各判一次；4 条对抗 × 三面；`bool` 不冒充 `int` | 红 |
| `test_authored_profile` | 只过一道门 ⇒ 拒（两种缺法各一臂）；profile 值 6 种非逐字取值 ⇒ 全拒 | 红 |
| `test_resolver_carries_constraints` | 未知键 ⇒ findings 点名且原声明可读 | 红 |
| `test_policy_check_reads_constraints` | 四种形状错误 ⇒ `POLICY_CONSTRAINTS_INVALID` + 点名词 | 红 |
| 收口断言集 | `AUTHORED_ALLOWED_BY_DEFAULT` 改 True ⇒ 红；第四键进 `ENFORCED_KEYS` ⇒ 红 | 红 |

## 结论

**PASS_WITH_WARNINGS**。六条 EC 全 PASS；两条残余（`W-1` 第四键只有形状 /
`W-2` `script_source` 未串进派发）、两条未覆盖（`U-1` 未跑真实 `authored` 实验 /
`U-2` 执行期约束落实未验证）、两条声称边界（`R-1` 生成级未启用 / `R-2` 沙箱不可逃逸未宣称）
逐条明写。

**本轮一处方法论收获**：**「让声明生效」与「重新发明合法集」是两件事**——
我第一版把出厂 `policy.yaml` 里早已声明的第四键判成非法，真实控制面随即 FAIL。
判据的方向应该是「既有声明在同一条线上被同一张表读」，
不是「我认为只有三个键合法」。**真实控制面的红是这件事唯一可靠的信号。**
