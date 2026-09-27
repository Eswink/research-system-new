---
id: RECHECK-20260927-208
slug: frontend-token-is-not-access-control-recheck
title: GOAL-021 cycle 4（EC-04）独立复检：判定点只在后端 + 仅内存结构 + 两处文档同源 + 反证 1/1 红
plan_id: PLAN-20260927-207
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-27
completed_at: 2026-09-27
owners:
  - root-agent
---

# RECHECK-20260927-208 — 前端 token 面不是访问控制（GOAL-021 EC-04）

## 检查结果

**复检口径**：不复用 PLAN / GOAL 的结论叙述；每一项给出**可复核观察面**
（命令、文件、sha256、实测输出）。**未实跑的不记通过**。

### 一、判定点只在后端（EC-04(b)）

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | **不经过任何前端**：认证开启，`POST /projects` **不带** token | **401** |
| 1.2 | **同一个请求**带上正确 token | **201**（通过） |
| 1.3 | 两条的差别 | **只在请求头** —— 两者都不经过前端 ⇒ 判定点**只在后端** |
| 1.4 | **结构**：认证中间件源码里是否出现前端概念 | `localStorage` / `sessionStorage` / `apps/web` / `window.` / `document.` **全部不出现**；且确有 `RESEARCHOS_CONTROL_PLANE_TOKEN`（证明读到了源码，不是空文件通过） |
| 1.5 | 被拒的写请求是否改动 canonical | **没有**（项目数不变、被拒的 id 不存在）⇒ 「前端能输入 token」不等于有写能力 |

### 二、仅内存 / 单一持有者（EC-04(a)）

| # | 观察 | 结果 |
| --- | --- | --- |
| 2.1 | token 模块**代码**是否触碰持久化面 | 剥注释后 `localStorage` / `sessionStorage` / `indexedDB` / `document.cookie` / `window.name` **零命中** |
| 2.2 | **反向对照**（判据确实读到可执行代码） | 源码含「浏览器存储」（注释里的决策说明）；剥注释后**不含**；且 `subscribeControlPlaneToken` 在代码里 |
| 2.3 | **单一持有者**：`apps/web/src` 里除该模块外是否有别处保存 token 值 | **无**（`let <...>token...: string` 形态零命中） |
| 2.4 | 与既有前端判据的分工 | `apps/web/tests/unit/control-plane-token.test.ts` 判**前端携带行为**与持久化零命中（含剥注释 + 两条反向对照）——**本 PLAN 未改该文件**；本 EC 的增量是**后端侧**独立判据 |

### 三、两处文档同源（EC-04 AC-4）

| # | 观察 | 结果 |
| --- | --- | --- |
| 3.1 | `docs/security/IDENTITY_AND_ACCESS.md` | 「未覆盖范围」新增**第 8 条**：**前端 token 输入面是便利面，不是访问控制**，含三条可复核事实（判定点只在后端 / 不持持久副本 / 前端不是判定点） |
| 3.2 | `docs/security/THREAT_MODEL.md` | §6.3 第 3 条（**不覆盖前端**）追加**实况更新**，与 3.1 同一口径 |
| 3.3 | 既有同源判据是否仍绿 | `test_control_plane_auth_same_source.py` + `test_reproducibility_wording.py` + `test_security_scan.py` ⇒ **22 passed** |
| 3.4 | 是否触发肯定式安全断言词表（`_FORBIDDEN_PHRASES`） | **未触发**（措辞全程带否定 / 「不是」限定） |
| 3.5 | 同源声明句与各文档未覆盖锚点 | **仍恰好一次**（AC-1 / AC-2 通过） |
| 3.6 | **该文件零改动** | `git diff --quiet tests/architecture/python/test_control_plane_auth_same_source.py` ⇒ **UNCHANGED** |

### 四、反证（先红后绿，逐字节复原）

**复检动作**：给 token 模块**临时接上**一个浏览器持久层写入
（`setControlPlaneToken` 里加 `window.localStorage.setItem(...)`），跑判据，再复原。

| # | 观察 | 结果 |
| --- | --- | --- |
| 4.1 | **既有**前端门 `tests/api/test_security_scan.py` | **1 failed**（`test_frontend_never_writes_secret_to_persistent_storage`）⇒ 该字面量断言**对新增写入有效** |
| 4.2 | **首版**本 EC 判据 | **6 passed（未红）** ⇒ 首版判据只断言**导出函数名**，**不绑定行为** ⇒ **不可证伪**。**按纪律记为「按压打偏」并修正** |
| 4.3 | **修正后**的本 EC 判据 | **1 failed**（`test_the_module_does_not_reference_browser_storage_apis`）⇒ 判据**改成剥注释后扫代码**（与前端判据同纪律） |
| 4.4 | 复原后 `sha256sum apps/web/src/api/controlPlaneToken.ts` | `32d7c4fc5e76b8d72c4a4b18e6713227b90564ab7b2b036ffbc40910595a6f44`（与按压前**逐字相同**） |
| 4.5 | `git diff --quiet apps/web/src/api/controlPlaneToken.ts` | **IDENTICAL TO HEAD** |
| 4.6 | 复原后复跑（本 EC 判据 + 既有安全扫描） | **12 passed** |

