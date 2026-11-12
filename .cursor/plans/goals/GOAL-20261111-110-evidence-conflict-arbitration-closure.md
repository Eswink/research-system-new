---
id: GOAL-20261111-110
slug: evidence-conflict-arbitration-closure
title: 证据矛盾的处置闭环（仲裁策略闭集 + HTTP 路由）
status: ACHIEVED
created_at: 2026-11-12
updated_at: 2026-11-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-11-11 登记序 77…80 五轮程序（与序 76 同一次授权），本轮为序 78：
    「证据矛盾的处置闭环（仲裁策略闭集 + HTTP 路由）」。沿用户 2026-10-29 全权限预授权；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支。
objective: >-
  检测与记账已经齐备（`content_conflict.py` 三种可判形态 / `conflict_sweep.py` /
  五态处置 / `ConflictResolution` + PG migration 023），缺的正是「**谁、依据什么消解**」：
  `resolve_memory_conflict` 只记录「谁在何时消解了哪一对」，不做谁对谁错的推断，
  且**没有 HTTP 路由**。本轮交付确定性仲裁闭集 + 带幂等键的 HTTP 路由 + 判据，
  阶梯「证据」行 `下一级` 改写为「处置闭环成立（策略闭集 + 可判依据）」。
exit_criteria:
  - id: EC-01
    criterion: >-
      **仲裁策略闭集**：新建 `packages/application/memory/arbitration.py`，三值闭集
      `NEWER_WINS` / `SOURCE_TRUST_WINS` / `REQUIRE_HUMAN`，确定性纯函数，每个策略给
      **可判依据**（时间戳 / `TrustLabel` 序 / 显式拒绝）。**默认必须是 `REQUIRE_HUMAN`**，
      自动策略只在显式声明时启用（与 §9 默认 deny 同姿态）。
    verify: >-
      `tests/application/memory/test_arbitration.py` ⇒ 三策略各一条正例（依据字段可读）+
      反证：不声明策略 ⇒ 返回 `REQUIRE_HUMAN`（默认拒绝自动化，点名）。
    status: PASS
  - id: EC-02
    criterion: >-
      **HTTP 路由**：`POST /memory/{id}/conflicts/{other_id}/resolve`，带幂等键
      （与既有写面路由同形态：幂等键头 / 请求体校验 / 读面不认证写面认证的既有姿态不变）。
    verify: >-
      `tests/api/test_memory_conflict_resolve_route.py` ⇒ 正例（幂等键下两次同请求同响应）+
      反证（无幂等键 ⇒ 点名拒绝；未知 memory id ⇒ 404 点名）。
    status: PASS
  - id: EC-03
    criterion: >-
      **判据**：三种策略各一条正例 + 两条反证（低于阈值的置信度必须拒自动消解；
      同一对不能重复消解——重复消解在域层已拒，判据要在路由层也钉住）。
    verify: >-
      `tests/application/memory/test_arbitration.py`（域层）与
      `tests/api/test_memory_conflict_resolve_route.py`（路由层）各自覆盖；
      反证臂按压后确认判红。
    status: PASS
  - id: EC-04
    criterion: >-
      **阶梯改写（只动一格）**：阶梯「证据」行 `下一级` 改写为「**处置闭环成立（策略闭集 +
      可判依据）**」；其余六格 `下一级` 逐字不动。
    verify: >-
      收口验证器断言：证据行含新句；其余六行与改写前逐字相同（锚点短语在位、无越句）。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口资产与宪章记账**：`tools/verify_goal110_closeout.py` +
      `tools/goal110_closeout_assertions.py`，登记进 `_VERIFIERS` 与 `IN_SCOPE`；
      宪章程序表 / 阶梯 / 进展 / 修订按实际改；GOAL-109 的 CI 台账 run id 回填顺路完成。
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
    - 让默认策略变成自动消解（REQUIRE_HUMAN 缺省语义逐字不动）
    - 重做检测面（content_conflict / conflict_sweep 已齐备，不新造第二套）
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 默认策略要求自动化（REQUIRE_HUMAN 缺省语义）⇒ 停下登记待拍板
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261112-110-conflict-arbitration.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-110-conflict-arbitration.md
memory_entries: []
---

# GOAL-20261111-110 —— 证据矛盾的处置闭环（仲裁策略闭集 + HTTP 路由）

## 目标与退出标准

承序 77：证据格的 `下一级` 是「矛盾处置闭环」。**检测面不重做**（三种可判形态 + 存量清扫
+ 五态处置已在树），本轮只补「谁、依据什么消解」的**决策面**与其 HTTP 入口。

