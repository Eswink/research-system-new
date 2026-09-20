---
id: RECHECK-20260920-126
plan_id: PLAN-20260920-126
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-21
completed_at: 2026-09-21
reviewer: root-agent-goal-009-closeout
baseline_ref: 337a2ae
checked_head: 337a2ae
---

# RECHECK-20260920-126 — GOAL-009 收口复检（EC-01…EC-06）

## 检查范围

**不采信五条 RECHECK 的结论文本**：用**独立复检脚本** `scratch/verify_goal009_closeout.py`
在**当前树**与**干净 checkout** 上各跑一遍，再核对门禁与残余登记。
收口另要求：「终止与收口 · 收口结论」+ `status: ACHIEVED` + `latest_recheck` 指向本文件 +
残余登记 + CI 台账尾巴。

## 检查结果

### 独立复检脚本（四层，封印前两棵树比对）

脚本**只读**且**不 import 仓库代码**（只用标准库），所以干净 checkout 里可用主树解释器跑。
四层：A 交付物（7 文件 + 承重符号）/ B 判据用例（8 个代表用例按名）/ C 登记面 /
D 凭据面（被跟踪文件命中数 + 磁盘副本是否都在已登记集合内）。

| 树 | A | B | C | D | 合计 | 失败 |
| --- | --- | --- | --- | --- | --- | --- |
| 当前树（tip `337a2ae`） | 21/21 | 8/8 | 55/58 | 3/3（**被跟踪文件命中 = 0**） | **90** | **3** |
| 干净 checkout（`git clone --no-hardlinks` → `D:\research-system-seal-20260921`，`git status` 干净） | 21/21 | 8/8 | 55/58 | 1/1（无 `.env` ⇒ 如实跳过） | **88** | **3** |

**两棵树同结论**：失败的**同一组**——`EC-06` 当时**仍未标 PASS**（本 cycle 才收）、
`latest_recheck` 是**裸 ID** 且**过期**（`RECHECK-20260920-123`）。
干净 checkout **不引入新绿、不引入新红**；差异只在 D 层，且那里如实报「无法比对」而非「通过」。

⇒ 这两处**都是真问题**，已在本收口修掉（EC-06 → PASS；`latest_recheck` → 本文件路径）。
同一次比对还抓出第三处：`child_plans` **漂了**（只列到 123，缺 124/125），也已补齐。

### 收口提交的封印复跑（两棵树同结论，最终态）

封印对象 = **收口提交 `778db35`**（EC-06 转 PASS、`status: ACHIEVED`、`latest_recheck` 指向本文件
的那一次提交）。方式：`git clone --no-hardlinks` 到仓库外 `D:esearch-system-seal-20260921`，
checkout `778db35`，克隆树 `git status` **干净**。

| 项 | 当前树 | 干净 checkout（`778db35`） |
| --- | --- | --- |
| 独立复检脚本 | **91 checks / 0 失败 ⇒ PASS** | **89 checks / 0 失败 ⇒ PASS** |
| 合并判据套件（12 文件） | **116 passed / 2 skipped** | **116 passed / 2 skipped** |
| 差异 | —— | 少 2 个 check：干净树**没有 `.env`**，D 层的值比对如实**跳过**（**不**读成「通过」） |

⇒ **两棵树同结论**：干净 checkout **不引入新绿、也不引入新红**。
封印前那次比对（tip `337a2ae`）抓出的三处真问题，修正后在此**不再出现**。

`checked_head` 说明：本文件 frontmatter 的 `checked_head: 337a2ae` 是**封印前比对**的 tip
（问题就是在那次比对里发现的）；最终态封印对象是 `778db35`，两处结论一致（0 失败）。

**残余的物理位置提醒**：干净 checkout 在仓库外的 `D:esearch-system-seal-20260921`，
是**一次性**封印产物（不在 git 里，也不在仓库工作树里）。

