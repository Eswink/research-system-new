---
id: MEM-20260925-140
title: "门禁输入面收窄要三件事：由外部权威决定 + 判据成对 + 不可用时当场点名硬失败"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-180-gate-input-face-is-git-decided.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-181-gate-input-face-is-git-decided.md
supersedes: []
tags: [gate, scoping, git, validate-bundle, goal-017, d-10]
---

## 做了什么

把 `framework/validate_bundle` 的 **Markdown 本地链接扫描**的输入面从「工作区里所有 `.md`」
收窄为 **git 决定**的「已跟踪 ∪ 未跟踪且未被忽略」（`git ls-files -z --cached --others
--exclude-standard` 的并集），于是**别人**的 gitignored 在制品（`scratch/`）不再能让本机门判红
（`R-3` 消失：as-is 本机 m0 从 22/23 变成 **23/23**）。被判内容（链接存在性）与其余检查项
**一字未动**。

## 为什么这样做

- **门禁的输入面必须是「本仓的产物」，不是「此刻磁盘上恰好有什么」**：`R-3` 的成因就是
  门禁扫到了仓库外写者的未跟踪文件。收窄输入面 ≠ 放宽判据：被扫物的**判法**没变，
  变的是**谁算输入**。
- **由外部权威决定，而不是再维护一份名单**：往 `NON_SOURCE_DIRS` 里加目录名只治一个名字，
  下一个在制品目录还会复发。git 自己已经持有「哪些路径属于这个仓」这件事
  （`.gitignore` + 索引），所以判定直接用 git。
- **`-z` 不是可选项**：默认 `core.quotepath` 会把非 ASCII 路径转义成八进制形式，
  与 `Path` 算出的相对路径对不上。本仓有 30 条非 ASCII 已跟踪路径（见 `ADR-0032`）
  ⇒ 不用 NUL 分隔输出，那 30 条会**静默**从输入面里消失（这正是「看似收窄、实则漏扫」）。
- **「已跟踪优先于忽略」是安全边界**：取并集而不是取差集 ⇒ 即使文件落在被忽略的目录里，
  只要它已跟踪就照旧被扫。判据必须**成对**（gitignored 的坏文件不判红 / **同内容但已跟踪**
  的坏文件仍判红），否则「收窄」与「漏扫」在测试上无法区分。
- **「该扫却扫不成」必须在**任何**后续检查之前可见地失败**：把不可用攒进 `ERRORS` 是错的——
  `ERRORS` 只在 `main()` 走到最后才打印，而根不可用时**别的检查会先崩**
  （实测：`check_index_links()` 在缺 `docs/INDEX.md` 的根上抛 `FileNotFoundError`），
  点名的那条就被埋掉了。改成**当场 print + `SystemExit(1)`**。
- **范围围栏要刻意**：同一份 `repository_files()` 还被版本号两段检查消费；授权只覆盖
  Markdown 链接扫描 ⇒ 那两段保持全工作区（这是**选择**，要写进记录，否则下轮会被误读成遗漏）。

## 怎么做与复现

- **实现**：`git_decided_inputs() -> frozenset[str] | None`（`None` = git 面不可用）；
  链接扫描里加一条 `if doc.relative_to(ROOT).as_posix() not in inputs: continue`；
  不可用时 `print("验证失败:") + print("… not_a_git_tree …") + raise SystemExit(1)`。
- **成对判据（hermetic 夹具树，不碰主树索引）**：
  `tests/tooling/test_validate_bundle_git_decided_input_face.py` —— `git init` 一个临时工作树，
  写四种身份的同内容坏链接文件（已跟踪 / 被忽略 / 被忽略里 force-add / 未跟踪未忽略），
  用 `CURSOR_FRAMEWORK_ROOT` 指向它，**只驱动被改的那个函数**并断言判词里谁出现、谁缺席。
  夹具自身的**前提**逐条先断言（`git check-ignore` / `ls-files --cached` /
  `--others --exclude-standard`）——否则夹具一失效判据就变空转。
  被忽略目录**刻意用任意名字**（`ignored-area/`）：按目录名特判的实现会在这条判据上红。
- **反证（先红后绿，同一个坏文件）**：`git worktree add --detach <tmp> HEAD`（**该 worktree
  有自己的索引** ⇒ 主树索引零改动），在 worktree 里造坏文件；`git show HEAD:<script>` 取出
  改动前的脚本跑同一棵树 ⇒ 红；工作树脚本跑同一棵树 ⇒ 绿；再 `git add -f` 把同一文件
  变成已跟踪 ⇒ **又红**。
- **按压判据自身**：同一夹具上跑「改动前 vs 改动后」两个脚本，断言 gitignored 那条
  **从出现变缺席**、其余三条**始终在**（否则判据可能是靠「门禁直接罢工」变绿的）。

## 适用边界

- **不适用于「判据本身该不该管这件事」**：收窄输入面只解决「谁算输入」；被判内容仍按原判法。
  想放宽判法那是另一件事（本仓 `fix_policy` 明文禁止）。
- **同一文件里的其它 `repository_files()` 消费者不会自动跟着收窄**：本仓的版本号两段
  **仍扫全工作区** ⇒ 别人未跟踪文件里若出现旧版本号，**仍**能让本机门判红。
  要收窄它们属**另一次授权**。
- **依赖 git 在场**：非工作树的扫描根（导出的 tarball / 打包发布物）会**硬失败**。
  这是**有意**的（fail-closed）：那种根上无法判定输入面，静默通过比硬失败更危险。
- **`...` 形式链接在 Win32 会剥尾点**：链接 / 路径判据的跨平台结论以 CI（Linux）为权威证书。
- 判据用**唯一一个**任意目录名取证「与名字无关」——那是契约，不是数学证明。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-180-gate-input-face-is-git-decided.md`（WP1–WP3）
- `.cursor/plans/goals/GOAL-20260925-017-gate-scoping-live-switch-and-observability-job.md`（EC-01 / D-10）
- `.cursor/plans/rechecks/RECHECK-20260925-181-gate-input-face-is-git-decided.md`（7 条 AC）
- `.cursor/skills/system-spec-check/scripts/validate_bundle.py`（`git_decided_inputs` / `validate_local_markdown_links`）
- `tests/tooling/test_validate_bundle_git_decided_input_face.py`（成对判据）
- `docs/architecture/LOCAL_GATE_PROTOCOL.md` 第 2 节 (iii) 与第 3 节 `R-3` 行（本项的起点）
- `tools/credential_audit.py`（`not_a_git_tree` 的既有口径先例）
- `scratch/goal017-c1-pair-proof.txt`、`scratch/goal017-c1-criteria-press.txt`、
  `scratch/goal017-c1b-m0-as-is.log`（输出留档，不入库）
