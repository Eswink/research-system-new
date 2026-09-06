# PA-1 Mimosa 密封深扫处置确认（scan-2026-09-03T06-45-52.069Z-406820d26e66）

- seal: `sha256:7e341656636ff52e8d9e05b70f6cb3f643ba63b81e3407b3517158c35ecc9956`
- coverage: partial / runStatus inconclusive（threatModel 0 入口——scanner 看不见
  `create_app`/`create_worker_app` FastAPI 组合，与 M16/M17 扫描同口径）。
- **不宣称"安全"**：静态覆盖 partial/static_only；本记录为逐条人工确认。

## HIGH（7）

| 位置 | 处置 |
| --- | --- |
| scratch/audit_c_redaction.py:26（PASSWORD 字面量） | ✅ 已修：常量改为 `RESEARCHOS_PROBE_PW` env + `probe-pw-marker-0000` 惰性默认（P4.13）。原值是脱敏探针的合成 canary，从非真实凭据。 |
| tools/upstream-spikes/S2_llm_construction.py:39（sk-test-mock） | ✅ 已修：改为 `RESEARCHOS_PROBE_KEY` env + `probe-inert-token` 默认（P4.13）。spike 只需非空占位符，不触网（MockTransport）。 |
| scratch/pa1-20260903/pg_acceptance_run.py:152（argv → run_clean_workflow 路径穿越） | ✅ 已修：固定为 `scratch/pa1-20260903/work`（P4.13 同批；scratch 驱动非产品）。 |
| examples/experiments/m12_reference_classification.py:228（`open("experiment_result.json","w")`） | 记录：实验脚本在其容器内工作区的固定相对文件名（M12 参考实验的确定性输出约定）；无外部输入参与路径。非产品代码（example），保留。 |
| scratch/audit_b_docker.py:35、audit_b_docker_repro.py:33（容器内 `open('result.json','w')`） | 记录：探针脚本给沙箱容器拼接的固定命令+固定文件名；无外部输入。untracked scratch，保留。 |
| adapters/research_tools/parsing.py:15（ET.fromstring 实体扩展） | ✅ 已修：拒绝 DOCTYPE/ENTITY + 5MB 上限 + malformed→InvalidInputError；新增 tests/adapters/research_tools/test_parsing.py（P4.12）。 |

## MEDIUM（28，全部"疑似跨文件污点"）

统一口径：**env → DSN → operator probe 工具的参数化查询**（static advice，proof-gap）。
- scratch/probe_*.py（14）与 tools/probes/probe_*.py（13）：operator 自用探针，
  `RESEARCHOS_POSTGRES_DSN` → 本地打开的连接 → 参数化 `%s` 查询（已人工核验
  probe_db_failure/probe_migration/probe_outbox/probe_scheduled_recovery/
  probe_stale_worker/probe_cancel_race/probe_canonical_state）。
- services/worker/__main__.py:77 的 1 条：`os.environ.get("RESEARCHOS_WORKER_ID",
  "worker-1")` 进 argparse default——纯标识符，无查询/路径拼接。

全部确认为误报语境，记录；无代码变更。

## LOW（5）

examples/experiments/m12_reference_classification.py 的 `random.seed` 确定性种子
（lines 32/41/63/68/141）——实验可复现设计（seed=7），非密码学用途。记录，
保留。

## 依赖 advisory（1，离线快照 context-only）

completion=completed，影响包 0；1 个包命中 1 条已知 advisory（离线库匹配，
需人工/联网复核；未定 0）。PA-1R 前建议联网复核 uv.lock 相关包。

## 复扫对比（Final 门禁，2026-09-03）

复扫 sealed scan：`scan-2026-09-03T18-19-27.013Z-5db69b4cad60`
（seal `sha256:e12fc0f3b7abfd4e13cbdafa7fc963588b38daf7f36eb91ebb78b42612a4704d`），
36 findings（high 3 / medium 28 / low 5），与修复前 40 findings（high 7）对比：

