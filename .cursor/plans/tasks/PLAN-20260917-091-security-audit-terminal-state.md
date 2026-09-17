---
id: PLAN-20260917-091
slug: security-audit-terminal-state
title: 完整安全审计的可复核终态：密封扫描跑通 + 36 条 findings 逐条处置 + 未覆盖范围写明（EC-07）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 8 = EC-07（后继入口第 1 项）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-091-security-audit-terminal-state.md
memory_entries:
  - MEM-20260917-066
---

# PLAN-20260917-091 — 完整安全审计的可复核终态（GOAL-004 cycle 8 = EC-07）

## 目标

EC-07 判据容纳两种合格终态：a) 扫描完整跑通 ⇒ findings **逐条处置** + 结论文本；
b) 环境仍 `scanner_enobufs` ⇒ 根因 + 可复现配方 + 人工步骤清单。**两种终态都禁止宣称
「项目安全」**，且未覆盖范围必须写进记录。

GOAL-003/004 的每一个 commit hook 都在报 `scanner_enobufs`（hook 侧扫描拿不到完整结论），
循环内以**独立 Mimosa 密封深扫**替代——本轮该独立扫描**首次跑通**（此前 GOAL-004 各 cycle
提交时的 hook 侧仍报 enobufs，`scratch/goal4-mimosa-enobufs.md` 记录了逐 cycle 现象）：

```text
scanId      scan-2026-09-17T20-05-18.700Z-663d0976701f
seal        sha256:b2af673997a765567d519bc4aee226c861deac1a6c6ec7dc76e87f69a0610347
depth       deep        runStatus inconclusive   completeness partial
totals      high 3 / medium 28 / low 5 / info 0 / businessLogic 0 = 36
dependency  182 packages scanned；offline advisory 命中 1 包 1 条（未署名，待联网复核）
```

⇒ 本轮走**终态 a**：把 36 条 findings 逐条处置（每条：结论 / 依据 / 处置），并把
「未覆盖范围」与依赖 advisory 未决项写进结论。**判 PASS 的依据是终态文档 + 证据，
不是「扫描没报问题」。**

## 口径

- **判 PASS 的依据 = 终态文档 + 可重跑证据**，不是「扫描没报问题」；两种终态都**禁止**
  宣称「项目安全」。
- **误报判定必须落到可重跑的东西**：全量检索 + **反证**（证明检索有判别力）+ 汇点逐行核对；
  只凭"看起来没问题"不构成处置。
- 本 PLAN 不改产品代码；若逐条核对发现真实缺陷，另立修复 WP 并如实记账（本轮未发现）。

## 验收条件

- AC-01 独立密封深扫**跑通**（非 hook 通道），读到 `scanId` / `seal` / `findingCount`。
- AC-02 seal 的**三件产物摘要可复核**（逐件 sha256 与 `seal.json.artifacts` 一致）。
- AC-03 **36 条 findings 逐条处置**（每条：结论 / 依据 / 处置）落终态文档。
- AC-04 结论**可复现**（同一 projectId 连续多次深扫剖面一致）。
- AC-05 **未覆盖范围**写明（含依赖 advisory 未决项与 hook 侧 `scanner_enobufs`）。
- AC-06 记录中不出现「项目安全」式断言；无产品代码变更。
- AC-07 记录链完整（PLAN / RECHECK / MEM / ALL_PLAN / GOAL）+ 治理 validator 绿
  + 本地 m0 全绿 + CI 六 job 终态如实记录。

## 实施清单

### WP-A — 证据固化与可复核性（已完成）

- 记录 scanId / seal / 三件套 digest / coverage 五阶段计数 / findings totals。
- **seal 可复核性实测**：逐件重算 sha256 与 `seal.json.artifacts` 对照（本轮实测三件全
  `ok`）；聚合 `digest` 的合成方式属扫描器内部（不宣称可复算，如实写明）。
- **跨轮稳定性**：同一 projectId 下连续 6 次深扫（2026-09-16T12:00 → 2026-09-17T20:05）
  的 findings 剖面**逐次相同**（3/28/5）、`inconclusive` + `partial` 同口径 ⇒ 结论可复现，
  且「inconclusive」是本扫描器在本仓库的**常态**而非本轮回归（与
  `docs/audits/PA1_MIMOSA_REVIEW.md` 的 2026-09-03/09-06 两次记录同口径）。

