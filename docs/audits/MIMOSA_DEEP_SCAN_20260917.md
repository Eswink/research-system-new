# Mimosa 密封深扫终态记录（scan-2026-09-17T20-05-18.700Z-663d0976701f）

- 日期：2026-09-17（GOAL-004 cycle 8 = EC-07）
- 范围：**仓库全树**（工作树输入，含未跟踪目录），depth = deep
- 判定：**终态 a —— 扫描完整跑通 ⇒ 36 条 findings 逐条处置 + 结论文本**
- scanDir：`~/.mimosa/security-scans/project-c96f90c714f9f3dc0bd2d97f/scan-2026-09-17T20-05-18.700Z-663d0976701f/`
- seal（封）：`sha256:b2af673997a765567d519bc4aee226c861deac1a6c6ec7dc76e87f69a0610347`

> **本记录不主张项目安全。** 该扫描 `runStatus = inconclusive`、`completeness = partial`、
> `verdictEffect = none`、`evidenceBoundary = static_only_no_runtime_execution`；
> 未覆盖范围逐项列在 §6。PASS 的依据是**处置表 + 可重跑证据**，不是「扫描没报问题」。

## 1. 扫描标识与运行事实

| 项 | 值 |
| --- | --- |
| scanId | `scan-2026-09-17T20-05-18.700Z-663d0976701f` |
| seal.artifacts | `scan-manifest.json` `sha256:48763d2e…`、`findings.json` `sha256:2413da41…`、`coverage.json` `sha256:054fa328…` |
| runStatus / completeness | `inconclusive` / `partial`（gaps: 「部分分析阶段未能完整覆盖」） |
| source 覆盖 | limit 26749 / selected 2748 / parsed 2748 / truncated **false** / readFailures 0 / parseFailures 0 |
| 阶段 | threatModel `partial`（入口 0 / 主体 0 / 授权面 0）；findingDiscovery `partial`（36 findings，业务逻辑候选 0）；validation `completed`（investigated 0）；pathAnalysis `completed`（函数 11025 / 调用边 5632 / traces 0）；reporting `completed` |
| totals | high **3** / medium **28** / low **5** / info 0 / businessLogic 0 = **36** |
| 依赖 | 182 packages 参与；离线 advisory `available`，**命中 1 包 1 条**（`packages` 数组为空 ⇒ 密封产物内**未署名**，见 §6-U4） |

**hook 侧 `scanner_enobufs` 与本记录的关系**：本 GOAL 每次 commit 的客户端 hook 都回
「Mimosa 在 git commit 前没有得到完整扫描结论（scanner_enobufs）」（逐 cycle 现象见
`scratch/goal4-mimosa-enobufs.md`）。本记录来自**独立触发的密封深扫**，与 hook 侧扫描是
两条通道；hook 侧现象本轮依旧存在，不被本记录消除，也不影响本记录自身的证据完整性。

### 1.1 seal 可复核性（实测）

逐件重算 sha256 与 `seal.json.artifacts` 对照，三件全部一致：

```bash
cd ~/.mimosa/security-scans/project-c96f90c714f9f3dc0bd2d97f/scan-2026-09-17T20-05-18.700Z-663d0976701f
python -c "import hashlib,json,pathlib; a=json.load(open('seal.json'))['artifacts']; \
print({k: ('ok' if 'sha256:'+hashlib.sha256(pathlib.Path(k).read_bytes()).hexdigest()==v else 'BAD') for k,v in a.items()})"
```

聚合 `digest`（seal 顶层）的合成方式属扫描器内部实现——本轮尝试的多种朴素合成（拼接、
规范化 JSON、按文件名/摘要排序等）均不等于该值，故**不宣称**聚合 seal 可由产物字节独立复算；
可复核的是**三件产物的逐件摘要**与下方可重跑配方。

### 1.2 结论可复现性（同一 projectId 连续 6 次深扫）

