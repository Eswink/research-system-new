---
id: RECHECK-20260915-073
plan_id: PLAN-20260915-073
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-closeout
baseline_ref: d5e5de7
checked_head: d5e5de7
---

# RECHECK-20260915-073 — GOAL-20260915-003 收口复检（预算触顶）

## 检查范围

本 GOAL 的十条 cycle（EC-01…EC-06 的交付面）、每个 cycle 的本地 m0 与 main 的 CI 结论、
安全扫描处置，以及"仍未处理的长程项"是否被写成后继入口。
**触发本次收口的是 `budget.max_cycles: 10` 触顶**（frontmatter 口径：硬上限，触顶即 BLOCKED），
不是 EC 未达成。

## 检查结果

### EC 表（收口时刻）

| EC | 判据 | 状态 | 证据 |
| --- | --- | --- | --- |
| EC-01 | 设计门禁结构判据（整块新增必红、只改样式不误报） | **PASS** | cycle 1（PLAN-063 / RECHECK-063）：33 路由结构签名基线 + 反证 6 passed + 跨平台逐字节一致；后续 cycle 3/4 各触发一次真实拦截（`ops-integrations` +18、`ops-schedules` 170→260 节点，同轮像素判据 1.64% < 2% 不报警） |
| EC-02 | ToolPack 供应链面（写面 / pin↔交付物 / 能力取值域 / 健康复核 schema digest 与漂移） | **PASS** | cycle 2（后端写面）、cycle 3（console 操作面 + live 链）、cycle 7（健康复核记录 digest 并可比对漂移：漂移是**状态**、未知观测不清除、approve 重基线化；三条反证在用例里） |
| EC-03 | ops 调度用户可见写面（执行体仍是既有守护线程） | **PASS** | cycle 4（PLAN-066）：`disabledOperations` 相应项消失、trigger 调用同一函数对象、停用被守护线程自己读面消费（可控时钟 + 真实线程）；诚实边界（无 store → 503、未挂执行体 → trigger 禁用、从未跑过 → UNKNOWN）都在用例里 |
| EC-04 | worker 退出语义（SIGTERM 有界中断阻塞读） | **PASS** | cycle 5（PLAN-067）：8 处出站调用收口到 `WorkerClient._call`，超 `RESEARCHOS_WORKER_DRAIN_SECONDS` 即放弃并抛 `WorkerDrainAbort`；同脚本同参数实测 **29.64s → 1.12s**；Linux 容器内两条真实 SIGTERM 用例通过 |
| EC-05 | 替身 harness 校验 Idempotency-Key | **PASS** | cycle 6（PLAN-068）：替身在 handler 之前守门，四条语义与真中间件对齐；**反证做在产品客户端上**（改 `http.ts` 的头 → stub 用例 7 failed / 2 passed，失败面板就是真件 422 detail）；跨语言词表守卫把 stub 与 `middleware.py` 钉成集合相等 |
| EC-06 | 每 cycle 本地 m0 与 main CI 全绿；收口 RECHECK + 安全扫描处置；长程项写成后继入口 | **PASS（含一次红项的处置）** | 见下「每 cycle 的 CI 结论」与「安全扫描处置」；cycle 9 的 ubuntu 红项已定位（反证不可移植）、更正并**在随后的 run 上验证**；本节即收口复检，后继入口见文末 |

## 每 cycle 的 CI 结论（main 分支，六 job）

| cycle | 收口提交 | CI run | 结论 |
| --- | --- | --- | --- |
| 1 | `28c9c30` | 35059391199 | 六个 job 全 success（此前 35056976439 因账户计费阻断在启动前失败，非代码缺陷） |
| 2 | `3c343f4` | 35064152993 | 六个 job 全 success |
| 3 | `ce28e05` | 35071216707 | 六个 job 全 success |
| 4 | `de58a31` | 35087267045 | 六个 job 全 success |
| 5 | `1f0c7d9` | 35093603690 | 六个 job 全 success（含两条真实 SIGTERM 用例） |
| 6 | `4af5ad4` | 35100510412 | 六个 job 全 success |
| 7 | `b269aef` | 35108305191 | 六个 job 全 success |
| 8 | `e4f5b3d` | 35111194584 | 六个 job 全 success |
| 9 | `cb61f41` | 35115260874 | **五个 job success，`quality-ubuntu-latest` 判红**（红在本轮新增的负载型反证：2 vCPU runner 复现不出竞态） |
| 10 | `d5e5de7` | 35119573827 | **六个 job 全 success** —— 其中 ubuntu 跑的是**更正后的结构判据**，证明更正可移植 |
| 收口 | `e020639` | 35121878161 | **六个 job 全 success**（eval-gate 16:26:41Z / collector-quality 16:28:27Z / container-quality 16:30:20Z / console-frontend 16:33:31Z / quality-ubuntu-latest 16:34:09Z / quality-windows-latest 16:38:12Z，无重跑）——收口提交本身也过了 main 的全部门禁 |