verify：三件套 digest 重算脚本输出；跨轮剖面表（含每轮 scanId）。

### WP-B — 36 条 findings 逐条处置（已完成）

按签名分四类，每条都在终态文档里落一行（结论 / 依据 / 处置）：

1. **HIGH ×1（产品代码）** `packages/application/protocol_authoring/service.py:103`
   `yaml.load(text, Loader=_StrictLoader)`：`_StrictLoader` **继承 `yaml.SafeLoader`**
   （service.py:83），不引入 `FullLoader/Loader`；已有时序性证据 = **已执行测试**
   `test_yaml_python_tags_are_rejected_not_executed`（python/object tag 不执行）、
   `test_duplicate_key_hook_subclasses_safe_loader`（该用例标题即写明"静态扫描按
   `yaml.load` 名字告警"）、`test_duplicate_key_rejected` ⇒ **登记误报**，无代码变更。
2. **HIGH ×2（仓库外）** `artifacts/钻孔官方API_v12/真实API预检_v12.py:16`、
   `artifacts/钻孔官方API_v12/src/ppocr_sidecar/客户端.py:24`：`artifacts/` 被
   `.gitignore:36` 覆盖、`git ls-files artifacts/` = **0 个文件**、`git log --all` 无该路径
   提交 ⇒ 第三方 API 转储的**未跟踪工作树副本**，不被仓库代码 import/构建/CI 执行
   （仓库内 `/artifacts/{id}` 全是 HTTP 路由字面量，非文件系统路径）⇒ **处置：仓库外范围**，
   在「未覆盖范围」里如实登记（含该目录内含明文 token 文件的未跟踪事实与 git 侧证据）。
3. **MEDIUM ×28（全部「疑似跨文件污点」）**：27 条同一签名 = env → `adapters/postgres/
   db.py:202`（`def migrate(` 行）的 `.execute`；1 条 = `services/worker/__main__.py:135`
   → `adapters/execution/gpu_probe.py:138` 的"路径穿越"。
   - 27 条依据：仓库**全量** grep 动态 SQL（`execute(f"…` / `%` / `.format(` / 拼接）
     **零命中**；`migrate()` 的 SQL 文本来自 `_MIGRATIONS_DIR` 仓库内 `*.sql` 文件
     （`path.read_text`）与字面量 DDL/SELECT，唯一带参语句是 `%s` 参数化 INSERT；
     env 值只作 **DSN（连接目标）** ⇒ 静态污点启发式把"连接目标"当成了"SQL 文本"⇒
     **登记误报**。
   - 1 条依据：污点汇 `gpu_probe.py:138` 是 `Path(tempfile.mkdtemp(prefix="researchos-gpu-probe-"))`
     ——系统生成的临时目录，不是 env 值；env 值 `RESEARCHOS_WORKER_GPU_IMAGE` 进的是
     docker 镜像引用。既有 `tests/distributed/test_security_distributed.py:78` 断言该 env
     **不进沙箱子进程环境** ⇒ **登记误报**，并把"operator env 选镜像"作为明示配置面写进文档。
4. **LOW ×5** `examples/experiments/m12_reference_classification.py`（:33/42/64/69/142）：
   `random.Random(seed)` **确定性种子**（seed=7）用于可复现参考实验，不参与任何安全决策
   ⇒ **登记误报**（沿用 `docs/audits/PA1_MIMOSA_REVIEW.md` 同口径处置）；且**无代码变更**
   （改 `secrets` 会破坏 M12 参考实验的字节级可复现契约）。

verify：**已执行**证据测试（非 prose）：`tests/application/protocol_authoring/test_draft_service.py`
（yaml 安全面）、`tests/distributed/test_security_distributed.py`（凭据隔离/env 泄漏面）。
反证：把 yaml loader 换成不安全 loader ⇒ 对应用例必须变红（不落库，仅记录方法）；
全量动态 SQL grep 与 `git ls-files artifacts/` 为**可重跑命令**（写进文档）。

### WP-C — 终态文档、记录与门禁（已完成）

- 新增 `docs/audits/MIMOSA_DEEP_SCAN_20260917.md`：证据 → 处置表 → 结论段 → **未覆盖范围**
  （静态-only：无运行时/动态验证、threatModel 阶段 0 入口/0 主体/0 授权面、业务逻辑候选 0、
  validation investigated 0、依赖 advisory 未署名待联网复核、`artifacts/` 与 `scratch/`
  非仓库内容也被扫描输入覆盖）。**结论文本不得出现"项目安全"式断言。**
