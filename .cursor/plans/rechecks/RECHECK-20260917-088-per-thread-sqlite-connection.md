---
id: RECHECK-20260917-088
plan_id: PLAN-20260917-088
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle5
baseline_ref: 8f0b91e
checked_head: 64d668a+worktree
---

# RECHECK-20260917-088 — 每线程 SQLite 连接（GOAL-004 cycle 5 = EC-05 第①半）

## 检查范围

PLAN-20260917-088 声称的交付面：控制面**文件库**路径下，共享连接不再被跨线程使用——
每条线程懒开自己的连接（WAL + `busy_timeout`），store 代码零改动（代理面转发），
`with conn:` = 本线程事务块，`close_all()` 覆盖全部登记连接，`:memory:` 共用一条被显式
钉住（SQLite 语义，不伪装成每线程）。

**不在本 PLAN**（EC-05 第②半，见告警 W-1 与 GOAL 续点）：worker claim 与 retry dispatch
的**统一派发读面**。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 真的每线程一条（AC-01） | 池单测（文件库）：两线程 `id(pool.current())` 不同、`connection_count()` = 基线 + 2（懒创建、不多开） | PASS |
| 写可见性（AC-02） | 池单测：本线程提交后同连接立即可读；另一线程在提交后读到（WAL 语义，不靠一把大锁） | PASS |
| 并发负载干净（AC-03） | API 用例（文件库夹具）：12 线程 × 24 次 `POST /ops/schedules` ⇒ 24×201、无 5xx、无 404、24 条都从读面列得出来；`:memory:` 同负载同样干净（基线对照）；池单测另有 12 线程 × 8 次直写全部落库、无异常 | PASS |
| 兼容面（AC-04） | 夹具统一走池 ⇒ `tests/api` 全量 **420 passed**（~30 个 store 的用法全部经代理面）；`tests/adapters/sqlite tests/application tests/contracts tests/e2e tests/postgres` **1371 passed / 4 skipped**；mypy **911 files** 无问题；ruff 绿 | PASS |
| 关闭语义（AC-05） | 池单测：`close_all()` 返回值 = 登记连接数（≥3：主线程 + 两条工作线程）、二次调用为 0（幂等）；`ApiDeps.close()` 改走 `close_all()`（`getattr` 兜底单连接注入） | PASS |
| `:memory:` 边界（AC-05） | 池单测：`is_memory_path` 判据 + 两线程拿到**同一条**连接、`connection_count() == 1`；模块文档与用例注释都点名"内存库属于连接" | PASS |
| 真 app 路径（AC-05） | live e2e **36 passed**（真 uvicorn 控制面 + 文件库 ⇒ 真的走每线程连接） | PASS |

## 反证与实测

- **基线测量（WP-A）**：先把 cycle 7 的负载搬成 hermetic 用例再改代码。修复前（池未接入）
  的实测分布是 **24×201、无 5xx、无 404** —— 与 live 探针的历史分布（修复前 19×201/2×500/
  2×404/1×409；加锁后 23×201/1×404/0×500）**不同**。原因如实记录：hermetic 用例里
  `:memory:` + 单连接看到自己的写，而 live 探针的多进程/多连接与真实调度时序不同。
  **因此本轮不宣称"修好了 404"**，只宣称"同一负载在本 harness 干净"（W-3）。
- **代理面兼容是"整库套件"给的证据**：夹具默认走 `:memory:`（退化为共用一条），但**对象
  本身是池**；420 条 API 用例覆盖 ~30 个 store 的全部连接用法（`execute`/`executescript`/
  `cursor`/`commit`/`with` 块/`row_factory`）——这是"代理面没有把原语义改坏"的实测。
- **`__getattr__` 递归陷阱**：转发必须放过下划线名（否则 `current()` 里 `self._shared`
  缺失时会递归进 `__getattr__`）；实现里显式 `raise AttributeError(name)`，池单测
  （文件库 + 内存库两条路径）与整库套件都覆盖到。
