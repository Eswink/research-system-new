---
id: RECHECK-20260906-033
plan_id: PLAN-20260906-031
attempt: 10
status: COMPLETED
result: PASS
created_at: 2026-09-06
completed_at: 2026-09-06
reviewer: root-agent-independent-pass
baseline_ref: 87b52e0（PA-1R 记录提交后的起点）
checked_head: 6f195643161e8831c874cd220b97debba4dd12c9
---

# RECHECK-20260906-033 — PA-1R 遗留债务清偿复检

## 冻结范围

任务计划：`.cursor/plans/tasks/PLAN-20260906-031-pa1r-leftover-debt-remediation.md`（W1-W6）。
被测代码固定为完整 commit `6f195643161e8831c874cd220b97debba4dd12c9`
（= 87b52e0 → b11b55e 封闭性加固 → f630b6d/d0b75a7 fixture 规范化 → 141f039 registry
变体 → 6f19564 登记对齐）。独立封存 checkout：`scratch/PA1R闭环v1/续审release-v6/`。

## 检查结果

| Gate | 检查 | 证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | DSN 链对齐（`RESEARCHOS_POSTGRES_DSN` 首位） | `services/api/settings.py`；`test_gateway_dsn_key_leads_canonical_chain` + `test_product_database_url_overrides_ambient_generic_url`（补 delenv）14 passed；部署文档重写 | PASS |
| G-02 | gen_openapi 封闭化（:memory: SQLite，永触不到环境 DSN） | `python -B tools/gen_openapi.py` 重生成后 `git status docs/api/openapi.m13.json` 为空（字节不变）；`test_openapi_snapshot_is_current` 绿 | PASS |
| G-03 | Starlette 弃用告警消除 | `pyproject.toml` filterwarnings；`pytest tests/api/test_settings_otel.py` 输出零告警 | PASS |
| G-04 | 主树扫描器 high 清零（3 项修复 + 前轮 2 项） | 两审计工具改字面 SQL 创建 `pg_temp` 参数化函数（对真实恢复库验证与旧 `sql.SQL().format` 产出**逐字节等价**）；examples 脚本 `Path.write_text` 字节等价（e2e 9/9，0.745 绝对断言 + 相对可复现不变）；registry 字面 TRUNCATE 分发 / pg_crash_restart 字面分支 / 凭据字面量计算常量化（29 测试绿） | PASS |
| G-05 | 密封扫描主树 high = 0 | `scan-2026-09-06T11-34-43.682Z-6a9b17a9dc0a`（seal `sha256:a4813342330d645c161c89a3abe7276554f1bac46365632225f9e3bd8b242b00`）：主树 16 findings = high **0** / medium 11（probes 跨文件污点误报，处置记录不改码）/ low 5（examples 确定性 seed，保留） | PASS |
| G-06 | 登记对齐 | BACKLOG 行 178（BUSY 接线，ab5ffc8 + G-15）/ 180（本计划 + 新 seal）清偿注记；能力表 SI-1/PA-1/PA-1R → DONE；`PA1_MIMOSA_REVIEW.md` 增补 PA-1R 轮处置节 | PASS |
| G-07 | 全量 m0 门禁（attempt-10，release-v6 封存树 @ 6f19564） | `质量门禁_m0_postdebt_6f19564.json`：**59/59 job、2961 测试全绿**（含治理验证 52、docs_consistency 58；DSN 对齐后控制面 PG 装配路径在隔离库实测） | PASS |

## Findings

1. attempt-7 因治理验证（plan-030 DONE 但正文未同步）失败 → 计划正文按规范闭合（勾选/证据/memory_entries/ALL_PLAN 投影）。
2. attempt-8 因 `registry.py` 证据工厂的 truncate 集合未登记字面分支失败 → 141f039 补登记（32 contract tests 绿）。
3. `worker_cross_process.py` 的"acquire_lease 是 sql-injection 入口"为 argv 污点式误报（适配器内 `%s` 参数化正确）；UUID 形状校验作为纵深防御保留，但**扫描器不识别为消毒**——该文件属不可改写消除项，已在 `PA1_MIMOSA_REVIEW.md` 记录性保留。
4. 过程性环境问题（旧 collector 占 22418 / compose 绑定失败容器无映射）按容器重建处理，不影响结论。

## 结论

W1-W6 全部完成，验收条件逐条有真实证据。**主树扫描器 high = 0（密封扫描证实）；
commit 门禁不再有主树既有 high 可采样；全量 m0 门禁在最终 revision 6f19564 全绿。**

PLAN-20260906-031 PASS。剩余为明确保留项（probes medium 处置、examples low、
M18/M19 DEFERRED）。
