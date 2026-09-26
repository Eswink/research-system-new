---
id: PLAN-20260926-192
slug: auth-surface-four-doc-same-source
title: GOAL-019 cycle 2（EC-04）：四处文档与威胁模型同源（写面已认证 / 读面未认证 / 多租户未做）+ 可按压结构判据
status: DONE
created_at: 2026-09-26
updated_at: 2026-09-26
parent_goal: GOAL-20260926-019
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260926-019 的 **EC-04**（文档与威胁模型同源）。授权沿用该 GOAL 的
    `authorization.ref`：**只保护写面**、**认证可关**、**主体归因落 canonical**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：多租户 / organization scope / RBAC / 角色权限矩阵 / M18 任何内容；
    **不给读面加认证**；**不改 `Idempotency-Key` 语义**；**不把 token 写进任何文件 / CI /
    记录 / 日志 / 遥测 / 测试输出**（本 PLAN 的文档**只登记变量名，绝不留值**）；
    **不新增依赖**；**不做** D-12 的 (a) 面。
    **本 PLAN 不放宽任何判据 / 阈值 / 放行面**，**不新增策略面 allow**，
    **不改 Canonical State 边界**，**不得宣称项目安全**。本 PLAN **不改**产品代码
    （只改文档 + 新增一条判据）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-193-auth-surface-four-doc-same-source-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-144-same-source-docs-need-a-pressable-declaration.md
---

# PLAN-20260926-192 — 四处文档与威胁模型同源 + 可按压结构判据

## 目标

把 GOAL-019 EC-04 做完：**四处文档同源**地登记「**写面已认证、读面未认证、多租户未做**」
这一实况，并**写明边界与未覆盖范围**，且**零夸大**。背景：cycle 1 已把认证面落到树上
（`c87823e`），但四处文档仍是旧口径 ⇒ **文档与实现有落差**（RECHECK-191 W-2）。

四处面（各承担同一事实的不同措辞）：

1. `docs/security/IDENTITY_AND_ACCESS.md` —— 身份与访问的**总纲**（人读）；
2. `docs/security/THREAT_MODEL.md` **第 6 节**（D-12(b) 草案）—— 授权面**实况与空白**；
3. `docs/api/CONTROL_PLANE_API.md` —— 对外**接口语义**；
4. `docs/integration/LIVE_MODEL_RUNBOOK.md` —— **怎么设 / 怎么关（含警告）/ CI 怎么保持关闭**。

## 关键设计决定

- **D-1｜同源靠「一条 canonical 声明句逐字重复」而不是靠「四处都提过」。**
  四处文档各写一条**逐字相同**的声明句（词汇表 = 判据里的常量）⇒ 「同源」成为
  **可机械判**的事实，而不是"读起来差不多"。
- **D-2｜判据必须绑到代码，不能只绑到文档。** 文档说"写面已认证"，判据就要**同时**
  用 AST 证明中间件真的按 `_MUTATING_METHODS` 分类、且该集合字面量恰为四个写方法
  ⇒ **文档不会被自身措辞喂饱**（承 `MEM-141`）。
- **D-3｜零夸大用「禁止面」而不是「要求面」表达。** 只要求"写了未覆盖范围"不够，
  还要断言**不得**出现「项目安全」「授权面已覆盖」「已完成威胁建模」这类
  **肯定式断言**。
- **D-4｜runbook 只加 `###` 子节，不动 `## N` 编号。**
  既存判据 `test_runbook_same_source.py`（五个必需小节）与
  `test_live_credential_lifecycle_same_source.py`（`§8` 的固定标签表按**二级标题**切节）
  都会被"插入新的二级标题"波及 ⇒ **新内容放 §2 下的 `###` 子节**，编号零漂移。
- **D-5｜runbook 里的环境变量名会自动受既存判据约束。**
  `test_runbook_same_source.py::test_every_env_style_token_exists_in_code` 要求反引号里的
  `RESEARCHOS_*` 形态 token **真实存在于代码**（本 PLAN 写入的两个名字都在
  `services/api/middleware.py` 里）⇒ **不新增**该判据的豁免，也不放宽它。
- **D-6｜`CONTROL_PLANE_API.md` 不得新增数字 / 上限。**
  该文件被 `tests/contracts/test_dispatch_ownership_weak_equivalence.py` 用作
  「上限值只在 port 常量里写一次」的核对面 ⇒ 认证段落**只写语义、不写数值**。
