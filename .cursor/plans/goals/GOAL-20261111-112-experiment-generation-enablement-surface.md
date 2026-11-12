---
id: GOAL-20261111-112
slug: experiment-generation-enablement-surface
title: 实验从「选择级」到「生成级」的启用面（只交付可启用的网，不启用）
status: ACHIEVED
created_at: 2026-11-12
updated_at: 2026-11-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-11-11 登记序 77…80 五轮程序（与序 76 同一次授权），本轮为序 80（最后一轮）：
    「实验从『选择级』到『生成级』的**启用面**」。沿用户 2026-10-29 全权限预授权；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支。
objective: >-
  GOAL-107 已交付一半：`script_authority.py` 的 `ExecutionAuthority` 闭集
  （`SHIPPED` / `AUTHORED`）、`AUTHORED_ALLOWED_BY_DEFAULT = False`、三条策略约束
  （`sandbox_required` / `path_prefix` / `max_seconds`）**在实验执行边界**已生效。
  缺的是 `W-4`：那三条约束在 `tool_plane/resolver.py` 与 `preflight/policy_check.py`
  **仍不读** ⇒ 同一条声明在不同执行面上效力不一致。本轮把**同一张约束表**推到工具面与
  preflight；交付 `script_source: "authored"` 声明 + 一个**具名安全 profile**；
  **`AUTHORED_ALLOWED_BY_DEFAULT = False` 逐字不动** —— 只交付「可启用的那张网」。
exit_criteria:
  - id: EC-01
    criterion: >-
      **同一张约束表**：新建 `packages/application/experiments/constraint_table.py`
      （或等价），把三条约束的**判定**（键名 / 类型 / 违反时的点名）抽成**唯一一份**纯函数；
      `script_authority.check_constraints`、`tool_plane/resolver`、`preflight/policy_check`
      **三处都调它**，不各写一套。判据钉住「三处都 import 同一个模块」。
    verify: >-
      `tests/application/experiments/test_constraint_table.py` ⇒ 表格自洽（三个键、类型、
      点名）; `tests/architecture/python/test_constraint_table_is_single_source.py` ⇒ 三处
      消费点都引用它（源码面 + AST）。
    status: PASS
  - id: EC-02
    criterion: >-
      **工具面读约束**：`tool_plane/resolver` 的解析结果携带**本 capability 的约束**；
      `ALLOW_WITH_CONSTRAINTS` 的 capability 在解析面上**不再等价于放行**——
      它返回的 `CapabilityResolution` 必须让约束**可读**（不静默丢弃）。
    verify: >-
      `tests/application/tool_plane/test_resolver_carries_constraints.py` ⇒ 正例（带约束的
      capability 解析结果含该约束）+ 反证（无约束 ⇒ 空，且与「有约束但空表」分得开）。
    status: PASS
  - id: EC-03
    criterion: >-
      **preflight 读约束**：`preflight/policy_check` 的 `ALLOW_WITH_CONSTRAINTS` 分支除
      措辞外**核验约束形状**（未知键 / 类型错 ⇒ finding 点名，不再只是一句话）。
    verify: >-
      `tests/application/preflight/test_policy_check_reads_constraints.py` ⇒ 正例（三条合法
      约束 ⇒ 无 finding）+ 反证（未知键 / 类型错 ⇒ 点名 finding）。
    status: PASS
  - id: EC-04
    criterion: >-
      **`script_source: "authored"` 声明 + 具名安全 profile**：`experiment_design` 可声明
      `script_source`（闭集 `shipped` / `authored`）；`authored` 只在**具名安全 profile**
      （`AUTHORED_SAFETY_PROFILE`，与序 76 的开关同形态：显式环境变量 + 点名）下被放行。
      **`AUTHORED_ALLOWED_BY_DEFAULT` 逐字不动（`False`）**。
    verify: >-
      `tests/application/experiments/test_authored_profile.py` ⇒ 反证：无 profile ⇒
      `AuthorityError` 点名；有 profile ⇒ 放行；`AUTHORED_ALLOWED_BY_DEFAULT is False` 断言。
    status: PASS
  - id: EC-05
    criterion: >-
      **对抗性反证 4 条全绿**（无沙箱 / 越界路径 / 超时 / digest 不匹配），且**每条都在
      三个执行面上各验一次**（实验执行边界 / 工具面 / preflight）——同一张表，三面同判。
    verify: >-
      `tests/application/experiments/test_constraint_table.py` ⇒ 4 条 × 3 面 = 12 臂，
      逐条按压判红。
    status: PASS
  - id: EC-06
    criterion: >-
      **收口资产与宪章记账**：`tools/verify_goal112_closeout.py` +
      `tools/goal112_closeout_assertions.py`，登记进 `_VERIFIERS` 与 `IN_SCOPE`；
      宪章程序表 / 阶梯 / 进展 / 修订按实际改；**序 76…80 五轮全部 ACHIEVED 的程序完成报告**。
    verify: >-
      收口验证器全 PASS；两处登记判据绿；`tools/credential_audit.py` 四面 `offenders=0`。
    status: PASS
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 把真实 key 写进任何被跟踪文件（只进 gitignored `.env`）
    - 改 TrustLabel 语义 / 动 RunManifest / 改 `.github/workflows/**`
    - 把 `AUTHORED_ALLOWED_BY_DEFAULT` 改成 True（安全姿态决定，须用户拍板）
    - 放宽 §9 任何默认 deny 项
    - 让 `authored` 在**没有**具名 profile 时被放行
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 需要打开 `AUTHORED_ALLOWED_BY_DEFAULT` 才能继续 ⇒ 停下登记待拍板
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261112-112-authored-enablement.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-112-authored-enablement.md
memory_entries: []
---

