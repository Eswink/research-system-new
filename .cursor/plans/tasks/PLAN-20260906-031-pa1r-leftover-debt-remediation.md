---
id: PLAN-20260906-031
slug: pa1r-leftover-debt-remediation
title: PA-1R 遗留债务清偿（扫描器 high 清零 + 封闭性加固 + 登记对齐）
status: IN_PROGRESS
created_at: 2026-09-06
updated_at: 2026-09-06
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-06 计划解决遗留债务和问题（批准计划含 W1-W6）"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: [pa1r-pass-baseline-complete, mimosa-scanner-false-positives]
---

# PLAN-20260906-031 — PA-1R 遗留债务清偿

## 目标

清偿 PA-1R 后登记的全部可行动债务：扫描器误报 high 清零（commit 门禁从此不再被既有项拦截）、两个产品封闭性隐患修复（DSN 链对齐、gen_openapi 封闭化）、Starlette 弃用告警消除、债务登记表（BACKLOG + 处置文档）与实际状态对齐。终局验收 = 新密封扫描主树 high=0 + 全量 m0 门禁在最终 revision 全绿。

## 范围

包含：W1 DSN 链对齐（settings.py 键序 + 测试加固 + 部署文档）；W2 gen_openapi 显式 :memory: SQLite 装配；W3 pyproject filterwarnings；W4 三项扫描器 high 修复（两个审计工具 SQL 构形 + examples 脚本等价改写）；W5 新密封扫描 + PA1_MIMOSA_REVIEW 增补 PA-1R 轮处置 + BACKLOG 行 178/180 清偿注记与能力表状态；W6 全量 m0 门禁 attempt-7 + recheck 033 + 提交。

不包含：`/cost` MONETARY_UNAVAILABLE（设计语义）；21 个 medium 的代码改动（probes 误报，仅处置记录）；examples 5 个 low（确定性 seed 设计）；BACKLOG 175/176 既有保留项；产品产品 SQL 装配的整批重写（无 high 命中）。

## 验收条件

- [ ] AC-1 新密封扫描主树（非 scratch）high = 0，seal 被 recheck 引用
- [ ] AC-2 DSN 对齐后 settings 链测试 + 全量 m0 门禁（attempt-7）在最终 revision 全绿
- [ ] AC-3 gen_openapi 无 DB 可生成且 docs/api/openapi.m13.json 字节不变
- [ ] AC-4 pytest 输出无 Starlette 弃用告警
- [ ] AC-5 examples 两个 e2e 测试文件全绿（0.745 与相对可复现断言不变）
- [ ] AC-6 BACKLOG 行 178/180 清偿注记 + 能力表 PA-1/PA-1R 状态更新；PA1_MIMOSA_REVIEW 含 PA-1R 轮处置节
- [ ] AC-7 全部工作提交、工作树干净、recheck PASS

## 状态历史

- 2026-09-06 IN_PROGRESS：计划批准，开始 W1。

## 实施清单

- [x] W1：DSN 链对齐（`services/api/settings.py` 键序 + `test_settings_otel` 加固与新增优先级断言 + `PERSONAL_DEPLOYMENT.md` 重写 + CI workflow postgres service 核验）。
- [x] W2：`tools/gen_openapi.py` 显式 `:memory:` SQLite 装配（快照字节不变，git diff 空）。
- [x] W3：`pyproject.toml` filterwarnings 过滤 starlette 导入期弃用告警（输出零告警实测）。
- [x] W4：三项主树 high 清零——`tools/PA1R运行演练v1.py` / `tools/PA1R恢复闭包v1.py` 改用字面 SQL 创建会话级 `pg_temp` 参数化函数（对真实恢复库验证与旧 `sql.SQL().format` 模式产出逐字节等价）；`examples/experiments/m12_reference_classification.py` 改 `Path.write_text`（字节等价；两个 e2e 套件 9/9 绿）。
- [x] W5：新密封扫描 `scan-2026-09-06T11-34-43.682Z-6a9b17a9dc0a`（seal `sha256:a4813342…`）主树 **high=0**；`PA1_MIMOSA_REVIEW.md` 增补 PA-1R 轮处置；BACKLOG 行 178/180 清偿注记 + SI-1/PA-1/PA-1R 能力表状态更新。
- [ ] W6：全量 m0 门禁 attempt-7/8（最终 revision）+ recheck 033 + 记录提交。

## 证据

| 项 | 证据 |
| --- | --- |
| W1 | `tests/api/test_settings_otel.py` 14 passed（含 `test_gateway_dsn_key_leads_canonical_chain`）+ ruff/mypy 干净 |
| W2 | `python -B tools/gen_openapi.py` 重生成后 `git status docs/api/openapi.m13.json` 为空（字节不变） |
| W3 | `pytest tests/api/test_settings_otel.py` 输出无 StarletteDeprecationWarning |
| W4 | 对恢复库实测 `pg_temp.pa1r_count`/`pa1r_row_json`（22 表；与旧模式哈希逐字节等价）；`test_m12_reference_e2e` + `test_evidence_admission_e2e` + `test_openapi_snapshot` 9/9 |
| W5 | 密封扫描 seal `sha256:a4813342330d645c161c89a3abe7276554f1bac46365632225f9e3bd8b242b00`（主树 16 findings：high 0 / medium 11 / low 5） |
| W6 | `质量门禁_m0_postdebt_b11b55e.json`（attempt-7 汇总，见 recheck 033 终态） |

## 影响报告

- Domain/API/schema：无新增；`settings.from_env` DSN 键序对齐为行为变更（部署文档同步；`.env.example` 两键同值，个人部署不受影响）。
- 安全/凭据：主树 tracked 扫描器 high 清零；无凭据变化。
- 兼容性/迁移：CI m0 workflow 已有 postgres service，控制面 PG 装配路径由全量 m0 在隔离库实测。
- 上游：无版本变更；starlette 弃用告警以 pytest filter 处理（不动锁）。
- 下一项任务：无（M18/M19 维持 DEFERRED）。