- **D-7｜`THREAT_MODEL.md` 第 6 节要区分「历史事实」与「更新后状态」。**
  §6.2 是 **GOAL-016 当时**的实况，**不删**（它记录了当时的空白），
  而是**就地标注哪些已被 GOAL-019 改变、哪些仍然成立**；§6.3 的未覆盖范围据实更新。
  §6.6 的写作纪律（不得被引用为"已做威胁建模"）**保留并收紧**为
  「只可引用为『写面已认证；**其余授权面仍未覆盖』」。

## 验收条件

- **AC-1**：四处文档**各含逐字相同**的 canonical 声明句（写面已认证 / 读面未认证 /
  多租户与 RBAC 未实现），且**各含「未覆盖范围」**节或声明。
- **AC-2**：四处文档**都不含**禁止面短语（肯定式的安全声明）。
- **AC-3**：判据**绑代码**——AST 证明认证中间件按 `_MUTATING_METHODS` 分类、
  字面量恰为 `{POST, PATCH, PUT, DELETE}`、且 token 由 `os.environ` 读取（不落盘）。
- **AC-4**：**成对可按压**——删任一处声明句 / 删「未覆盖范围」/ 插入禁止面短语 /
  把方法集合改掉 ⇒ **判红**；逐字节复原 ⇒ **绿**。
- **AC-5**：既存 runbook 同源族 + 凭据边界措辞判据**原样绿**（未被本次文档改动打破）。
- **AC-6**：`ruff` / 规模门禁（450 行 / 50 行）/ 治理 `validate.py` / `DOCS-CHECK` 绿；
  **全量 m0 = 23/23**。

## 实施清单

- [x] **WP1｜总纲**：`docs/security/IDENTITY_AND_ACCESS.md` 增「控制面写面认证（GOAL-019）」
      节 + canonical 声明句 + 「未覆盖范围」节。
- [x] **WP2｜威胁模型**：`docs/security/THREAT_MODEL.md` §6 就地标注实况更新
      （§6.2 第 2 条从「无认证」改为「**写面已认证（GOAL-019）；读面仍无认证**」），
      §6.3 未覆盖范围据实更新，§6.5 的「(a) 前置 = 先有主体模型」标注为**已具备最小形态**，
      §6.6 引用纪律收紧。
- [x] **WP3｜接口面**：`docs/api/CONTROL_PLANE_API.md` 头部补认证语义 +
      §Identity/Governance 的「无 principal 概念」旧句据实更正。
- [x] **WP4｜runbook**：§2 下新增 `###` 子节「控制面写面 token：怎么设 / 怎么关 / CI 怎么保持关闭」。
- [x] **WP5｜判据**：新增 `tests/architecture/python/test_control_plane_auth_same_source.py`
      （AC-1…AC-4），并按 AC-4 逐条按压。
- [x] **WP6｜本地验证 + 记录**：定向套件 + `ruff` + 规模门禁 + **m0 全量** + 治理 + 本 PLAN /
      RECHECK / GOAL 回写。

## 证据

（实施后逐条填写；未实跑不得记 PASS。）

### 一、四处文档改动（WP1–WP4）

| # | 文件 | 落点 | 关键内容 |
| --- | --- | --- | --- |
| 1.1 | `docs/security/IDENTITY_AND_ACCESS.md` | 新增 `## Control Plane 写面认证（GOAL-019）`（L99）+ `### 未覆盖范围（明确不覆盖什么）`（L127，**7 条**） | canonical 声明句 + 诚实边界（单一共享 token ⇒ 单一主体，**不接受**调用方自报身份） |
| 1.2 | `docs/security/THREAT_MODEL.md` | 就地标注 §6.2 第 2 条 / §6.3 第 1 条 / §6.5 前置；§6.6 引用纪律收紧；新增 `### 6.7 实况更新：Control Plane 写面认证（GOAL-019，2026-09-26）`（L264） | §6.2 历史**不删**（记录 GOAL-016 当时空白）；§6.7 写明 **BFLA 在写面从「无校验点」变成「有认证、无授权」，BOLA 完全未动** |
| 1.3 | `docs/api/CONTROL_PLANE_API.md` | 文首 canonical 声明句（L3）+ 认证段（Bearer / 变量名 / 关闭⇒警告 / 401 ProblemDetail / 主体落 canonical / `**未覆盖范围**`）；§Identity·Governance 旧句「单用户控制面无 principal 概念」据实更正 | 旧句是**事实错误**（cycle 1 已有 `Principal`）⇒ 更正而非删除，并说明「有请求主体概念，但**没有**可查询的逐调用方身份」 |
| 1.4 | `docs/integration/LIVE_MODEL_RUNBOOK.md` | §2 下新增 `### 2.1 控制面写面 token（另一条凭据面，与 LLM 凭据无关）`（L90） | 怎么设（两条形态：`export` / 单命令前缀）/ 怎么关（`unset` ⇒ 警告）/ CI 怎么保持关闭（**不设**）/ 轮换 / 未覆盖范围 |

