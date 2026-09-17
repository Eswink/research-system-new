---
id: RECHECK-20260917-092
plan_id: PLAN-20260917-092
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle9-closeout
baseline_ref: 7c0d9f2
checked_head: d00dec6+worktree
---

# RECHECK-20260917-092 — GOAL-004 收口复检（EC-01…EC-07 × 当前树 + CI 台账）

## 检查范围

GOAL-20260917-004 的终止条款前置：七个 EC 在**当前树**上的证据面（源码标记 + 文档 + 登记表 +
**真的跑**的定向套件），以及本 GOAL **全部** CI run 的逐 job 终态。**不在本轮**：重开任何 EC、
新增产品能力、把 EC-07 的未决项（依赖 advisory / hook 侧 enobufs）在本机强行推进。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| EC-01 来源自足续跑 | `ProtocolBody`/`ProtocolSource` 域值对象 + `run.protocol_source` 冻结事实 + `continue_from_rebuild` 入口；定向 4 文件真跑 | PASS |
| EC-02 停车语义读面 | `services/api/run_pause_view.py` + `PausedDispatchDto`；定向 1 文件真跑 | PASS |
| EC-03 failure_policy 消费者 | `OnTaskFailure` 域类型 + `phase_runner` 消费点；定向 3 文件真跑 | PASS |
| EC-04 失败 run 语义 digest | `manifest_semantic_digest` 落到 run 结果 + `convergence` 校验 + `EVENT_MODEL.md` 口径；定向 1 文件真跑 | PASS |
| EC-05 锁粒度 + 统一派发读面 | 端口 `dispatch_ownership` + 四态常量 + **三个适配器各自实现** + SQLite 连接序列化；定向 3 文件真跑（含 PG parity） | PASS |
| EC-06 续跑失败补偿 | 单一 `compensate_failed_resume` + `RUN_RESUME_FAILED` 词表 + 文档口径；定向 2 文件真跑 | PASS |
| EC-07 审计终态 | 终态文档（scanId / seal / **36 行逐条处置表** / 未覆盖范围 / 不主张项目安全）+ `docs/INDEX.md` 登记 | PASS |
| 治理登记面 | ALL_PLAN 含 084…092；GOAL 中 EC-01…EC-07 **逐个块**判定为 `status: PASS`；续点指向收口 | PASS |
| 复检脚本总体 | `scratch/verify_goal004_closeout.py`（46 条断言 + 15 个定向套件真跑） | **PASS（全绿）** |
| CI 台账 | 44 个 GOAL-004 commit → **16 个 run** 逐 job 重读（见下表） | PASS（1 次失败已在同 cycle 内修复并复绿） |

## CI 台账（逐 job）

| run | head | 结论 | 备注 |
| --- | --- | --- | --- |
| #133 `35203036505` | `7c0d9f2` | **failure**（仅 `collector-quality`） | 建档 run：2 条 PG 退避用例的**测试墙钟依赖**（夹具注入固定引擎时钟却用 SQL `now()` 挪 deadline）⇒ 同 cycle 修复提交 `5607992`（夹具改用引擎时钟，**断言未改**） |
| #134 `35204710864` | `5607992` | 六个 job 全 success | 修复验证 |
| #135 `35211094454` | `5141e06` | 六个 job 全 success | cycle 1 |
| #136 `35219834215` | `7316d1d` | 六个 job 全 success | cycle 2 |
| #137 `35221608267` | `ffa272c` | 六个 job 全 success | **本轮补记**（此前未进 GOAL 台账） |
| #138 `35227784813` | `186963c` | 六个 job 全 success | cycle 3 |
| #139 `35238057745` | `13054a8` | 六个 job 全 success | cycle 4 |
| #140 `35239932808` | `8f0b91e` | 六个 job 全 success | cycle 4 收口 |
| #141 `35245282964` | `d8c9377` | 六个 job 全 success | cycle 5 |
| #142 `35246943135` | `2a979e2` | 六个 job 全 success | cycle 5 收口 |
| #143 `35258463258` | `e6656be` | 六个 job 全 success | cycle 6 |
| #144 `35259814746` | `ce06be2` | 六个 job 全 success | cycle 6 收口 |
| #145 `35266572576` | `0a58b6d` | 六个 job 全 success | cycle 7 |
| #146 `35268496008` | `3a9b86c` | 六个 job 全 success | cycle 7 收口 |
| #147 `35272745779` | `b6e14d4` | 六个 job 全 success | cycle 8（EC-07 终态） |
| #148 `35274491507` | `d00dec6` | 六个 job 全 success | cycle 8 收口提交（收口复检时读回） |

36/37 次 job-结论为 success；唯一失败项在同一个 cycle 内以**修夹具而非改断言**收口。

## 反证与实测

- **复检脚本本身有判别力**：首跑即抓出 1 条真实缺项——EC-07 处置表按"同签名合并行"写，
  逐条行只有 7 行（< 36）⇒ 判 FAIL；随后按封印产物**逐条生成 36 行**（生成脚本直接读
  `findings.json`，保证与封印列表一一对应），复跑全绿。**若脚本只会照抄结论，这一条不会被抓出。**
- **定向套件是真跑**：每条 EC 证据都是子进程 pytest 的退出码（非零即 FAIL），
  含 `tests/postgres/test_dispatch_ownership_pg.py`（真 PG）与 `tests/e2e/` 两条端到端。

## 告警（W）

收口不隐藏缺口；本 GOAL 期间登记的告警按主题汇总进 GOAL 的「终止与收口」表（9 类），
其中需要**环境/人工**才能推进的是：

- **W-1 安全审计残留**：依赖 advisory 1 条未署名（需联网复核）、hook 侧 `scanner_enobufs`
  未消除、扫描输入含 gitignored 内容、`artifacts/` 内含未跟踪明文 token、威胁建模与
  授权面零覆盖（EC-07 / RECHECK-091 W-1…W-5）。
- **W-2 同形未修入口**：`resume_after_approval` 失败同样不补偿（EC-06 / RECHECK-090 W-1）。
- **W-3 450 行硬上限持续贴线**：`run_orchestration/service.py` 450/450（EC-03 / RECHECK-086 W-5）。

## 结论

七个 EC 在当前树上**逐条复核通过**（含真跑定向套件），CI 台账逐 job 复核无遗漏，
未覆盖与未决项如实写进 GOAL「终止与收口」。**GOAL-20260917-004 收口条件成立 → `ACHIEVED`。**
本结论不主张"项目安全"（EC-07 口径不变）。