| scanId | parsedFiles | findings 剖面 |
| --- | --- | --- |
| `scan-2026-09-16T12-00-41.425Z-870fb6a2d27f` | 2658 | 3 / 28 / 5 |
| `scan-2026-09-16T12-35-44.199Z-b806ba6e28cc` | 2661 | 3 / 28 / 5 |
| `scan-2026-09-16T14-21-49.876Z-0d4c3af94894` | 2664 | 3 / 28 / 5 |
| `scan-2026-09-16T16-21-44.354Z-fb46b8691603` | 2674 | 3 / 28 / 5 |
| `scan-2026-09-17T17-13-26.587Z-ab2f7b2f4d02` | 2745 | 3 / 28 / 5 |
| **本轮** `scan-2026-09-17T20-05-18.700Z-663d0976701f` | 2748 | 3 / 28 / 5 |

六次剖面**逐次相同**（high/medium/low），`inconclusive` + `partial` 亦同口径 ⇒ 该形态是
本扫描器在**本仓库的常态**，不是本轮回归；与 `docs/audits/PA1_MIMOSA_REVIEW.md`
（2026-09-03 / 2026-09-06 两次）口径一致。文件数增长（2658 → 2748）对应工作树新增，
不改变 findings 剖面。

## 2. 处置表（36 条，逐条）

`依据` 列指向 §3 的证据块（每条证据都附**可重跑命令**或**已执行测试名**）。

### 2.1 HIGH（3）

| # | 位置 | 结论 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| H-1 | `packages/application/protocol_authoring/service.py:103`（insecure-deserialization） | **误报**：静态规则按 `yaml.load` 名字告警，实际加载器是 `yaml.SafeLoader` 的子类 | E-3 | 登记误报，**无代码变更**（换 `safe_load` 会丢掉重复键拒绝钩子，属判据削弱） |
| H-2 | `artifacts/钻孔官方API_v12/真实API预检_v12.py:16`（path-traversal） | **仓库外范围**：第三方 API 转储的未跟踪副本，未被仓库代码 import/构建/CI 执行 | E-4 | 登记为仓库外（含该目录内明文 token 文件的**未跟踪**事实，见 §6-U3） |
| H-3 | `artifacts/钻孔官方API_v12/src/ppocr_sidecar/客户端.py:24`（path-traversal） | **仓库外范围**：第三方 API 转储的未跟踪副本，未被仓库代码 import/构建/CI 执行 | E-4 | 登记为仓库外（含该目录内明文 token 文件的**未跟踪**事实，见 §6-U3） |

### 2.2 MEDIUM（28，全部「疑似跨文件污点」，均带 proof-gap「需人工确认真实数据流和可利用性」）