**cycle 9 红项的处置（按 GOAL 失败分类表）**：分类 = 反证不可移植（非代码缺陷、非门禁过严）；
处置 = 反证从"负载压出读错"换成"读结果是否在锁内取尽"的**结构判据**，负载型复现器
降级为记录（数字与脚本在 RECHECK-071「更正」段）；**未**放宽任何被保护的性质。
验证 = cycle 10 的 run 35119573827 上 ubuntu job success。

## 安全扫描处置

- **Mimosa 密封深度扫描（本轮实跑，已完成）**：
  - scanId `scan-2026-09-16T16-21-44.354Z-fb46b8691603`，seal
    `sha256:8b801259bb8c2f0f3afa77c2e6ce3ce30b3c2b5529a42e6e5c19c9e7989538bb`；
  - 结果：**36 findings（3 high / 28 medium / 5 low）**，182 packages；
    依赖侧离线库命中 **1 包 / 1 advisory**（`dependencySummary.offlineAdvisory`）；
  - **coverage: partial，runStatus: inconclusive**，gap = "部分分析阶段未能完整覆盖"；
  - **本轮 cycle 8–10 的改动文件在报告里 0 命中**（`adapters/sqlite/db.py`、
    `services/api/tool_provider_endpoints.py`、`preflight_support.py`、
    `tool_registry_support.py`、`packages/domain/tool_registry.py` 等逐项检索）；
    36 条与 cycle 4/5/6 记录的逐项一致（同一批历史面）。
  - **能力边界**：`evidenceBoundary = static_only_no_runtime_execution` —— 这是**静态**证据，
    **不能**替代运行时验证，也**不能**据此宣称"项目安全"。
- **提交门禁的既有噪声**：本 GOAL 每次 commit/push 的钩子都报告 `scanner_enobufs`
  （未取得完整扫描结论）——按兼容策略继续。因此本 GOAL 全程只声明
  "本轮改动面在密封扫描/提交门禁下没有新增高危"这一级事实，**不做全仓安全结论**；
  上面这次密封扫描（36 findings / partial coverage）就是可复核的证据面。

## 仍未处理的长程项（后继入口，按优先级）

1. **provider 端点注入执行路径**（RECHECK-072 W-1）：`endpoint_env` 已能被执法与可见，
   但 adapter 仍用构造时注入的连接规格。要真正"配置驱动"，需要按 spec 重建 provider
   实例——这会引入**受控出网**面（出网白名单 / `network_domains` 执法），
   属安全策略级动作，**需要用户/ADR 决策**后再做。
2. **provider 凭据绑定**（RECHECK-072 W-4）：`ToolProviderSpec` 无法表达 `credential_ref`；
   与第 1 项同族，但**不需要出网**，可以独立先做（声明 → 门槛 → 可见，只做存在性检查、
   绝不物化密钥）。这是本 GOAL 结束后**最小、最安全**的下一步。
3. **`tool_pack.*` 策略产品决策**（RECHECK-065 W-1）：是否在生产 `policy.yaml` 放行
   ToolPack 安装/更新能力，或在获批前保持 default DENY——产品决策，需用户拍板。
4. **`conn.cursor()` 自建游标路径**（RECHECK-071 W-3）：不走物化，本仓无调用点；
   若要彻底收口需把游标也纳入保护（低优先）。
5. **锁粒度**（RECHECK-070 W-2 / 071 W-4）：所有 store 共享一把锁；若将来出现长查询，
   应改为每线程连接而不是加大锁。
6. **GOAL 预算续期**：`max_cycles: 10` 已用尽。继续迭代需要**新 GOAL**（沿用
   GOAL-002 → GOAL-003 的承接方式）或本 GOAL 的显式预算变更——由用户决定；
   本文只登记事实，不自作续期。

## 结论

十条 cycle 全部交付并各自留下可复核证据：五个 EC 全 PASS，第六个（治理收口）在
"每 cycle 本地 m0 + main CI + 收口复检 + 扫描处置 + 后继入口"四条上都成立，
其中 cycle 9 的 CI 红项被定位为**反证不可移植**（非代码缺陷），更正后在 cycle 10 的
run 上被验证。结果为 **PASS_WITH_WARNINGS**：W 类事实是本文「安全扫描处置」的
密封扫描 coverage 仍 partial、以及「仍未处理的长程项」六条（其中两条需要用户决策）。
GOAL 状态按 frontmatter 口径因 **`max_cycles` 触顶**置 **BLOCKED**，并附后继入口。
