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

## 与产品改动的交集

本次扫描后本批修复引入的产品改动（memory gate、PG 重连、event publisher 提交、
NCBI 解析、BUSY 接线等）将以新的密封深扫（Final 门禁）重新覆盖；目标：
除上述记录性/静态 advice 外无新增 high。