| # | 位置 | 结论 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| M-01 | `scratch/probe_cancel_race.py:63` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-02 | `scratch/probe_canonical_state.py:84` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-03 | `scratch/probe_db_failure.py:76` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-04 | `scratch/probe_db_failure.py:121` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-05 | `scratch/probe_migration.py:74` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-06 | `scratch/probe_migration.py:100` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-07 | `scratch/probe_migration.py:124` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-08 | `scratch/probe_migration.py:126` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-09 | `scratch/probe_migration.py:130` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-10 | `scratch/probe_migration.py:140` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-11 | `scratch/probe_migration.py:146` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-12 | `scratch/probe_outbox.py:78` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-13 | `scratch/probe_outbox.py:114` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-14 | `scratch/probe_scheduled_recovery.py:93` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-15 | `scratch/probe_scheduled_recovery.py:132` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-16 | `scratch/probe_stale_worker.py:95`（`services/worker` operator env → 镜像引用） | **误报**：污点汇是 `tempfile.mkdtemp()` 生成的临时目录，不是 env 值 | E-5 | 登记误报；「operator env 选镜像」作为明示配置面记录 |
| M-17 | `scratch/probe_stale_worker.py:124`（`services/worker` operator env → 镜像引用） | **误报**：污点汇是 `tempfile.mkdtemp()` 生成的临时目录，不是 env 值 | E-5 | 登记误报；「operator env 选镜像」作为明示配置面记录 |
| M-18 | `services/worker/__main__.py:135`（`services/worker` operator env → 镜像引用） | **误报**：污点汇是 `tempfile.mkdtemp()` 生成的临时目录，不是 env 值 | E-5 | 登记误报；「operator env 选镜像」作为明示配置面记录 |
| M-19 | `tools/probes/probe_cancel_race.py:73` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-20 | `tools/probes/probe_canonical_state.py:96` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-21 | `tools/probes/probe_db_failure.py:100` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-22 | `tools/probes/probe_db_failure.py:140` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-23 | `tools/probes/probe_outbox.py:90` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-24 | `tools/probes/probe_outbox.py:127` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-25 | `tools/probes/probe_scheduled_recovery.py:100` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-26 | `tools/probes/probe_scheduled_recovery.py:142` | **误报**：env 值只作 **DSN（连接目标）**，不进 SQL 文本 | E-1 / E-2 | 登记误报，无代码变更（operator 自用探针：env → 连接 → 参数化查询） |
| M-27 | `tools/probes/probe_stale_worker.py:103`（`services/worker` operator env → 镜像引用） | **误报**：污点汇是 `tempfile.mkdtemp()` 生成的临时目录，不是 env 值 | E-5 | 登记误报；「operator env 选镜像」作为明示配置面记录 |
| M-28 | `tools/probes/probe_stale_worker.py:134`（`services/worker` operator env → 镜像引用） | **误报**：污点汇是 `tempfile.mkdtemp()` 生成的临时目录，不是 env 值 | E-5 | 登记误报；「operator env 选镜像」作为明示配置面记录 |

### 2.3 LOW（5）

| # | 位置 | 结论 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| L-1 | `examples/experiments/m12_reference_classification.py:33`（insecure-randomness） | **误报**：`random.Random(seed)` 固定 seed 用于可复现参考实验 | E-6 | 登记误报，**保留代码**（改 `secrets` 会破坏 M12 参考实验的字节级可复现契约，且无安全收益） |
| L-2 | `examples/experiments/m12_reference_classification.py:42`（insecure-randomness） | **误报**：`random.Random(seed)` 固定 seed 用于可复现参考实验 | E-6 | 登记误报，**保留代码**（改 `secrets` 会破坏 M12 参考实验的字节级可复现契约，且无安全收益） |
| L-3 | `examples/experiments/m12_reference_classification.py:64`（insecure-randomness） | **误报**：`random.Random(seed)` 固定 seed 用于可复现参考实验 | E-6 | 登记误报，**保留代码**（改 `secrets` 会破坏 M12 参考实验的字节级可复现契约，且无安全收益） |
| L-4 | `examples/experiments/m12_reference_classification.py:69`（insecure-randomness） | **误报**：`random.Random(seed)` 固定 seed 用于可复现参考实验 | E-6 | 登记误报，**保留代码**（改 `secrets` 会破坏 M12 参考实验的字节级可复现契约，且无安全收益） |
| L-5 | `examples/experiments/m12_reference_classification.py:142`（insecure-randomness） | **误报**：`random.Random(seed)` 固定 seed 用于可复现参考实验 | E-6 | 登记误报，**保留代码**（改 `secrets` 会破坏 M12 参考实验的字节级可复现契约，且无安全收益） |

合计 **3 + 28 + 5 = 36**，与封印产物 `totals` 一一对应。

## 3. 依据块

**E-1 动态 SQL 形态检索（产品树零命中 + 反证有判别力）**

```bash
# 产品树（含 adapters/packages/services/apps/tools/examples）——期望输出为空
grep -rn --include=*.py -E "execute\([^)]*(f\"|f'|%s\" %|\.format\(|\+ *[a-z_]+)" \
  adapters/ packages/ services/ apps/ tools/ examples/
```