- `docs/INDEX.md` 登记该文档；写 `RECHECK-20260917-091`、`MEM-20260917-066`、PLAN DONE、
  `ALL_PLAN` 行、GOAL-004（EC-07 PASS + 迭代日志第 8 行 + 状态历史 + 续点 = cycle 9 收口复检）。

verify：治理 validator 绿；`make validate-all` 全量 23 项（本机 m0）+ 受影响定向套件；
web 门（lint/typecheck/unit/stub e2e/live e2e）；CI 六 job 终态如实记录。

## 证据

- **扫描产物**：`~/.mimosa/security-scans/project-c96f90c714f9f3dc0bd2d97f/scan-2026-09-17T20-05-18.700Z-663d0976701f/`
  五件（manifest / findings / coverage / seal / report）；三件摘要逐件重算与
  `seal.json.artifacts` **全 ok**；同 projectId 连续 6 次深扫剖面逐次相同（3 / 28 / 5）。
- **已执行测试**：`tests/application/protocol_authoring/test_draft_service.py` **13 passed**
  （含「危险 tag 被拒绝且不执行」「重复键钩子必须继承 `SafeLoader`」）；
  `tests/distributed/test_security_distributed.py::test_worker_child_env_holds_zero_db_credentials`
  与 `::test_secret_enumeration_surface_is_zero` **2 passed**。
- **反证**：动态 SQL 形态检索对四种蓄意形态（f-string / `+` / `%` / `.format`）**命中**、
  对参数化写法**不命中** ⇒ 产品树零命中不是模式退化；另有写路径守卫拦截记录（旁证）。
- **门禁**：治理 validator 首跑红（PLAN 缺注册章节）⇒ 补齐后复跑绿；本地 m0 **23/23**
  （全量 pytest 结果见「状态历史」）；CI 六 job 终态见「状态历史」。

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 8 = EC-07，driver=client-goal / owner=root-agent）：
  commit hook 侧仍报 `scanner_enobufs`，改用 MCP 独立密封深扫；深扫 **completed**
  （36 = high 3 / medium 28 / low 5）；`status: IN_PROGRESS`。
- 2026-09-17 收口：WP-A/WP-B/WP-C 完成；终态 **a** 成立（36 条逐条处置，全部为误报或
  仓库外，无产品代码变更）；本地 m0 首跑 22/23（红项 = `framework/validate`：本 PLAN 缺注册
  章节 ⇒ 补 `## 验收条件 / ## 实施清单 / ## 证据 / ## 状态历史 / ## 影响报告`，未改 validator）
  ⇒ 复跑 **23/23**（全量 pytest 3896 passed / 10 skipped，493.96s）；新增 `docs/audits/MIMOSA_DEEP_SCAN_20260917.md` + `docs/INDEX.md`
  登记；RECHECK-20260917-091 = PASS_WITH_WARNINGS（W-1…W-5）；`status: DONE`。

## 影响报告

- **Domain / API / schema**：无变化（本 PLAN 只新增文档与治理记录，不改产品代码）。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无凭据面变更；登记一条工作树事实——未跟踪的
  `artifacts/钻孔官方API_v12/配置/官方API本地_v12.local.yaml` 含明文 token（从未提交、
  `.gitignore:36` 覆盖），是否清理属操作者决策（记录中不含其内容）。
- **兼容性 / 迁移风险**：无（无运行时行为变化）。
- **上游版本影响**：无（未新增依赖；pin 未变）。
- **下一项任务**：GOAL-004 收口复检（cycle 9）。

## 诚实边界（事先声明）

- 本轮的「逐条处置」是**静态结论 + 可重跑命令 + 已执行的安全面测试**三者的组合，**不是**
  运行时验证；`runStatus=inconclusive` / `completeness=partial` 是记录的一部分，不是被
  掩盖的细节。
- 依赖 advisory 的 1 条命中在密封产物里**没有署名**（`dependencies.packages` 为空数组），
  本轮**不做**联网检索（超出本机可验证范围）⇒ 作为未决项写进文档，不以"未发现"收尾。
- 本 PLAN 不改任何产品代码；若逐条核对中发现**真实缺陷**，另开修复 WP 并如实记账。