### 残余登记

**GOAL-008 的六项人工面原样保留**（逐条在 GOAL「不进入循环 / 需人工拍板」里，本 GOAL 未动）：

1. **ADR-0031**（`tool_pack.*` 能力策略）仍 `Status: Proposed`——归用户拍板；
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——需用户或 ADR 拍板；
3. **`artifacts/` 明文 token 清理**——涉及不可变历史资产，需人工确认；
4. **450 行纪律的贴线文件**——大重构会放大 diff 风险；
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等）——上游 pin 变更需拍板；
6. **hook 侧 L3 门**——治理面，需人工决定。

**外加**：**把真实 runtime 设为默认**、**为 anthropic 形态引入新依赖**、**把凭据写进 CI**、
**`ModelCompatibilityProfile` 建为一等域实体**——同列在「不进入循环」里，本循环未做。

**本 GOAL 新产生的残余（W 列表，逐条见各 RECHECK）**：

- `RECHECK-121` **W-1…W-7**：终态是 `FAILED` 非 `SUCCEEDED`（设计内）；逐条失败消息未捕获；
  litellm 无该模型价格映射；单次「一致」样本的证明力；缺 `system_fingerprint`；
  anthropic 面归 EC-02；**W-7 = 全量 m0 期间一次真实出站**（本地门「离线」不是结构保证）。
- `RECHECK-122` **W-1…W-6**：run 腿仍走 `OPENAI_COMPATIBLE`；(a) 从未实跑；
  「会打到 OpenAI 形态 mock」是**强推断**；判据**有意过严**；判据不覆盖执行正确性；
  前端列无判据把守；cycle 1 的 CI 红（已修）。
- `RECHECK-123` **W-1…W-6**：单次样本 ≠ 永不漂移；反证**发现不了自洽的假样本**；
  判据与标签行**耦合**；「未持久化」只有文档口径；前端 drift 渲染不在射程；CI 台账规则。
- `RECHECK-124` **W-1…W-7**：端点拒绝那一格是**指向**既有判据而非本 GOAL 重测；
  「模型不存在」只有**装配层**判据、无 provider 侧实跑样本；失败消息**未按内容**断言；
  预置条件开关是新环境变量；「门开 ≠ 凭据有效」是设计内语义；CI 台账；**出站 2 次**的如实登记。
- `RECHECK-125` **W-1…W-6**：构造语义被判据当**契约**钉住（改它须三处同步）；
  「按引用」只成立于测试/注入路径；大小写只钉住「拷贝后敏感」这一半；
  本 cycle **未读/未打印/未写入任何真实凭据值**（代价：不覆盖真实 `.env` 注入链路）；
  额度声明只判在场；CI 台账。
- **本次收口新增**：磁盘上除 `.env` 外还有一份凭据副本 **`secrets/llm_key.txt`**
  （**gitignored、untracked**，时间戳早于本 GOAL）。**这不是 tracked 泄露**
  （被跟踪文件命中数 = **0**），但它是**未经登记的第二份明文副本**，已登记为残余交人工决定；
  **本循环不删除它**（不是本循环该动的资产）。

### 门禁

- 全量 m0（**CI 同形配置**：`LLM_MAIN_KEY=""` + 测试 DSN pin）⇒ 见下方 m0 小节。
- 治理 `validate.py` ⇒ 绿。

#### m0 结果

命令（**CI 同形配置**：挡住本机凭据 + pin 测试 DSN）：

```text
LLM_MAIN_KEY="" RESEARCHOS_POSTGRES_DSN=<测试 DSN> RESEARCHOS_DATABASE_URL="" DATABASE_URL="" POSTGRES_DSN=""   uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py   --profile m0 --keep-going
```

**两轮，都如实登记**：