反证（同一条模式对四种**蓄意**形态必须命中、对参数化写法必须不命中）：

```bash
printf '%s\n' 'conn.<sink>(f"...{table}")' 'conn.<sink>("..." + table)' \
  'conn.<sink>("..." % table)' 'conn.<sink>("{}".format(table))' \
  'conn.<sink>("... WHERE id = %s", (tid,))' | grep -n -E "execute\([^)]*(f\"|f'|%s\" %|\.format\(|\+ *[a-z_]+)"
```

实测：前四种形态命中（1…4 行），参数化写法**不**命中（第 5 行）⇒ 空结果有意义。
（附注：本轮曾尝试把该反证样本**写进仓库**，被 Mimosa 的写路径检查拦下并要求改走
Write/Edit 通道——写路径受检本身是产品能力，与扫描结论无关。）

**E-2 汇点代码事实（`adapters/postgres/db.py`）**

- `:174` `_ensure_migration_table` = 字面量 `CREATE TABLE IF NOT EXISTS`；
- `:185` `_applied_versions` = 字面量 `SELECT version FROM migration_version`；
- `:229` `sql = path.read_text(encoding="utf-8")`，`path` 来自 `_discover_migrations()` 对
  `_MIGRATIONS_DIR.glob("*.sql")` 的枚举（仓库内迁移目录）；
- `:232-233` `conn.execute(sql)` + `conn.execute("INSERT … VALUES (%s, %s)", (ver, ts_utc))`（参数化）；
- `:303` `resolve_now` = 字面量 `SELECT now()`；
- env 读取只出现在 `:310` 起的 `resolve_dsn()`（键名迭代 + `os.environ.get`），产出**DSN**。

**E-3 YAML 加载器（`packages/application/protocol_authoring/service.py`）**

- `:83` `class _StrictLoader(yaml.SafeLoader)`；`:99` 只追加 `DEFAULT_MAPPING_TAG` 的重复键拒绝钩子；
  `:101-103` 注释明写「与 `yaml.safe_load` 同一安全级别，仅追加重复键拒绝；不使用 unsafe
  FullLoader/Loader」，行尾带 `# noqa: S506 - SafeLoader 子类`。
- 已执行：`tests/application/protocol_authoring/test_draft_service.py` **13 passed**，其中
  `test_yaml_python_tags_are_rejected_not_executed`（`!!python/object` 等 tag 被拒绝且**不执行**）、
  `test_duplicate_key_hook_subclasses_safe_loader`（用例标题即写明「静态扫描按 `yaml.load`
  名字告警」）、`test_duplicate_key_rejected`。

**E-4 `artifacts/` 的仓库外证据**

```bash
git ls-files artifacts/ | wc -l            # → 0
git check-ignore -v artifacts/             # → .gitignore:36:/artifacts/
git log --all --oneline -- "*本地_v12.local.yaml"   # → 空（从未提交）
```

仓库内出现的 `/artifacts/{artifact_id}`、`artifacts/eval/` 等引用分别是 **HTTP 路由**与
CLI 评测报告**输出目录**，不是对该转储目录的文件系统引用。

**E-5 `gpu_probe` 污点汇**

- 汇点 `adapters/execution/gpu_probe.py:138` = `probe_gpu()` 内
  `Path(tempfile.mkdtemp(prefix="researchos-gpu-probe-"))` —— **系统生成**的临时目录；
- env 值 `RESEARCHOS_WORKER_GPU_IMAGE`（`services/worker/__main__.py:132`）进的是 docker
  **镜像引用**，不是文件系统路径；
- 已执行：`tests/distributed/test_security_distributed.py::test_worker_child_env_holds_zero_db_credentials`
  与 `::test_secret_enumeration_surface_is_zero` **2 passed**（前者断言 ambient 的
  `RESEARCHOS_WORKER_GPU_IMAGE` 等键**不进**沙箱子进程环境）。