**编号零漂移（D-4 实证）**：runbook 的 `## N` 标题集合与改动前**逐条相同**（新内容只在
`## 2` 下新增一个 `###` 子节）⇒ `test_runbook_same_source.py`（五个必需小节）与
`test_live_credential_lifecycle_same_source.py`（按**二级**标题切 §8）**均未受影响**（1.5 实跑）。

| # | 检查 | 结果 |
| --- | --- | --- |
| 1.5 | 既存措辞/同源判据 | `tests/architecture/python/` = **175 passed**（cycle 1 同数）；`test_runbook_same_source.py` 单跑 **10 passed** |
| 1.6 | 改动面 | `git diff --stat` = **5 文件 / 146 插入 / 2 删除**；**产品代码零改动**（`services/**`、`packages/**`、`apps/web/**` 均无本次改动） |
| 1.7 | 变量名同源 | 反引号里的 `RESEARCHOS_CONTROL_PLANE_TOKEN` / `RESEARCHOS_CONTROL_PLANE_PRINCIPAL_ID` 是 `services/api/middleware.py` 里两个常量的**值**（判据 3.4 实跑）；**值**未出现在任何 tracked 文件 |

### 二、判据（WP5）

新文件 `tests/architecture/python/test_control_plane_auth_same_source.py`：**437 行**（450 行上限内）、**11 passed**。

| 组 | 断言 | 形态 |
| --- | --- | --- |
| AC-1 | canonical 声明句在四份文档各**恰好一次**逐字相同 | 逐字子串计数 |
| AC-2 | 每份文档有**自己的**未覆盖锚点 + **自己的**必需措辞（逐份不同 ⇒ 不许互相顶替） | 锚点 + 有界窗口（1200 字） |
| AC-3 | 21 条肯定式安全断言**零命中**；否定语境（同句含 `不得`/`不是`/`禁止`…）为**有意豁免** | 词表 + 句级豁免 |
| AC-3b | **豁免机制自身受判**（`test_the_prohibition_allowance_is_not_a_hole`）：宣示 ⇒ 红，引述禁令 ⇒ 绿 | 4 条内联断言 |
| AC-4 | 分类**复用** `_MUTATING_METHODS`（值恰为四个写方法 + 全模块**只有这一处**方法字面集合）/ 读面靠 `NotIn` 放行 / 认证面**不引用** `_ANALYSIS_ACTIONS` / token 走 `hmac.compare_digest` 且**无** `==` / 变量名只有一个读取点 / **无新增依赖**（stdlib + 已知第三方 allow-list） | AST |
| AC-5 | `create_app` 里认证注册在 `IdempotencyMiddleware` **之后**（Starlette `reversed` ⇒ 后注册者在外层） | AST + 语句行号 |

### 三、按压（AC-4 / 可非恒真）—— 14 条逐条实跑

脚本 `scratch/goal019-ec04-press.py`（输出 `scratch/goal019-ec04-press.out`）：每条按压
**改一处 → 判红 → 逐字节还原**，且每条按压的 `old` 必须在文件里**恰好出现一次**
（防"按压打偏"，承 `MEM-20260926-142`）。基线与终态均 `exit=0 failed=无`。

| 组 | 按压 | 结果 |
| --- | --- | --- |
| AC-1 | P1 只改一处口径（`读面…未认证`→`已认证`）/ P2 删掉整句 | **各只判红 AC-1** |
| AC-2 | P3 删未覆盖块的**内容**（对象级授权那一条）/ P4 删**锚点**（整节标题） | **各只判红 AC-2** |
| AC-3 | P5 插入 `已实现 RBAC` | **只判红 AC-3**（首版连带打红 AC-2：替换时把「零夸大」删了 ⇒ 已改正为保留该词） |
| AC-3b | P6 在文档里插入**引述禁令**（`不得…说成「授权面已覆盖」`） | **不判红**（豁免按设计工作）——这是**唯一**一条"期望不红"的按压，用来证明豁免不是漏洞 |
| AC-4 | P7 认证面自建第二处方法字面集合 / P8 分类放宽（GET 进写面）/ P9 幂等例外集漏进认证面 / P10 `hmac.compare_digest`→`==` / P11 变量名第二个读取点 / P12 新增依赖（`import requests`） | **6/6 判红对应组，0 连带** |
| AC-5 | P13 警告不再写明后果 / P14 注册顺序反转 | **各只判红对应组** |
| — | 逐字节还原 | **14/14 `还原=True`**，终态 `11 passed` |

### 四、本地门（WP6）