### 闭环缺的哪一环（现状实测）

- `packages/application/memory/lifecycle.py` 的 `resolve_memory_conflict` **只记录**
  「谁在何时消解了哪一对」（`ConflictResolution(other_id, resolved_by, resolved_at)`），
  **不做**谁对谁错的推断；
- `services/api/routers/memory.py` 的四个 `@router` 里**没有**它 ⇒ HTTP 面没有入口；
- 因此「两条证据矛盾了」之后，唯一出路是人工在域层直接调函数——闭环缺**决策**与**入口**。

### 默认姿态（与 §9 同源）

`REQUIRE_HUMAN` 是**缺省**返回值：任何不显式声明策略的调用都得到「必须人来裁决」——
自动化消解只能被**显式**打开。这与 AGENTS.md §9 的默认 deny 是同一条纪律在证据面的应用。

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 五条 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
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
| lint/format/typecheck | ruff / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest 断言 | 读失败输出定位；**修产品优先，禁改断言迁就** |
| 行尾漂移 | 一条 LF 锚点判据突然红 | 检查是不是自己把文件写成 CRLF |
| flake/env | 已知签名（observability OTLP 端口、teardown race） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |

## 终止与收口

- **ACHIEVED**：五条 EC 全 PASS + RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 两树复检 + 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过上限，或 `max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实，不得留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261112-110 | 见台账 | 仲裁判据 14 passed + 路由判据 10 passed（共 24）；收口验证器 **73 PASS / 0 FAIL**；OpenAPI 快照已重生成；ruff/format/mypy 三道绿 | 与收口提交同一次 push（无独立 run；不冒领） | 四处（`Timestamp` 是包装类不可直接比大小；路由方向判定须先于仲裁；快照重生成写成 CRLF 需归一到 LF；`memory.py` 撞 450 行硬上限 ⇒ 消解路由单列 `memory_conflicts.py`） | `W-1`/`W-2` 残余、`U-1`/`U-2` 未覆盖 | 序 79（叙述强口径） |

## 残余与未覆盖范围

### 残余（本轮已交付里仍然存在的缺口）

- `W-1` **仲裁只覆盖「两条记忆」这一对形状**：`arbitrate(left, right)` 是二元函数；
  一组记录里的**多方**矛盾（A↔B↔C 之间两两冲突）要调用方**逐对**调、并自己决定
  调用顺序——顺序会影响「先消解哪一对」（先消解 A↔B 会让 B 的处置变化）。
  传递闭包 / 多方仲裁是**另一个设计问题**（谁赢一次不等于谁赢全局），本轮未做。
- `W-2` **`trust_labels` 由调用方给，不从记录里推导**：`MemoryRecord` 没有信任标签字段
  （证据侧的 `TrustLabel` 在 `SourceRecord` 上）；路由因此**不**自动查证据面——
  自动查会把「哪条证据支撑这条记忆」这个同样需要判定的问题引进仲裁里。当前形状是
  「判据可信但输入要显式给」，判据钉住的是这个边界不是缺省推断。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1` **检测面与仲裁面的端到端联调未做**：`conflict_sweep` 扫出的存量矛盾**不会**
  自动进入仲裁（那需要一条批量作业 + 「谁来批准自动消解」的运维决策）。本轮交付的是
  **单对消解**的决策面与入口；批量闭环是运维面。
- `U-2` **前端未接**：消解路由没有对应的 UI（Memory 页仍只读 `conflict_resolutions`）。
  `types.ts` 也未加 DTO（它手工维护、当前判据不要求同步）——接前端时要一并补。

### 声称边界（**不得宣称**的事）

- `R-1` **不宣称「矛盾已被自动消解」**：缺省是 `REQUIRE_HUMAN`（返回判词、**不落账**）；
  自动消解只能由**显式声明**的策略 + 阈值触发，且依据必须齐备（时间戳/标签在场且不等）。
  自动化是**选择**，不是**缺省行为**。
- `R-2` **不宣称「消解等于判对了」**：`NEWER_WINS` / `SOURCE_TRUST_WINS` 判的是
  **声明面上的两条可判依据**（谁更新 / 谁的来源更可信），不是「内容在事实上正确」。
  仲裁结果与 `resolved_by` 一起入账，复核时读得出**依据是什么**——那是本轮的射程。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-12 | ACTIVE | 建档：序 78；五条 EC；检测面不重做 |
| 2026-11-12 | ACHIEVED | 五条 EC 逐条落地；缺省 REQUIRE_HUMAN 不落账（`R-1`）；多方/批量/前端未做（`W-1` / `U-1` / `U-2`） |

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