# GOAL-20261111-112 —— 实验从「选择级」到「生成级」的启用面

## 目标与退出标准

承序 79。**只交付「可启用的那张网」，不启用。**

### 缺的正是 `W-4`：同一张约束表，三个执行面效力不一致

GOAL-107 让三条策略约束（`sandbox_required` / `path_prefix` / `max_seconds`）在
**实验执行边界**（`script_authority.check_constraints`）生效了。但：

- `tool_plane/resolver.py` 的 `_effective_decision` 注释写着「ALLOW_WITH_CONSTRAINTS
  由执行路径落实约束，解析面等价放行」——**约束在解析面上是丢掉的**；
- `preflight/policy_check.py` 的 `ALLOW_WITH_CONSTRAINTS` 分支只把键名拼成一句话
  （`constraints = ", ".join(...)`），**不核验形状**（未知键 / 类型错都放过去）。

⇒ 同一条声明在「实验边界」严格执行、在「工具面」看不见、在「preflight」只被复述。
本轮把**同一份判定表**推到三处。

### 交付的启用面（不启用）

- `script_source: "authored"` 声明入 `experiment_design`（闭集 `shipped` / `authored`）；
- 一个**具名安全 profile**（`AUTHORED_SAFETY_PROFILE`，与序 76 的开关同形态：
  显式环境变量 + 点名），**只有它**能让 `authored` 通过权威面；
- **`AUTHORED_ALLOWED_BY_DEFAULT = False` 逐字不动**：出厂行为与改动前逐字节相同。

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 六条 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住 ⇒ 移入「残余与未覆盖范围」，**继续做剩下的**，GOAL 保持 ACTIVE；
5. 工作树上有**别人**的未提交改动 ⇒ 只 add 本 cycle 的显式路径，绝不 `add -A`。

## 单 cycle SOP

① derive → ② 执行 → ③ 本地验证（定向套件 + 全量 m0 见证）→ ④ commit（显式路径）
→ ⑤ push main + CI 轮询 → ⑥ 纠错 → ⑦ 回写记录 + 下一轮。

