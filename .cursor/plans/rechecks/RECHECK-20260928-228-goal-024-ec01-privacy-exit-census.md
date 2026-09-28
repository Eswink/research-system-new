---
id: RECHECK-20260928-228
slug: goal-024-ec01-privacy-exit-census
title: GOAL-024 EC-01 复检：非 canonical 出口清单是「受判 ∪ 带理由豁免」的分区（113 候选全覆盖）+ 四向按压先红后绿 + 逐字节复原
plan_id: PLAN-20260928-227
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-228 — GOAL-024 EC-01 复检

**复检口径**：不复用 PLAN 的叙述；每项给出**可复核观察面**；**未实跑的不记通过**。
本轮最要紧的一件事是：**清单是分区，而分区会自审** —— 判据**第一次自跑**就抓到两处
**自己清单里的真错**（重复分类 + 形态自检样本写错），两处都当场修掉（见第五节）。

## 检查结果

### 一、交付面（可复核观察面）

| 交付物 | 观察面 | 结论 |
| --- | --- | --- |
| `tests/observability/privacy_exit_census.py`（**259 行**，无超 50 行函数） | AST 形态谓词 + 扫描根 + 分区/清单/下界的机械部分；`discover_emitters` **lru_cache** 化的只读普查 | 成立 |
| `tests/observability/test_privacy_exit_census.py`（**407 行**，无超 50 行函数） | `EXIT_SURFACES` / `EXEMPT_PRODUCERS` / `REQUIRED_JUDGED_EXITS` / `CANARY_SOURCES` / `UNCOVERED_SHAPES` 全部**写在判据源码里**；13 例 | 成立 |
| 普查剖面（`discover_emitters` 实跑） | **113 个候选**：`application_log` 2 / `stdout` 4 / `otlp_span` 12 / `otlp_metric` 11 / `disk_write` 8 / `read_face` 29 / `failure_payload` 47 | 成立 |
| 分类剖面 | 受判出口 **6**（`otlp-traces-wire` / `otlp-metrics-wire` / `application-log` / `read-face-http` / `failure-payload` / `disk-run-artifacts`）+ 豁免出口 **1**（`stdout-stderr`，默认进程内路径**零生产点**）+ 豁免生产者 **25** 条（逐条带理由）| 成立 |
| 六类金丝雀源 + 失败消息 | `CANARY_SOURCES` 声明 7 源，判据断言含 GOAL 要求的六类与 `failure_message` | 成立 |
| 未机械枚举的形态 | `UNCOVERED_SHAPES` **4** 条逐条带理由（显式 open 写、目录镜像、DB 文件、出站请求体） | 成立 |

**口径边界（必须连同清单一起读）**：canonical state（PG 域实体 / SQLite 域表）
允许持有用户自己的任务输入 —— **不是泄漏**；本清单只管**非 canonical 出口**。

## 二、四向按压（**先红后绿 + 逐字节复原**）

| # | 按压 | 观察到的红 | 复原证据 |
| --- | --- | --- | --- |
| P1 | **在真实产品根新建一个只含 `print` 的模块**（`packages/application/observability/press_probe_module.py`） | `未分类的非 canonical 出口:packages/application/observability/press_probe_module.py [stdout]` ⇒ `1 failed, 12 passed` | 删除该文件后 `git status --porcelain -- packages/application/observability/` **为空**、判据 **13 passed** |
| P2 | 从 `otlp-traces-wire` 的显式生产者清单里**删掉一行**（`services/api/scheduler.py`） | `未分类的非 canonical 出口:services/api/scheduler.py [otlp_span]` ⇒ `1 failed, 12 passed` | 复原后 raw `sha256` = `076fad378c48c794df3fa4e672614a7e379f10bc69f2e81d7eb5e7ce42aac74f` **与按压前相同**（`MATCHES_BASELINE True`）⇒ 13 passed |
| P3 | 把 `_REASON_CLI` **抽空** | `豁免生产者 adapters/cli/eval_gate.py [disk_write]: 缺少理由` + `[stdout]` 两条 ⇒ `1 failed, 12 passed` | 复原后 raw `sha256` 同上 **逐字节相同** ⇒ 13 passed |
| P4 | 往 `REQUIRED_JUDGED_EXITS` 里**加一条非受判 id**（`stdout-stderr`） | `必备受判出口缺失:['stdout-stderr']` ⇒ `1 failed, 12 passed` | 复原后 raw `sha256` 同上 **逐字节相同** ⇒ 13 passed |

