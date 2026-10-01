# Mimosa 深扫终态记录（2026-10-01）

> 处置记录，对应 `scan-2026-10-01T07-47-51.288Z-3fce4de3077a`。
> **不主张项目安全**：扫描是 static-only、coverage=partial、`verdictEffect=none`；`R-M1` 未收口。

## 1. 扫描回执

| 项 | 值 |
| --- | --- |
| scanId | `scan-2026-10-01T07-47-51.288Z-3fce4de3077a` |
| seal | `sha256:66c19cdf656595ddee577628afc3f57c4783634dc4870ac1bb5ba24b738ad8eb`（覆盖 scan-manifest / findings / coverage 三份语义产物） |
| 产物目录（仓库外） | `C:\Users\googl\.mimosa\security-scans\project-c96f90c714f9f3dc0bd2d97f\scan-2026-10-01T07-47-51.288Z-3fce4de3077a` |
| depth | deep |
| runStatus / completeness | inconclusive / partial |
| evidenceBoundary / verdictEffect | static_only_no_runtime_execution / none |
| 源面 | selected 3097 / parsed 3097；truncated=false；read/parse failures 0 |
| 阶段状态 | threatModel partial（0 入口 / 0 主体 / 0 授权面）；findingDiscovery partial；validation completed（investigated 0）；pathAnalysis completed（11224 函数 / 5915 调用边 / 0 traces）；reporting completed |
| findings | 36：high 1 / medium 28 / low 7；businessLogic 0；suppressedTestContext 10 |

本次为「工作树全量 + 四个在改文件点名」运行。四个点名文件（`apps/web/src/features/models/ModelDetails.tsx`、`packages/domain/model_drift.py`、`services/api/dto/models.py`、`services/api/middleware.py`）**零命中**；且复核证实它们的 git-status「M」是纯 CRLF/LF 行尾差异（内容与 HEAD 逐字节相同，`git diff` 为空补丁）——与安全面无关，不构成本轮 finding。

## 2. 与上一轮的关系

同族记录：`docs/audits/MIMOSA_DEEP_SCAN_20260917.md`（36 = 3/28/5）、`docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md`（干净树 25 = 1/19/5）、`docs/audits/PA1_MIMOSA_REVIEW.md`（五轮台账）。本轮 36 条与 0917 类别分布相同；相对 0918 的差异：

| 变化 | 内容 |
| --- | --- |
| 新增 LOW ×2 | `examples/experiments/exact_match_index_benchmark.py:41`、`examples/experiments/sort_analysis_baseline.py:35`（GOAL-027 期间的确定性实验脚本；同一误报理由，见 §3.3） |
| 其余 34 条 | 与既有台账同形态（HIGH ×1、MEDIUM ×28、LOW ×5 在 m12） |

## 3. findings 逐类处置（36 条 occurrence）

### 3.1 HIGH ×1（insecure-deserialization）

- `packages/application/protocol_authoring/service.py:103`。判定：**误报（构造性证伪 + 测试钉住）**。
  实际加载器是 `yaml.SafeLoader` 的子类（同文件 :83 `class _StrictLoader(yaml.SafeLoader)`），仅追加重复键拒绝钩子与 5 MB 尺寸上限；不使用 FullLoader/Loader。反回归判据在 `tests/application/protocol_authoring/test_draft_service.py`（本机实跑 **13 passed**）：`!!python/*` 标签拒执行、loader 子类断言、重复键拒绝、尺寸上限。
- 无代码变更（改成 safe_load 会丢重复键拒绝钩子，属判据削弱）。

### 3.2 MEDIUM ×28（跨文件污点启发式）

分三组（行号取本次 findings.json 的 occurrence）：

- `scratch/` ×17（未跟踪探针）：probe_cancel_race.py:63、probe_canonical_state.py:84、probe_db_failure.py:76,121、probe_migration.py:74,100,124,126,130,140,146、probe_outbox.py:78,114、probe_scheduled_recovery.py:93,132、probe_stale_worker.py:95,124
- `tools/probes/` ×10（已跟踪）：probe_cancel_race.py:73、probe_canonical_state.py:96、probe_db_failure.py:100,140、probe_outbox.py:90,127、probe_scheduled_recovery.py:100,142、probe_stale_worker.py:103,134
- `services/worker/__main__.py:135`（汇点签名 = `adapters/execution/gpu_probe.py:138` 的路径穿越）

判定：**全部误报**。

- 共同形状（前两组）：源 = 环境变量（这些探针里是 `RESEARCHOS_POSTGRES_DSN` 连接串，见 `tools/probes/probe_cancel_race.py:36` 形态），汇点 = `adapters/postgres/db.py` 的 `migrate()` 执行行。逐行核对：SQL 文本来自仓库内 migrations 文件与字面量（唯一带参语句是 `%s` 参数化 INSERT）；**DSN 是连接目标，不是 SQL 文本**。
- AST 反证（结构性，`tools/probes/probe_dynamic_sql_forms.py`）：`--selftest` ⇒ 8/8 分类正确；`--root packages --root services --root adapters` ⇒ 532 个文件、22 处字符串构造的 execute 首参，全部为模块常量 / 字面量迁移字典 / 绑定 `%s`（与 0918 的 22 处同值），`tools/` 内 0 处。
- gpu 那条：路径汇点实为 `tempfile.mkdtemp` 的隔离目录（`adapters/execution/gpu_probe.py:148`），路径成分不含外部输入。