**记录顺序**：写全部记录 → `git add` 全部受判文件 → 记录面判据
→ **最后**跑 `tools/run_m0_with_witness.py` → 之后不再改树 → 提交推送。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff（`product-lint` 与单文件 lint **不同**：前者扫全产品根）/ mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest 断言 | 读失败输出定位；**修产品优先，禁改断言迁就** |
| 台账为空 | `test_goal_ledger_covers_every_commit`：CI 台账没有提交 | **首推必红（序 78/79 各一次）**：补行 → 重跑 m0 → 再推 |
| 行尾漂移 | 一条 LF 锚点判据突然红 | 检查是不是自己把文件写成 CRLF |
| flake/env | 已知签名（observability OTLP 端口、teardown race） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |

## 终止与收口

- **ACHIEVED**：六条 EC 全 PASS + RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 两树复检 + 本文件收口 + **五轮程序完成报告**。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过上限，或 `max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实，不得留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261112-112 | 见台账 | 表/三面/authored 四判据 **57 passed**；受影响面回归 **235 passed**；收口验证器 **66 PASS / 0 FAIL**；ruff/format/mypy 三道绿（mypy 1439 文件） | 与收口提交同一次 push（不冒领） | 三处（`experiments/__init__` 导入成环 ⇒ 函数内导入；`requires_workspace_lease` 被误判非法 ⇒ 纳入闭集只过形状；测试夹具类型面 10 条 mypy） | `W-1`/`W-2` 残余、`U-1`/`U-2` 未覆盖 | 五轮程序完成报告 |

## 残余与未覆盖范围

### 残余（本轮已交付里仍然存在的缺口）

- `W-1` **第四键只有形状校验、没有执行语义**：`requires_workspace_lease` 是
  `examples/config/policy.yaml` 的 `workspace.write.code` 里**早已声明**的一条
  （全仓除该 YAML 外零命中）。本轮的判据是「同一张表三面对齐」，不是「重新发明合法约束集」
  ——把出厂策略里写着的键判成「非法」会让真实控制面 preflight 直接 FAIL（实测三条判据当场红）。
  因此它进了闭集并过形状校验（`bool`），但**执行语义未实现**：判它需要「租约是否已持有」
  这个事实，实验执行边界拿不到。**这是本轮之前就存在的缺口，本轮没有扩大也没有假装补上。**
- `W-2` **`script_source: authored` 只接在声明面与权威面**：`declared_script_source`
  读得出、`authority_for` 拦得住，但**派发路径还没有把它串起来**
  （`plan_selected_script` 目前仍按白名单选脚本，不看 `script_source`）。串起来要改派发体
  如何把「脚本字节从哪来」交给执行后端 —— 那是**执行面**改动，不是声明面，本轮未做。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1` **未跑过一次真实 `authored` 实验**：所有判据都在闸门上（`authority_for` /
  `check_constraints` / 表 / 两个新接入面）。真实路径要「模型写脚本 → 落盘 → 过权威面 →
  沙箱执行 → 取结果」，其中**落盘与执行**两段没有测试覆盖（`W-2` 的下游）。
- `U-2` **约束在「执行期」的落实仍只在实验边界**：工具面现在**携带**约束（解析结果可读），
  但工具调用的**执行路径**是否按 `path_prefix` / `max_seconds` 真的限制住，本轮没有验证
  —— 那要看 `execute_tool_call` 那一侧，它本轮未改。

### 声称边界（**不得宣称**的事）

- `R-1` **不宣称「生成级已启用」**：`AUTHORED_ALLOWED_BY_DEFAULT` 逐字仍是 `False`；
  `authored` 要过**两道门**（调用方显式 `authored_allowed=True` **且**具名 profile 在场）。
  本轮交付的是**可启用的那张网**，不是启用本身。
- `R-2` **不宣称「沙箱不可逃逸」**：本仓对沙箱的证据止于「镜像 digest pin + 三条策略约束
  在执行边界被检查」。容器逃逸、内核层隔离、资源耗尽攻击**都不在本轮射程内**，
  也没有任何判据声称覆盖它们。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-12 | ACTIVE | 建档：序 80（五轮程序最后一轮）；六条 EC |
| 2026-11-12 | ACHIEVED | 六条 EC 逐条落地；生成级未启用（`R-1`）；第四键只过形状（`W-1`）、`script_source` 未串进派发（`W-2`）、真实 authored 与执行期落实未做（`U-1` / `U-2`） |

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
