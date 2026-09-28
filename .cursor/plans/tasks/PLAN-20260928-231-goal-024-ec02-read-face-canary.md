---
id: PLAN-20260928-231
slug: goal-024-ec02-read-face-canary
title: GOAL-024 cycle 3（EC-02 余下）：应用级读面内容金丝雀 —— 路由树分区白名单 + 逐路由实取零命中 + 声明载体正控制 + 两向反证与按压
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-024
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-024 的 **EC-02 余下**（cycle 2 只交付了编排层一半：读面
    `read-face-http` 登记为 `NOT_YET_OBSERVED`）。授权沿用该 GOAL 的 `authorization.ref`：
    范围严格限定为「**新增金丝雀判据与夹具**（一律落 `tests/**`）+ **修被新判据证明为真缺陷**
    （只允许收紧记录面）+ **文档同源更新**」；**不加新能力、不放宽任何判据、不改安全策略、
    不修改任何既有判据**；push-to-main-for-CI 口径（**只推 main、不 force**）；默认 runtime
    保持 **Fake**、默认 CI **离线**。
    **本 PLAN 专属边界**：读面口径 = **白名单**（只判「契约声明返回内容」的路由能否看到内容；
    其余路由必须零命中）；**不得**改 `tests/api/**`（既有装配/夹具只读，可 import 复用）；
    金丝雀一律**测试内构造的合成串**；**不得**把真实 prompt / 凭据 / token 写进夹具、记录或输出；
    读面**不加认证**（属 GOAL 明确不做）；**不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **读面清单是分区且逐条显式**：应用路由树上的 GET 叶子（含 FastAPI 新版
      `_IncludedRouter` 包装）与登记清单**逐条对齐**：未分类 / 重复 / 陈旧（双向）/ 理由为空
      四条判红，并有**上下界**（声明面 ≤ 15、零命中面 ≥ 45）防白名单膨胀。
    status: PASS
  - id: AC-2
    criterion: >-
      **零命中（非空真）**：先证明 **canonical 侧真的有金丝雀**（草稿正文 / 制品正文 /
      claim 正文三种，直接读存储对象），再对**全部零命中路由**逐条实取并扫描 ⇒ 零命中；
      实取到非空响应的零命中路由 **≥ 40**（本轮实测 51）；无法实取的路由**逐条登记**（本轮 2 条）。
    status: PASS
  - id: AC-3
    criterion: >-
      **声明载体正控制**：契约声明返回内容的路由必须**真的看得到**它声明的内容
      （草稿正文 / 制品正文 / claim 正文三族共 9 条），否则判红；取不到的声明载体逐条登记
      （本轮 1 条 `/library/{resource_id}`）。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证 + 按压**：①零命中路由出现金丝雀 ⇒ 判红并**点名路由与 kind**；
      ②声明载体看不到声明内容 ⇒ 判红；③在**真实应用**上新增一条未登记读路由 ⇒ 分区判红并点名；
      ④登记里出现路由树没有的路径 ⇒ 陈旧判红。七源注入面**逐条登记**（注入 3 / 无注入面 4）。
    status: PASS
  - id: AC-5
    criterion: >-
      新判据与新夹具自洽过门：`ruff check` / `ruff format --check` / 规模（文件 ≤ 450 行、
      函数 ≤ 50 行）/ `mypy`；既有隐私判据（`test_privacy_canary.py` /
      `test_privacy_exit_census.py`）**逐字节未改**且仍全绿；`tests/observability/` 全目录绿；
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`（**记录写入之后**）；
      治理 `validate.py` 绿；CI 台账到终态。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-232-goal-024-ec02-read-face-canary.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-162-read-face-zero-hit-needs-a-bounded-whitelist.md
---

# PLAN-20260928-231 — GOAL-024 cycle 3（EC-02 余下）：应用级读面金丝雀

**动因**：cycle 2 只跑到**编排层**：读面（`read-face-http`）在判据源码里登记为
`NOT_YET_OBSERVED`，EC-02 因此未达成。读面又是**最像会泄漏的一面**（它是应用自己把
canonical 内容端出来的地方），所以这一半必须补上，且口径只能是**白名单**：
「内容出现在**契约声明返回内容**的路由上」是业务真相，「出现在别处」才是越界。

**本轮不做**：读面认证、多租户、BOLA/BFLA（GOAL 明确不做）；也不改写既有读面契约。

## 验收条件

见 frontmatter `AC-1`…`AC-5`：分区与上下界 / 零命中非空真 / 声明载体正控制 /
两向反证与按压 / 门与记录。

## 实施清单

- [x] WP1：`tests/observability/read_face_canary_support.py` —— 应用级装配（`make_run_ready_deps`
      + 换入金丝雀 runtime + `create_app` + `TestClient`）、canonical 注入（草稿正文 / 制品 /
      claim）、路由树枚举、逐路由实取、扫描纯函数。
- [x] WP2：`tests/observability/read_face_route_registry.py` —— 68 条读路由**逐条**判定
      （声明载体 15 / 零命中 53）+ 分区自审与命中核验两条纯函数。
- [x] WP3：`tests/observability/test_privacy_read_face_canary.py` —— 10 例：分区 / canonical
      非空真 / 正控制 / 零命中 / 反证两向 / 按压两向 / 七源登记。
- [x] WP4：记录（本 PLAN / RECHECK / MEM / GOAL 回写）+ 记录面判据 + as-is m0 + push + CI 台账。

## 证据

| 观测 | 数值 / 结论 |
| --- | --- |
| 路由树里的读路由 | **68**（GET 叶子；含 `_IncludedRouter` 包装下的子路由） |
| 声明载体 / 零命中 | **15 / 53**（上界 15、下界 45 均由判据看守） |
| canonical 侧金丝雀 | `prompt` / `artifactbody` / `evidencebody` **三种都在**（直接读存储对象） |
| 零命中路由实取 | **51 / 53** 取到非空响应（其余 2 条无对象、逐条登记） |
| 声明载体正控制 | 9 条真的看得到声明内容（草稿 3 / 制品 2 / claim 与 export 2 / lineage 2） |
| 未观测的声明载体 | 6 条（模板 ×2 / 记忆 / 交付物 / 库 ×2），逐条写明理由 |

**可复用事实**：读面零命中必须配**有上界的白名单**（见 MEM-20260928-162）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档（GOAL-024 cycle 3，EC-02 余下）；读面按白名单口径。 |
| 2026-09-28 | DONE | 三条新文件交付并过四道门；10 例全绿；读面零命中在**canonical 有内容**的前提下成立；两向反证与两向按压均有牙。EC-02 的读面一半就此补齐（EC-02 记 PASS 的依据见 GOAL 迭代日志 cycle 3 行与 RECHECK-232）。 |

## 影响报告

- **Domain/API/schema**：无（只新增 `tests/**`）。
- **安全/凭据**：无新凭据；夹具复用既有 `make_endpoint_payload()` 的**合成** fixture key
  （字面量由既有测试构造，非真实密钥）；读面仍**不认证**（属 GOAL 明确不做，未改）。
- **兼容性/迁移风险**：无。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-024 **EC-03**（边界条款 + 未覆盖面登记）→ 再 EC-04（自举收口）。