- **静态类型边界**：池不是 `sqlite3.Connection` 子类 ⇒ 装配处显式 `cast`（conftest 一处、
  用例一处），并注明"覆盖由池单测 + 整库套件提供"。mypy 看不到鸭子类型（W-2）。
- **50 行/函数硬上限拦了一次**：把池接进夹具后 `conftest.make_base_deps` 变 54 行 ⇒
  `tests/tooling/test_python_source_limits.py` 红（m0 首跑唯一红项）。处置是**拆模块**
  （`tests/api/base_fixtures.py::build_base_deps`，夹具名与 import 面不变），不是调门禁；
  拆完 conftest 118 行、mypy 912 files 绿、`tests/api` 420 例复绿。

## 告警

- **W-1（EC-05 第②半未做）**：统一派发读面（worker claim 与 retry dispatch 各自持有，
  以及两者皆无的三态可判定答案）**不在本 PLAN**。EC-05 因此在 GOAL 的 EC 表里**未被标记为通过**，
  下一 cycle（PLAN-089）承接：读面需同时看 lease 事实与重排事实，且文档化"pause 不撤销
  已持租约"这一既有契约（`tests/contracts/test_pause_dispatch_contract.py:124-145`）。
- **W-2（代理面没有静态表面检查）**：`__getattr__` 转发让"连接上不存在的名字"只会在运行期
  暴露（`AttributeError`），mypy 看不到（装配边界已 cast）。缓解：整库套件 + 池单测覆盖了
  当前全部用法；若将来新增连接 API，仍应同时补一条用例而不是只依赖转发。
- **W-3（404 不在本 harness 复现）**：见"反证与实测"首条——EC-05 verify 里"无 404"的判据
  以本 harness（文件库 + 12 线程 24 次登记）为准；live 探针的历史 404 仍无 hermetically
  可复现的根因，**不做修复声明**。
- **W-4（池不做线程死亡回收）**：线程结束时其连接留在登记表里直到 `close_all()`。
  线程数受 threadpool/守护线程上限约束（连接数 = 用到连接的线程数），但"长跑进程里连接
  随线程增长"是运维事实，读面只提供 `connection_count()`；若将来需要上限/回收，属新增能力。

## 门禁

- 定向：池单测 **5 passed**；负载用例 **2 passed**；`tests/api` **420 passed**；
  `tests/adapters/sqlite tests/application tests/contracts tests/e2e tests/postgres`
  **1371 passed / 4 skipped**（213.47s，postgres 实跑非 skip，DSN 按固化配方）。
- 类型/风格：`mypy` **Success: no issues found in 911 source files**；ruff check/format 绿。
- live e2e：**36 passed**（真 app + 文件库路径）。
- m0：两次实跑——**①1 failed / 3844 passed**：唯一红项是 `tests/tooling/test_python_source_limits.py`
  的 `conftest.make_base_deps` 54 行（>50 行/函数硬上限，本改动引入）；处置是**拆模块**
  （`tests/api/base_fixtures.py`，夹具名与 import 面不变）而不是调门禁；**②PASS**：
  `PASS: profile=m0; 23 deterministic checks`（全量 pytest **3846 passed / 10 skipped**，
  510.93s，exit 0）。两次红都定位到具体原因并在**代码/记录**上修复，未改门禁。

## 结论

控制面**文件库**路径的连接粒度从"一条连接 + 一把大锁"改为**每线程一条连接**：
`ThreadLocalConnection` 是 store 已经拿到手的那个句柄，但把语句、游标、事务边界与
pragma 面转发到本线程自己的连接上；跨线程写由 SQLite 的 WAL 写锁 + `busy_timeout`
协调。`SerializedConnection` 及其边界/事务/游标用例**原样保留**（它仍是"必须共用一条
连接"场景——`:memory:`、单连接工具——的正确实现）。

结果为 **PASS_WITH_WARNINGS**：W-1 是 EC-05 的另一半（下一 cycle），W-2/W-3/W-4 是
代理面静态检查、404 不可复现、连接回收三条如实边界。**未宣称**"并发问题全部解决"或
"live 的 404 已修"——本轮只把**锁粒度**换到每线程连接，并给出同一负载在文件库路径下的
实测分布。
