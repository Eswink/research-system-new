---
id: RECHECK-20260929-238
slug: goal-025-ec01-response-header-face-in-scan
title: GOAL-025 EC-01 复检：读面响应头进扫描面（头清单分区 + 零命中 + 非空取证 + 正控制 + 两向反证 + 按压复原）
plan_id: PLAN-20260929-237
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-238 — GOAL-025 EC-01 复检

**复检口径**：不采信判据自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / raw `sha256`）。
**未实跑的不记通过**；警告逐条留位。

## 检查结果

### 1. 头清单是分区且写在判据源码里（AC-1）
- `tests/observability/read_face_header_inventory.py`：**217 行**，`ruff format --check` =
  `2 files already formatted`、`ruff check` = `All checks passed!`、`mypy` = `Success`。
- `HEADER_RULES` 六条：**受判 2**（`content-disposition` / `etag`）、**豁免 3**
  （`content-type` / `content-length` / `x-content-type-options`）、**登记为不发射 1**
  （`last-modified`）。分区自审五条 + 受判面下界（`MIN_JUDGED = 2`）都在源码里。
- 三条按压（改 `HEADER_RULES` 源码）**全部先红后绿**、逐字节复原（见第 3 节）：
  - P1 删 `content-disposition` 规则 ⇒
    `['未分类的响应头:content-disposition', '受判面低于下界:1 < 2']`；
  - P2 把 `etag` 的理由抽空 ⇒ `['理由为空:etag']`；
  - P3 `last-modified` 由 `ABSENT` 改判 `EXEMPT` ⇒
    `['豁免头缺少机械值形态:last-modified', '登记陈旧(本轮未观测到):last-modified']`。

### 2. 零命中 + 非空取证（AC-2）
- 逐路由实取**响应头**（不筛状态码）：**65 条**读路由取到响应 ≥ 下界 40。
- 头部观测计数（实跑）：`content-type` **65** / `content-length` **65** / `etag` **4** /
  `content-disposition` **1** / `x-content-type-options` **1** / `last-modified` **0**
  ⇒ 受判头**逐条非空**（`judged_observation_findings` 全绿）。
- **金丝雀零命中**：`test_no_canary_in_any_response_header` 对全部 65 条路由的全部头逐值扫描
  ⇒ 零违规。豁免头的机械值形态（十进制计数 / `nosniff` / 媒体类型字符集）全部成立。

### 3. 正控制 + 两向反证 + 按压与逐字节复原（AC-3）
- **正控制（头是活的且是标识符回显面）**：`/artifacts/{artifact_id}/content` 的
  `Content-Disposition` 实测 = `inline; filename="canary-artifact_<run>"`（`filename` **逐字符等于**
  净化后的 `artifact.id`）；`ETag` **逐字符等于** `f'"{meta.digest}"'` ⇒ 受判头确实在发，
  且回显的是**标识符**（不是内容）。
- **两向反证**：
  - 该红时红（判据内，真实应用 + 真实响应）：受判头带金丝雀（按压路由回 `ETag` 含
    `ARTIFACT_BODY`）⇒ 判红并点名**路由 + `etag` + `artifactbody`**；未分类新头
    （`x-echo-prompt`）⇒ 判红点名；登记为不发射的头出现（`Last-Modified`）⇒ 判红点名；
  - 不该红时不红：内容放进 **canonical / 声明载体的正文**（本轮正文确有 `prompt` 与
    `artifactbody` 两种金丝雀）⇒ **头面仍零命中**。
- **按压 → 逐字节复原（承 MEM-152）**：三处源码按压均以 Edit 施加 / 复原，`sha256` 用**二进制读**
  计算、证据用**二进制写**盘；复原后 raw `sha256` 回到
  `9e9a51ea65603f03cc76d4ea050bdd5555d917138ed9cca41d2bbd37c4e0babd`（`MATCHES_BASELINE True`），
  判据复绿（**13 passed**）。证据：`scratch/goal025-ec01-press-matrix.log`。
- **边界钉住**：`test_identifier_boundary_is_not_carried_by_the_fixture` 断言夹具的**全部标识符**
  （两个制品 id + `face.ids` 全部取值）都不含金丝雀 token ⇒ 将来若有人把内容塞进标识符，
  先在这里判红，而不是让头面判据悄悄变成「标识符不许出现」。

### 4. 终态（AC-4）
- 四道门（两个新文件）：`ruff format --check` / `ruff check` = `All checks passed!`、
  `mypy` = `Success`、规模 **217 / 245 行**（≤450）；
  规模门判据定向跑 = **2 passed**。
- 既有隐私判据**逐字节未改**（`git diff --stat -- tests/observability/` 在改前为空）；
  `tests/observability/` 全目录 **113 passed, 1 skipped**（GOAL-024 cycle 4 收口时为
  100 passed + 1 skipped ⇒ 本轮 **+13** = 新判据 13 例）。
- `m0` / 治理 / CI 台账：见 PLAN-20260929-237 的「证据」与 GOAL 迭代日志（**记录写入之后**才跑）。

## 结论

**PASS_WITH_WARNINGS**。EC-01 的四条验收（头清单分区 / 零命中 + 非空取证 / 正控制 + 两向反证 +
按压复原 / 终态）**全部有实跑证据**；残余 `G24-2`（「读面扫描只扫响应体、响应头不在面」）
在本轮**收口**（`m0` 与 CI 台账由 GOAL 记录面承载）。

**警告（如实留位，不消解）**：

- `W-1`：受判面是**有界的**——受判头目前只有 2 条，且**头名清单是人工登记**的：
  「运行期观测到的未分类头 ⇒ 判红」能挡住**新头**，但挡不住「**已登记为受判的头**被人工改判成
  豁免」（改判会在 `登记陈旧` / `豁免头缺少机械值形态` 两条上被挡，但最终仍是人工决定）。
- `W-2`：`EXEMPT` 的机械值形态是**形态**断言（字符集 / 常量 / 十进制），**不是**「该头永不承载
  内容」的证明；形态允许的字符集内仍可能塞入短串（本轮以「任何头值零命中金丝雀」的绝对扫描兜底）。
- `W-3`：`Content-Disposition.filename` 取值来自 **`artifact.id`**（字符类净化 + 尾 120 截断）。
  本轮只判定「**内容**金丝雀不回头」；`artifact.id` 的**来源面**（运行时是否允许它承载用户文本）
  **未判定** ⇒ 已登记为 GOAL-025 的残余（见 GOAL 的迭代日志与 EC-02/EC-04 的登记面）。
- `W-4`：按压是**源码级**（改判据自身的清单）与**判据内**（真实应用按压路由）两形态；
  **未**在**产品侧**（`_content_headers()` 的实现）施加按压 —— 若产品侧的取值来源改变，
  本判据会在**正控制**（`filename` 逐字符等于净化后的 id、`ETag` 等于 digest）上判红，
  但那是**断言**层面的发现，不是产品侧按压。
- `W-5`：本轮只覆盖**读面**（GET）。**写面**响应头（`POST` / `PATCH` / `PUT` 的响应）**不在射程**。
- `W-6`：`etag` 的两个来源（制品 digest / 草稿 revision）中，**草稿三条路由**的 `ETag` 只在
  正控制之外的**零命中扫描**里被覆盖（未逐条断言其取值来源）⇒ 该取值面**未逐条取证**。
- `R-M1` 未收口：**不得**据此宣称项目安全；本复检只覆盖被点名判据在本机默认离线链上跑到的那几面。