| 轮 | 结果 | 红项 |
| --- | --- | --- |
| 第 1 轮 | **`FAILED: 1 check(s): framework/validate=1`**（`python/tests` = **4260 passed / 13 skipped**，无红） | 治理 validator 报两处**记录**缺陷：①DONE 任务（PLAN-126）正文含占位词；②通过态复检（本文件）正文含同一占位词——都是我**在正文里引用状态值时用了那个哨兵词**。处置是**改写措辞**（改成「当时仍未标 PASS」），**不是**放宽 validator |
| 第 2 轮 | **`PASS: profile=m0; 23 deterministic checks`**（`4260 passed, 13 skipped`，`601.05s`，`FAIL` 计数 **0**） | —— |

⇒ 两轮之间**没有**改任何代码或断言：只改了**记录措辞**。这属于「修记录而非调门禁」的既有口径
（同 `MEM-20260920-096`）。

## Warnings（不阻断，如实登记）

- **W-1 本文件的 C 层在封印时仍是「3 失败→已修」的形态**：两棵树跑的是**收口前**的 tip
  （`337a2ae`），失败项是 `EC-06` 与 `latest_recheck`——它们**在收口的同一次提交里被修掉**，
  因此封闭复跑（在收口提交上再克隆一次）的结论记在本文件的追加小节与 GOAL 的 CI 台账里。
  这不是「先修后补证据」，而是**先测出问题、再修、再复验**的顺序。
- **W-2 干净 checkout 没有 `.env`**，所以 D 层的**值比对**在那边不执行（如实报「无法比对」）。
  可跨树比对的是 A/B/C 三层与文件内容；D 层的「被跟踪文件 0 命中」只在当前树可判。
- **W-3 `secrets/llm_key.txt` 是**未登记**的第二份副本**（见残余）。本循环的判断是
  **登记而非删除**：它 gitignored、untracked、早于本 GOAL 存在，删除它属于「动不可变/他人资产」，
  超出本循环授权。**风险如实**：多一份明文副本 = 多一个泄露面（该 key 为可弃用额度，
  但纪律不因此放松）。
- **W-4 复检脚本本身不是判据**：它核对「该在的东西在不在、登记面一致不一致」，
  **不**重跑每条 EC 的行为判据（那些由各自的 pytest 套件承担，且已在各 RECHECK 里实跑过）。
  脚本**不 import 仓库代码**是刻意的：这样它不会因为被测代码的 bug 而「同谋通过」。
- **W-5 `child_plans` 曾漂**（只列到 123）——由本次复检抓出并补齐。
  这类「登记面漂移」不会让任何 pytest 变红，只能靠复检脚本抓 ⇒ 这正是 EC-06 的价值。
- **W-6 CI 台账**：见下方小节；**未跑到终态的不记**。

## 结论

**result: PASS_WITH_WARNINGS**。GOAL-009 的六条 EC **全部 PASS 且有实跑证据**：
EC-01 首次真实 live run（终态 `FAILED` = 设计内 acceptance-gate 判拒，口径 `REPEATABLE_CONFIGURATION`）/
EC-02 anthropic 面取 (b) 并写成**可判**边界 / EC-03 漂移样本成为**可重算**事实 /
EC-04 失败路径**有实跑反证**（`401` ⇒ `FAILED`，零计费、无泄露）/ EC-05 凭据生命周期
按**实测的构造语义**写死并钉住；EC-06 本次独立复检**两棵树同结论** + 门禁 + 残余登记。
**收口结论：ACHIEVED。** PLAN-20260920-126 可置 **DONE**。

**Warning 不阻断的理由**：W-1…W-6 都是**如实说明证据的射程与顺序**（哪些在两棵树可比、
哪些只在当前树可判、哪些是登记而非修复），**不是**被掩盖的失败；W-3 是一条**已登记的残余**
（不是本循环该处置的资产）。**全程未改任何门禁或断言强度；未新增依赖；未改 pin；未改 Policy；
未把凭据写进 CI；未把真实 runtime 设为默认。**