**按压全部用 Edit 工具**（Bash 写源码被 Mimosa 拦截），**逐字节证据用 raw `sha256` + 二进制读**
（承 MEM-152：`git diff` 会因行尾归一化掩盖差异，不得充当逐字节证据）。
P1 是**真实树**按压（不是合成候选集）：判据在**真实产品根**上抓到了新增出口。

## 三、非空转（承 MEM-156）

- 判据断言**候选 ≥ 50**（实测 113）且**命中形态 ≥ 6**（实测 7）⇒ 空发现会让判据**判红**，不是空真。
- 交付清单里**受判出口 6 条 ≥ 5**、每条都有**生产者清单**与**观测方式**（`surface_findings` 兜底）。
- **七种形态各有一段同源正样本**（`ast.parse` 内存样本）⇒ 谓词静默失效即红。
- 反证组（未分类 / 重复分类 / 陈旧 / 空理由 / 受判面无观测方式 / 下界收缩）**各自 1 例**，
  全部在**合成候选集**上跑（不碰文件系统）。

## 四、四道门与既有判据

| 检查 | 结果 |
| --- | --- |
| `ruff format --check` | `2 files already formatted` |
| `ruff check` | `All checks passed!` |
| 规模（450 行文件 / 50 行函数） | 259 / 407 行，超 50 行函数 **0** 个（407 > 300 触发**软告警**，如实登记） |
| `mypy`（strict） | `Success: no issues found in 2 source files` |
| 既有隐私判据 `test_privacy_canary.py` | **逐字节未改**且全绿（与新政判据合跑 `20 passed` = 13 新 + 7 既有） |

## 五、本轮抓到的两处**自己的**真错（当场修掉）

1. **重复分类**：`adapters/otel/failsafe.py [otlp_metric]` 同时被受判面 `otlp-metrics-wire`
   与豁免面认领 ⇒ 判据报 `重复分类的非 canonical 出口:… -> ['exempt:…', 'otlp-metrics-wire']`。
   **处置**：从豁免面移除该条（它是 sink 自身的计数面，属受判的 metrics wire）。
2. **形态自检样本写错**：`read_face` 的样本写成赋值式（`f = router.get('/x')(f)`），
   而谓词认**装饰器**位形 ⇒ 自检报 `形态谓词失效:read_face`。**谓词是对的、样本是错的**；
   **处置**：按真实装饰器形态重写样本。

⇒ 这两条正是「**分区 + 每形态正样本**」的价值：它们把清单错误变成**交付前可观测的红**。

## 结论

**EC-01 = PASS**（`PASS_WITH_WARNINGS`）：出口清单是**分区**（113 候选 → 受判 6 / 豁免 25 +
豁免出口 1，未覆盖面 4 条带理由），四类异常各自判红且**四向按压**先红后绿并**逐字节复原**；
判据自跑抓到并修掉了两处**自己的清单错**。**未实跑的不记通过**：`stdout-stderr` 的
「对内容可见」与全部受判出口的**零命中扫描**都留给 **EC-02**（本 EC 只交付扫描面）。

## 六、如实登记的警告

- **`W-1`｜普查是「形态驱动」的，不是「全部写路径」的**：`UNCOVERED_SHAPES` 里 4 条
  （显式 `open` 写、目录镜像、DB 文件、出站请求体）**本轮不判**；`disk-run-artifacts` 的
  受判生产者**只有 1 条**（`adapters/sqlite/artifact_store.py`）⇒ 磁盘面射程**窄**。
- **`W-2`｜`stdout-stderr` 是豁免出口**：默认进程内路径**零生产点**（这不是遗漏，是实测），
  其「对内容可见」只能靠 EC-02 的**正控制**证明，本 EC **不**提供该证据。
- **`W-3`｜豁免理由是「有理由的登记」，不是证明**：25 条豁免生产者按
  worker / CLI / 容器 / postgres / 真实 relay / 真实 runtime / 独立应用 / 词汇层 分组给理由，
  但**没有**机械证明它们**永不**进入默认路径（如组合根被改写）。
- **`W-4`｜射程只看 `(module, kind)`**：同一模块内**新增同形态发射点**（第 2 个 `print`）
  **不**产生新的分类需求 ⇒ 漏的是「位置」而非「形态」。
- **`W-5`｜403 行触发的软告警**：`test_privacy_exit_census.py` 407 行 > 300 ⇒ 既有规模判据
  会打 `UserWarning`（**不是**失败）；如实登记，未为消除告警而拆文件。
- **`W-6`｜不含任何认证面 / 授权面结论**：本轮**零**认证、策略、门禁语义改动。