### 五、既有判据零改动与规模

| # | 观察 | 结果 |
| --- | --- | --- |
| 5.1 | `tests/api/test_security_scan.py`（`git diff --quiet`） | **UNCHANGED** |
| 5.2 | `apps/web/tests/unit/control-plane-token.test.ts` | **UNCHANGED** |
| 5.3 | `tests/architecture/python/test_control_plane_auth_same_source.py` | **UNCHANGED** |
| 5.4 | 新判据规模 | **163 行**（≤ 450）；单函数 ≤ 50 行；`ruff check` + `ruff format --check` + `mypy` 全过 |
| 5.5 | web 门 | `lint` **通过**（`eslint src --max-warnings 0` 无输出）；`typecheck` **通过**；unit **94 passed / 0 failed** |
| 5.6 | 凭据纪律 | token 为**合成假值**，不从环境读取、不落盘、不进日志 |

### 六、本轮是否证明产品缺陷

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | 后端判定是否依赖前端状态 | **不依赖**（1.1–1.4） |
| 6.2 | 前端是否持有持久副本 | **不持有**（2.1–2.3） |
| 6.3 | ⇒ 产品代码改动 | **零**（`controlPlaneToken.ts` 按压后 `git diff` 为空） |
| 6.4 | 自检结论 | **边界成立**（前端是便利面，不是访问控制） |
| 6.5 | 本轮修掉的缺陷 = **判据自身 1 处（断言不绑定行为）** | 首版断言导出函数名 ⇒ 按压不红；改为剥注释后扫代码。**如实登记**，**不**算产品缺陷 |

## 结论

**`PASS_WITH_WARNINGS`**。GOAL-021 **EC-04** 两条**全部成立且有实跑证据**：
**判定点只在后端**（绕过前端直调 API：无 token 401 / 有 token 201，且中间件源码不含前端概念、
被拒请求不改动 canonical）；**仅内存且单一持有**（代码零持久化命中 + 无别处副本）。
两处安全文档**同源登记**「便利面不是访问控制」，既有同源判据**仍绿且零改动**。
反证 **1/1 红**（修正判据后）、逐字节复原、web 门通过、**零产品缺陷**。

**警告（如实登记，不构成 PASS 的例外）**：

- **`W-1`（最要紧）**：本 EC 的**结构判据**（token 模块零持久化）与
  `apps/web/tests/unit/control-plane-token.test.ts` 的同类断言**方向一致、互为冗余**。
  **冗余是刻意的**（理由：EC-04 要在**后端套件**里独立发现「前端开始持久化」这一回归，
  不必依赖 web 门是否被跑到），但**代价**是：改持久化纪律时要**同时**顾及两处判据。
  ⇒ 记录在案，避免将来误认为其中一处是死代码。
- **`W-2`**：**「前端不是判定点」是结构判据（扫源码无授权逻辑）**，不是形式化证明。
  它**不能**排除「有人把授权判断藏进别的模块」——那属于代码审查面，不是本判据能穷尽的。
- **`W-3`**：XSS 面**未测**。内存态同样可被同源脚本读取（任何浏览器方案都如此），
  本 EC 只证明**不落持久层**（刷新即失），**不**证明抗 XSS。
- **`W-4`**：本 EC 的**行为判据**是**本机**实跑（`TestClient` + 合成 token）；
  CI 的 `console-frontend` 跑的是既有 stub / live 套件（**关闭态**）⇒
  **开启态**的浏览器侧证据未进 CI 判据（承 GOAL-020 EC-01 的既有登记）。
- **`W-5`**：前端 token 面的**可用性代价**（刷新即失）是**选定的代价**，
  不是缺陷；但它意味着**长期运行**的操作者会反复粘贴 —— 这是**已知**的取舍（`MEM-20260926-147`）。

### 七、全量门（记录写完之后）

| # | 观察 | 结果 |
| --- | --- | --- |
| 7.1 | `run_all_checks.py --profile m0 --keep-going` | 终态行 **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4613 passed / 21 skipped**、零 `FAILED`/`ERROR`；日志 `scratch/goal021-c4-m0.log`） |
| 7.2 | m0 条数 | 仍为 **23** ⇒ 新判据**未**新增 check |
| 7.3 | web 门（本 EC 的受影响面） | `lint`（`eslint src --max-warnings 0`）**通过**；`typecheck`（`tsc --noEmit`）**通过**；unit **94 passed / 0 failed** |
| 7.4 | 顺序 | 记录（PLAN / RECHECK / GOAL）写入**先**，全量门运行**后**（承 MEM-145） |

**未覆盖范围（承 GOAL-021 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
**本 RECHECK 证明的是「前端不构成访问控制」，不能证明「项目已安全」。**