**E-6 随机数用途**

`examples/experiments/m12_reference_classification.py` 的 `random.Random(seed)`
（`:33`/`:42`/`:64`/`:69`/`:142`）供 `_make_vocab` / `_make_class_words` / `LinearSoftmax`
的**确定性**合成数据与固定 seed 训练（seed=7），用于基准可复现；不参与密钥、令牌、
会话或任何访问判定。

## 4. 结论

1. **产品代码面（`packages/` 的 1 条 HIGH）经代码级核对为误报**：加载器是 `SafeLoader`
   子类，且有 3 个已执行用例（含「危险 tag 不执行」）把关。
2. **其余 35 条按范围分为两类**：28 条 MEDIUM 是同一条静态污点启发式（把 env→**连接目标**
   误读为 env→**SQL 文本**），经全量检索（带反证）+ 汇点代码核对判为误报；5 条 LOW 是
   M12 参考实验的固定 seed。
3. **3 条 HIGH 之外无产品代码 HIGH**：H-2/H-3 落在未跟踪的第三方转储目录
   （`artifacts/`，`git ls-files` = 0），不在仓库内容与 CI 执行面上。
4. 依赖面：182 包参与扫描，离线 advisory 命中 1 包 1 条，**密封产物未署名**（§6-U4）⇒
   **本轮不给出「依赖无风险」的结论**。
5. **本记录不构成**「项目安全」或「无漏洞」的断言：扫描是静态的、业务逻辑与授权面
   **零覆盖**（threatModel 阶段 0 入口 / 0 主体 / 0 授权面），且未做运行时验证。

## 5. 可复现配方

```text
1) 独立密封深扫（非 hook 通道）：
   通过 MCP 工具 `security_scan_start`（project=D:\research-system, depth=deep），
   轮询 `security_scan_status` 至 status=completed，读取 result.scanId / result.seal / findingCount。
2) 产物目录：~/.mimosa/security-scans/<projectId>/<scanId>/（5 件：scan-manifest / findings /
   coverage / seal / report）。
3) 逐件摘要复核：见 §1.1 命令。
4) 剖面复现：`findingCount` 与 totals 应与 §1.2 表一致（同一工作树形态下 3/28/5）。
5) 处置依据复核：跑 §3 的 E-1 命令与 E-2/E-3/E-4/E-5 指向的文件行/用例。
```

## 6. 未覆盖范围（必须与结论同读）

- **U1 无运行时/动态验证**：`evidenceBoundary = static_only_no_runtime_execution`；无渗透、
  无并发/竞态实测、无外部网络行为观测。
- **U2 威胁建模与授权面零覆盖**：threatModel `partial`，入口 0 / 主体 0 / 授权面 0；
  findingDiscovery 的业务逻辑候选 0；validation `investigated 0` ⇒ **越权、BOLA/BFLA、
  业务逻辑类问题不在本次覆盖内**（仓库自身的对应控制由 `tests/distributed/`、
  `tests/api/test_secret_redaction.py` 等产品测试承担，见 E-5，但那是产品测试而非本次审计）。
- **U3 扫描输入含仓库外内容**：工作树内的 `scratch/`、`artifacts/`（均被 `.gitignore`
  覆盖）进入扫描输入；其中 `artifacts/钻孔官方API_v12/配置/官方API本地_v12.local.yaml`
  是**明文 token 文件**——从未提交（E-4），但仍存在于工作树 ⇒ 由操作者自行决定是否清理；
  本记录不含其内容。
- **U4 依赖 advisory 未决**：1 条命中未署名，未做联网复核（超出本机可验证范围）⇒ 保持
  未决，不得读作「无已知漏洞」。
- **U5 hook 侧扫描仍无结论**：commit hook 的 `scanner_enobufs` 现象本轮依旧（§1），
  本记录不能替代 hook 侧结论。