### 3.3 LOW ×7（insecure-randomness）

`examples/experiments/m12_reference_classification.py:33,42,64,69,142`（既有五条）、`examples/experiments/exact_match_index_benchmark.py:41`、`examples/experiments/sort_analysis_baseline.py:35`（本轮新增两条）。

判定：**误报**。全部是实验脚本的 `random.Random(seed)` 确定性语料生成——固定种子是**可复现配置**要求，不生成任何秘密/令牌；代码内注释已写明。无变更。

**小结：36/36 为误报或范围外，未发现产品代码缺陷；本轮无代码变更。**

## 4. 依赖 advisory 复核（本机实跑，OSV）

- 复跑路径：`tools/probes/probe_dependency_advisories.py`（离线构建 413 个查询；探针自身零网络代码）+ 唯一出网步骤 `curl` POST `https://api.osv.dev/v1/querybatch`（公开只读端点、无凭据、无个人数据）。
- 锁定面：`uv.lock` `sha256:98af1c42…3390`（149 包，与 0918 证据**逐字节相同**）；`pnpm-lock.yaml` `sha256:f857c70b…5cca`（264 包，自 0918 后已更新——`vite` 6.4.3 / `yaml` 2.8.4 已由 GOAL-016/018 消化）。
- 结果：**hitCount=4**（0918 为 3），共 32 条 advisory：
  - **pyjwt 2.13.0**（`mcp` 1.29.0 传递依赖）：13 条，含 **1 critical**（GHSA-ffc3-869f-jxw9，修复版 2.14.0；一条需 2.15.0）。全部 published 2026-09-29…10-01 ⇒ 0918 之后**新出现**。
  - **urllib3 2.7.0**（`docker` 7.2.0 / `requests` 2.34.2 传递依赖）：3 条（2 high），修复版 2.8.0。2026-09-30 发布。
  - **brace-expansion 5.0.9**（dev 链：eslint → `minimatch` 10.2.6）：3 条（2 high），修复版 5.0.10/5.0.11/5.0.12。2026-09-29 发布。
  - **undici 5.29.0**（`@cursor/sdk` 1.0.30 传递，dev 链）：13 条（相对 0918 的 12 条 +1：GHSA-r53p-7pc4-xj5r，LOW）。
- 处置：**本轮不改任何 pin**。依赖版本变更不在本轮授权范围内（undici 属已拍板的 D-03「维持现状」；pyjwt / urllib3 / brace-expansion 为上轮之后新出现，建议单独授权评估升级，见 §6）。
- 证据落盘：`docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20261001.json`（逐条 id / CVE 别名 / severity / 修复版本 / 来源 URL；复跑命令内嵌）。
- 附注：扫描器自带依赖相（182 包 / offline 命中 1）**不可用作证据**（口径同 0918：无署名）；本节 OSV 复核取代之。

## 5. 未覆盖范围（逐条明写，不夸大）

- **static only**：无运行时验证（`evidenceBoundary=static_only_no_runtime_execution`）；本记录不做可利用性结论。
- **threatModel partial**：0 入口 / 0 主体 / 0 授权面 ⇒ 授权面与业务逻辑面**零覆盖**。
- **输入面**：工作树扫描（含未跟踪 / 被 ignore 的本地资产，如 `scratch/` 探针与本机 `.venv` 之外）；仓库外 `~/.mimosa/` 状态不在扫描面内。
- **不覆盖**：读面未认证 / 多租户 / BOLA·BFLA / 部署面（承继 GOAL-027 的未覆盖清单）。
- **hook 侧 L3**：`scanner_enobufs` 属 D-04「维持现状」；`R-M1` 未收口，不得据此宣称项目安全。

## 6. 残余与决策引用

| 事项 | 状态 | 引用 |
| --- | --- | --- |
| 本轮 36 条 findings | 全部误报/范围外；无代码变更、无门禁改动 | 本文 §3 |
| pyjwt / urllib3 / brace-expansion | **新增** advisory（1 critical + 4 high）；未处置，升级 pin 需**单独授权** | 本文 §4；口径同 D-03（依赖 pin 变更需授权） |
| undici | 维持现状（已拍板） | `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` D-03 |
| hook 检测层 | 维持现状（已拍板） | 同上 D-04 |
| `R-M1`（`scanner_enobufs`） | 原样保留 | 同上 |

## 7. 复跑命令

```bash
# 密封扫描（外部 MCP 通道）
#   security_scan_start(project=D:\research-system, depth=deep)
#   security_scan_status(jobId=...)  ⇒ scanId + seal + 产物目录

# findings 复核（本记录 §3）
uv run --frozen --no-sync python -B tools/probes/probe_dynamic_sql_forms.py --selftest
uv run --frozen --no-sync python -B tools/probes/probe_dynamic_sql_forms.py \
    --root packages --root services --root adapters
uv run --frozen --no-sync python -B -m pytest \
    tests/application/protocol_authoring/test_draft_service.py -q

# 依赖 advisory 复核（本文 §4）
uv run --frozen --no-sync python -B tools/probes/probe_dependency_advisories.py --root . > batches.jsonl
curl -s -X POST https://api.osv.dev/v1/querybatch \
     -H 'Content-Type: application/json' --data @batches.jsonl > response.json
uv run --frozen --no-sync python -B tools/probes/probe_dependency_advisories.py \
    --root . --responses response.json
```

---

本记录是处置与证据，不是安全结论；**不主张项目安全**，也不得把「扫描干净」读成「无漏洞」。