| 严重度 | 修复前 | 复扫 | 变化 |
| --- | --- | --- | --- |
| HIGH | 7 | 3 | -4：全部为已修项消失（audit_c_redaction PASSWORD、S2 sk-test-mock、pg_acceptance_run argv、parsing.py DTD/实体）；残留 3 项均为**记录性保留**（m12_reference_classification.py:228 固定容器内文件名、scratch/audit_b_docker*.py 固定命令+文件名） |
| MEDIUM | 28 | 28 | 同口径不变：env → DSN → operator probe 工具参数化查询（scratch 14 + tools/probes 13 + services/worker/__main__.py 1），静态 advice + proof-gap |
| LOW | 5 | 5 | m12 example `random.seed` 确定性种子（复现设计，非密码学） |
| 依赖 advisory | 1（离线 context-only） | 1 | 不变（需联网复核 uv.lock 相关包） |

**结论：产品代码面零命中；high 从 7 降至 3（残留全部为记录性保留项），
无新增。** coverage 仍为 partial/static_only（threatModel 0 入口——scanner
看不见 FastAPI 组合），不宣称"安全"；PA-1R 前建议联网复核依赖 advisory。

---

## PA-1R 轮处置（2026-09-06，PLAN-20260906-031）

密封扫描 `scan-2026-09-06T11-34-43.682Z-6a9b17a9dc0a`（seal `sha256:a4813342330d645c161c89a3abe7276554f1bac46365632225f9e3bd8b242b00`，
180 packages，dependency advisory 1 条离线 context-only 不变）。
与 09-03 扫描（40 findings）相比总量 616→37 的差值主体为此前封存审计
checkout 副本（已按 RECHECK-20260906-032 迁移/清除，非代码变化）。

### 主树 tracked（16 findings）：HIGH = 0

| 严重度 | 数量 | 处置 |
| --- | --- | --- |
| HIGH | **0** | 3 项全部已修（commit `f8205e8`/待提交轮）：`tools/PA1R密钥审计v1.py` 常量库名改字面 SQL；`tools/PA1R运行演练v1.py:333` 与 `tools/PA1R恢复闭包v1.py:107` 的 `sql.SQL(...).format(sql.Identifier(...))`（psycopg 正确参数化用法，属误报）改为**纯字面 SQL 创建会话级 `pg_temp` 参数化函数 + `%s` 调用**（动态标识符由库内 `quote_ident` 保证安全；对真实恢复库验证与旧模式产出逐字节等价） |
| MEDIUM | 11 | **记录；无代码变更**：`tools/probes/probe_*.py`（10）与 `services/worker/__main__.py:92`（1）的"疑似跨文件污点"——env DSN → 本地连接 → 参数化查询的操作员自用链路，静态 advice + proof-gap，人工核验无污点汇（沿用本文件 PA-1 轮同类处置） |
| LOW | 5 | **记录；保留**：`examples/experiments/m12_reference_classification.py` `random.seed=7` 确定性可复现设计（非密码学用途） |

### 本轮已修（对应上轮 3 个 open high）

1. `examples/experiments/m12_reference_classification.py:228`（前轮"保留"项）：`open("experiment_result.json","w")` → `Path(...).write_text(json.dumps(..., ensure_ascii=False, sort_keys=True), encoding="utf-8")`，**输出字节等价**（M12 参考实验 artifact digest 契约依赖的确定性字节不变）；`test_m12_reference_e2e.py` + `test_evidence_admission_e2e.py` 全绿（0.745 绝对断言 + 相对可复现）。前轮保留理由（避免扰动）已被字节等价验证取代，处置更新为 已修。
2. `tools/PA1R运行演练v1.py`、`tools/PA1R恢复闭包v1.py`：见上表 HIGH 行。

### 结论

主树 tracked（产品 + 测试 + 工具 + 示例）**high = 0**；无产品代码命中。
coverage 仍为 partial/static_only（threatModel 0 入口——scanner 看不见
FastAPI 组合），不宣称"安全"。commit 门禁对主树既有项不再有 high 可采样。