| # | 门 | 结果 |
| --- | --- | --- |
| 4.1 | 定向套件 `tests/architecture/python tests/tooling tests/api/test_principal_auth.py` | **1377 passed**（出口 0） |
| 4.2 | `ruff check` + `ruff format --check`（m0 的 `python/product-lint` / `python/format-check`） | 全绿（1 次 `format` 自动折叠后被 m0 复核） |
| 4.3 | 规模门禁 | 新文件 **437 行** ⇒ 450 行内；**曾以 451 行判红并修**（见 6.1） |
| 4.4 | **全量 m0**（独占、仓库 `.venv`、DSN 固化、`--keep-going`） | 终态行 **`PASS: profile=m0; 23 deterministic checks`**、`M0_EXIT=0`；`PASS [` = **24**；`python/tests` = **4550 passed / 20 skipped**；`FAILED`/`ERROR` **0**（日志 `scratch/goal019-c2-m0.log`） |
| 4.5 | 判据数对照 | 4550 − 4538（cycle 1）= **+12** = 11 条新用例 + 1 条规模门禁参数化条目 |
| 4.6 | 治理 `validate.py` | **Cursor 治理验证通过**（含 ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致） |
| 4.7 | `DOCS-CHECK` | **PASS: 6 deterministic checks** |

### 五、零夸大（安全口径）

- 四处文档**都不是**安全结论：`R-M1`（Mimosa 钩子侧结论未取得）在
  `IDENTITY_AND_ACCESS.md` 的未覆盖范围第 7 条、§6.7 的未覆盖清单里**逐条在位**；
- 未覆盖范围**四处各自声明**：读面未认证 / 多租户与 RBAC 未实现 / 对象级授权（BOLA·BFLA）未做 /
  逐调用方身份未做 / 部署面未验证 / 主体无数据库级约束；
- 判据 AC-3 + AC-3b 把"零夸大"变成**可机械判**的事实（而不是承诺）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | IN_PROGRESS | 派生自 GOAL-20260926-019（cycle 2）：EC-04 四处文档同源 + 可按压判据。落 7 条设计决定（D-1…D-7），其中 D-1（canonical 声明句逐字重复）、D-2（判据绑代码）、D-4（runbook 只加 `###` 不动编号）是判据形态的关键。**尚未改任何文件**。 |
| 2026-09-26 | DONE | WP1–WP6 全部落地。四处文档按同一 canonical 声明句同源（runbook 编号零漂移）；新增 11 条 AST/文本判据（**14 条按压**：13 条按预期判红、1 条"引述禁令不判红"证明豁免不是漏洞），全部逐字节还原；定向 **1377 passed**、全量 m0 **23/23**、治理与 DOCS-CHECK 绿。**产品代码零改动**（文档 + 判据两条面）。 |

### 本轮内被门禁抓到的真红（已修，非"一次通过"）

| # | 红面 | 根因 | 处置 |
| --- | --- | --- | --- |
| 6.1 | `tests/tooling/test_python_source_size_limits.py::…[tests\architecture\python\test_control_plane_auth_same_source.py]` | 新判据 **451 行 > 450 行**硬上限（差 1 行） | 压掉 `_HTTP_METHODS` 的逐行集合写法（8 行 → 1 行）+ 合并 `_DOC_UNCOVERED` 短条目 ⇒ **437 行**；因 450 行**贴近上限**，后续再扩要重新压缩 |
| 6.2 | 判据自身 4 处（首版） | ①`frozenset({…})` 是 `Call`，`ast.literal_eval` 直接抛；②`os.environ` 的识别用属性名集合比较恒不相等；③警告文案里的变量名是 **f-string 插值**而非字面量；④`dispatch` 是 `AsyncFunctionDef` | 逐处改为：剥包装取字面节点 / 判 `Attribute.attr == "environ"` / 用 `FormattedValue` 结构判插值 / `_function` 同时接受同步与异步 |

## 影响报告

- **改动面（计划）**：四处既有文档 + 一条新判据；**产品代码零改动**。
- **Domain / API / schema**：零变化（无 DTO / 路由 / 迁移 / OpenAPI 快照变化）。
- **安全 / 凭据**：文档**只登记变量名**，**不留值**；无新增放行面。
- **兼容性 / 迁移风险**：文档措辞变更可能打到**既存措辞类判据**
  （`test_credential_boundary_wording.py` / `test_runbook_same_source.py` /
  `test_live_credential_lifecycle_same_source.py`）⇒ AC-5 专门盯这一面；
  若判红且根因是**本次措辞**与既存判据冲突 ⇒ 优先改本次措辞（撤回载体改动）。
- **上游版本影响**：无。
- **下一项任务**：EC-05（收口复检 + 残余登记）。
