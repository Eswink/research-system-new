---
id: PLAN-20260922-131
slug: offline-gate-structural-judge
title: 把「默认门离线」做成整轮结构判据：公网出站发生即红（GOAL-010 EC-05）
status: DONE
created_at: 2026-09-22
updated_at: 2026-09-22
parent_goal: GOAL-20260921-010
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260921-010 cycle 5 = EC-05（出站结构判据，承 `RECHECK-121` W-7）。授权来源：2026-09-21
    用户 goal 模式指令 frontmatter `authorization.ref`——(2) **默认姿态不变**（默认 runtime 保持 Fake、
    默认 CI 离线，AGENTS.md §11）；(5) push-to-main-for-CI（只推 main、不 force、不重写历史）。
    安全口径照抄 GOAL：服务端 URL 仅 http/https，发请求前校验 host 并拒绝 localhost/环回/私有/保留
    （**复用既有 `endpoint_policy`，不新造判据**）；凭据只从环境变量读取；观测隐私不记录完整 Prompt。
    **本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；skip/删除测试、降低断言强度；
    新增依赖、改上游 pin；把真实 runtime 设为默认；把凭据写进 CI；用「本次没观测到出站」充当判据。
    **触到 Domain / Canonical State 边界即 BLOCKED**，留人工拍板。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260922-131-offline-gate-structural-judge.md
memory_entries:
  - .cursor/memory/entries/MEM-20260922-104-network-judge-traps-and-egress-sources.md
---

# PLAN-20260922-131 — 默认门离线的整轮结构判据（GOAL-010 EC-05）

## 目标

把「**默认门离线**」从**约定**变成**结构判据**：在不显式开门（不声明 live 开关）的默认测试运行里，
**任何一次通向公网目的地的出站尝试都会让发起它的用例判红**——判据**不依赖人工观察**，
也**不依赖凭据是否可解析**（这正是 `RECHECK-121` W-7 暴露的缺口）。

反证必须成立：**关掉守卫** ⇒ 常驻证物 RED；复原 ⇒ GREEN。**不得**用「这一轮没看到出站」充当判据。

## 验收条件

- **AC-1 整轮覆盖**：判据的作用域是**一轮默认测试运行**（不是某条用例、某条代码路径）：
  任何用例里发生的公网出站尝试都被判红，且**点名**发起者（nodeid）与目的地。
- **AC-2 不依赖环境**：同一套件在「凭据**可**解析」（`.env` 已进进程）与「凭据**不可**解析」
  两种状态下**同结论**——W-7 的红正是「凭据可得性驱动的环境签名」，这一条必须被封住。
- **AC-3 反证成对且**被压过：**常驻证物**（对**不可路由**的保留地址发起的真实连接尝试**被拦下**）
  + **非空转正对照**（对环回/私网目的地的连接尝试**不被**拦）。按压（关掉守卫）⇒ 证物 RED；
  复原 ⇒ GREEN。两向都留证据。
- **AC-4 不误伤既有套件**：判据开启后默认全量测试**全绿**（docker / postgres / observability /
  distributed 等既有依赖环回或私网目的地的套件不受影响）；若真有合法公网出站，**先如实登记**
  再决定（不得默默放行）。
- **AC-5 口径单一来源**：目的地分类**复用** `packages/application/model_relay/endpoint_policy.py`
  的既有 host 判据（不新造第二套分类、不改它的判定语义）；**Domain 一字不动**。
- **AC-6 门禁与记录**：规模门禁自查（50 行函数 / 450 行文件）→ 定向套件 → m0 全量 23/23 →
  治理 `validate.py` 绿 → 独立 RECHECK（含 W 列表）→ GOAL 回写（EC-05 状态 / 迭代日志 /
  `child_plans` / `latest_recheck` / `memory_entries`）。

## 证据（derive 阶段实测；**只读代码/配置/日志，未发起任何真实调用**）

| # | 事实 | 核对方式 | 对 EC-05 的含义 |
| --- | --- | --- | --- |
| E-1 | 被捕获的那次真实出站是 `GET https://apihub.agnes-ai.com/v1/models` ⇒ `200 OK`，发生在**全量 m0 期间**；触发条件是「前序 import 过 openhands-sdk ⇒ litellm `load_dotenv()` ⇒ `.env` 凭据进进程」 | `RECHECK-121` W-7（三轮表 + 失败用例名） | 缺口不是「某条路径忘了关门」，而是**整轮没有宪法**：出网由一个**谁也没 mock** 的路径发起 |
| E-2 | 既有的「零出站」判据是**逐用例 mock `socket.socket`**：`mock.patch.object(socket, "socket", _no_network)`，且断言的是**该用例关心的那条路径** | `tests/e2e/test_ec04_live_gate_offline.py::TestZeroOutboundWhileClosed` 等 | 判的是**路径**不是**运行**：没人想到的路径**天然逃逸**——W-7 就是这么漏的 |
| E-3 | host 分类**只有一份**判据：`endpoint_policy._host_kind` / `_is_reserved`（localhost / link_local / private / reserved / public / domain）；公开面是 `validate_endpoint_url` / `endpoint_url_refusal`，**入参是 URL**，没有「按 IP 判类」的公开助手 | `packages/application/model_relay/endpoint_policy.py`（全文） | 守卫要在 socket 层判**目的地 IP** ⇒ 需要把既有判据**暴露**（不是新写一套分类） |
| E-4 | pytest 配置：`testpaths = ["tests"]`，`pythonpath = ["."]`，**仓库根没有 conftest**；`tests/conftest.py` 是测试树的根配置（docker/gpu 的环境探测式 skip 就在那里） | `pyproject.toml:101-117`、`tests/conftest.py` | 守卫放 `tests/conftest.py`（或其引用的新模块）即**覆盖默认门收集到的全部用例**，且不需要新增根 conftest |
| E-5 | m0 的 `python/tests` = `python -m pytest --ignore=<boundary_test>`，**不给路径** ⇒ 走 `testpaths` | `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py:123-126` | 「默认门」的 python 面 = `tests/`；其它作业（`collector-quality` / `container-quality` / TS 四作业）各自是独立进程与独立根，**不在本判据射程内**（如实登记为边界） |
| E-6 | `.env.example` 里有 `ALLOW_PUBLIC_NETWORK=false`，但**全仓零消费者**（`rg` 只命中该文件） | `rg -n ALLOW_PUBLIC_NETWORK` | 它是**已声明未接线**的产品侧安全旋钮；把守卫的放行面挂在它上面会**改变它的语义**（产品策略 ≠ 测试门），**不采用**，如实登记 |
| E-7 | `.env`（gitignored）持凭据；操作者配方是 `set -a; . ./.env; set +a`；openhands-sdk 的 litellm 会**自行**把 `.env` 读进**任何 import 过它的进程** | `docs/integration/LIVE_MODEL_RUNBOOK.md`、`RECHECK-121` W-7 | AC-2 的两种进程状态**都能构造**：带 `.env` / 不带 `.env` 各跑一次 |
| E-8 | live 门的既有语汇是**显式命名开关**（`RESEARCHOS_AGENT_RUNTIME=openhands` + 凭据可解析），live 用例的声明方式是 **pytest marker `requires_live_llm`** | `services/api/runtime_support.py`、`pyproject.toml` markers、各 live 套件 `pytestmark` | 放行面应当**同源**：按 **marker** 放行（不是按环境变量），与既有门语汇一致且**不依赖环境** |

## 已知的**不可回避**取舍（定案必须选一个并写明代价）

1. **判据住在哪一层**：进程级 socket 守卫（**能判「发生」**，代价是一个新的 conftest 组件 +
   必须证明它不误伤既有套件）vs. 扫描式 validator（便宜，但**判的是代码形态**，
   满足不了「出站发生 ⇒ 红」——W-7 那种「谁也没想到的路径」正好逃逸）。
2. **放行面**：按 marker 放行（同源、非环境依赖）vs. 按环境变量放行（便宜，但**环境一变口径就变**，
   正是 EC-05 明文要避免的形态）。
3. **拦截语义**：**拦下并抛错**（出站根本不会发生，符合「默认门离线」的字面承诺）vs. **放行但记账**
   （能观测真实行为，但「离线」就不再是结构事实）。EC-05 要求前者；后者只允许出现在**按压**里。
4. **目的地分类的射程**：socket 层看得见的是**已解析的 IP**；**DNS 查询本身不经 `socket.connect`**
   ⇒ 本判据**不覆盖 DNS**（如实写进边界，不假装覆盖）。

## 候选面（WP1 在此表上定案）

| 候选 | 形态 | 代价 | 已知风险 |
| --- | --- | --- | --- |
| (a) `tests/conftest.py` 里的**进程级 socket 守卫** | 包装 `socket.socket.connect` / `socket.create_connection`；目的地按既有 `endpoint_policy` 判类，**公网/保留 ⇒ 抛错并点名**；环回/私网/链路本地放行；当前用例带 `requires_live_llm` ⇒ 放行 | 一个新模块 + 必须实测「默认套件零公网出站」 | 误伤既有套件（docker/postgres/observability）；对 SSE/子进程内的出网不可见（子进程有独立解释器） |
| (b) 扫描式 validator（源码里出现未声明的出网调用点即红） | 静态规则，无运行成本 | 判**形态**不判**发生**；误报面大（网关、probe 本来就该出网） | **不满足** AC-1/AC-3，只能当补充 |
| (c) 继续扩既有 per-test mock | 每个新用例各自 mock | 零新架构 | **结构上无法**覆盖「没人想到的路径」——W-7 已证明 |

## WP1 定案（**已完成**：取 (a) 的「进程级 socket 守卫 + marker 放行」形态）

### 逐条回答四个取舍

1. **判据住在哪一层** ⇒ **(a) 进程级 socket 守卫**，由 `tests/conftest.py` 在**导入期**装配
   （E-4：这是默认门唯一覆盖全部用例的位置）。理由：EC-05 要的是「**出站发生 ⇒ 红**」，
   只有**拦截点**能判「发生」；(b) 判的是代码形态，(c) 已被 W-7 证否。
2. **放行面** ⇒ **按 pytest marker `requires_live_llm`**（E-8：既有语汇，且**不依赖环境**）。
   守卫在 `pytest_runtest_setup` 记下当前用例，socket 拦截点据此裁决；**没有当前用例**
   （收集期 / 导入期 / 用例之外）⇒ **默认拒**（fail-closed）。
   **不采用**环境变量放行（那正是 EC-05 明文禁止的「依赖环境的弱化形态」），
   **不采用** `ALLOW_PUBLIC_NETWORK`（E-6：产品策略旋钮，语义不同）。
3. **拦截语义** ⇒ **拦下并抛错**：`PublicNetworkBlocked(RuntimeError)`，消息**点名**目的地
   (`ip:port`) 与发起用例 nodeid，并写明放行方式（live 用例挂 marker）。出站**根本不会发生**
   ——这才是「默认门离线」的字面承诺。「放行但记账」只允许出现在**按压**里。
4. **分类射程** ⇒ 只判 **`connect` / `connect_ex` 的 AF_INET / AF_INET6 目的地**。
   **DNS（`getaddrinfo`）不在射程内**（E-…：它不经 `socket.connect`），**UDP / 子进程 /
   非 python 作业**同样不在射程内 —— 逐条写进「不做边界」，**不假装覆盖**。

### 判定集合（复用既有判据，不新造）

- **分类来源**：把 `endpoint_policy` 里**已经唯一存在**的 host 判据暴露成公开助手
  `destination_kind(host) -> str`（返回 `localhost` / `link_local` / `private` / `reserved` /
  `public` / `domain`），实现就是 `return _host_kind(host)` —— **判定语义一字不改**，
  只是把「只有本模块能问」变成「门也能问」（E-3 的公开面只吃 URL，socket 层拿到的是 IP）。
  代价：`endpoint_policy.py` 一处**加性**改动（+1 函数、`__all__` 若存在则同步）。
- **拒**：**除环回以外的一切**（含 `private`）。**这条是 WP3 实测改过的**：derive 时写的是
  「拒 `public` + `reserved`、放 `private`」，实测发现本机 DNS 走 fake-IP 代理、公网域名解析到
  `198.18.0.0/15`，而 `ipaddress` 把它归**私有** —— 按原稿那条真实出站会**静默通过**。
  放行面因此在落地时收窄到 `localhost` 一类，理由与证据写进 `tests/egress_guard.py` 的 docstring。
- **放行**：`localhost`（`127.0.0.0/8`、`::1`）—— 既有套件（docker / postgres / observability /
  distributed）连的都是这一类。
- **不判**：`domain` —— socket 层见到的已是**解析后的 IP**，不应当出现域名；真出现就按
  **fail-closed 拒**（并让消息点名，便于定位）。

### 常驻证物与正对照（AC-3）

1. **证物（拒的向）**：`socket.create_connection(("198.51.100.1", 443), timeout=2)`（**RFC 5737
   TEST-NET-2 文档地址，永不是真实服务**：落在 `private`）⇒ 必须抛 `PublicNetworkBlocked`。
   **「文档地址」不等于「不可路由」**（WP3 实测纠正）：本机 fake-IP 代理对**任意** IP 都秒回连接
   （`1.1.1.1` 与各文档地址全部 0.02s 内 CONNECTED）⇒ 证物「不真出网」靠的是**判据在发 SYN 前拦下**，
   **不是**靠地址不可路由。这条纠正同时推翻了本 PLAN derive 稿里「按压时不会真出网」的说法（见 P-1）。
2. **分类单向断言**（避免证物依赖真实出网）：`destination_kind("1.1.1.1") == "public"` 且
   判定集合拒它 —— **只判分类，不发连接**。
3. **正对照（放的向）**：对一个**真实在听的环回端口**（`bind(("127.0.0.1", 0))` + `listen()`）
   发起连接 ⇒ **必须成功**（既证明守卫没有把一切都拦掉，也证明它不误伤既有套件）。
4. **装配断言**：默认门里守卫处于 armed 状态（不是「恰好没触发」）。

### 按压（AC-3 的另一半，**零真实出站**）

把守卫改成「只记账不拦」⇒ **证物 1 立刻 RED**（它会拿到 `ConnectTimeout`/`ConnectionError`
而不是 `PublicNetworkBlocked`）；复原 ⇒ 复绿。**注意（实测纠正）**：撤防后那次连接**真的会连上**
（本机代理对任意 IP 秒回），所以按压**必然**产生一次受控出站——按压取最小次数、只发一次、如实登记。

## WP2 落地记录（判据本体）

**两条机制**（缺一条都留缺口）：

| 机制 | 位置 | 判的是什么 | 为什么不能只靠另一条 |
| --- | --- | --- | --- |
| **拦** | `EgressGuard.judge`（装在 `socket.socket.connect` / `connect_ex` **与**事件循环的 `sock_connect`） | 出站**发生**（先于任何数据包） | 光拦不判：异常会被调用方当普通连接失败吞掉 |
| **判** | `tests/conftest.py::pytest_sessionfinish` 按**记录**收口 | 整轮**发生过**探针之外的阻断 | 光判不拦：数据包已经出去了，「默认门离线」就成了空话 |

**两个面都要装**（第二面是**独立复检**逼出来的）：Windows 的 Proactor 事件循环用
`_overlapped.ConnectEx` 直接发起连接，**一次都不经过** `socket.socket.connect`——复检实测
`asyncio.open_connection` 连到 LAN 地址**成功**且 `judged 0`。异步栈（anyio / httpcore /
`httpx.AsyncClient` / aiohttp）与仓内 `adapters/mcp/transport.py` 都在那条线上。
第一版装的是**抽象基类** `asyncio.events.AbstractEventLoop`——复检指出那是**错话**：
它上面那份是 `raise NotImplementedError` 桩、对实际循环**不可达**（W-8）。改成装两个**具体实现**
（`BaseSelectorEventLoop` + `BaseProactorEventLoop`），并补一条**行为**判据（selector 循环上的
异步连接必须被拦下），这样「异步面已覆盖」才不是靠同步面兜底说出来的。
`disarm()` 按「该类是否自带该属性」原样复原（继承来的就删掉，不把继承函数固化进子类 `__dict__`）。

- **归因**：每条阻断带调用链摘要（`EgressAttempt.origin`，项目内帧由内到外、最多 6 帧；
  伪文件名如 `<frozen runpy>` 不算项目帧——第一版实测被它填满过）。
- **判据自证的豁免是点名的**：只有探针地址（RFC 5737 TEST-NET-2 的 `198.51.100.1`）不计入
  会话级红灯，同网段的另一个地址照样判红（`test_only_the_named_probe_is_exempt`）。
  **为什么不是 TEST-NET-1**：它的字面量会被 `validate_bundle.py` 的「旧项目版本引用」正则
  读成一个旧版本号（实测误报，不是本 PLAN 要改的门禁）⇒ 换个文档网段即可绕开，**不动门禁**。
- **射程不变**：DNS / UDP / 子进程 / 非 python 作业仍不在射程内（下节）。

## WP3 测量记录（EC-05 的核心证据；全部为真实运行输出，非推断）

| # | 场景 | 命令 | 实测 | 结论 |
| --- | --- | --- | --- | --- |
| M-1 | 全量默认门 + 守卫（**会话级红灯尚未加**） | m0 的 `python/tests`（`scratch/m0-goal010-cycle5-wp2.log`） | `judged 745`、`blocked 4`；套件 PASS | 745 次连接里 4 次被拦：3 次是判据自证探针，**1 次是真实出站** |
| M-2 | 上面那 1 次是谁 | 同上日志 | `BLOCKED 198.18.0.59:443 by <outside-a-test>` | **收集期**（没有当前用例）发生，正是 W-7 的形态：谁也没想到的路径 |
| M-3 | 全栈定位 | `scratch/probe_outside_a_test_egress.py`（把整条栈写文件，绕开 pytest 捕获） | `tests/adapters/openhands/test_adapter_core.py:5` → `openhands/sdk/.../logger.py:16` → `litellm/__init__.py:520` → `get_model_cost_map.py:287 get_model_cost_map` → `:159 fetch_remote_model_cost_map` → `httpx.get(...)` | **`import openhands.sdk` 会在导入期拉着 litellm 去公网拉 model cost map**（默认 URL 在 `raw.githubusercontent.com/...`，失败才回退 wheel 自带副本） |
| M-4 | 只收集、不跑用例（干净复现） | `python -m pytest --collect-only -q` | `judged 1`、`blocked 1`、**exit 1**（会话级红灯生效） | 与 M-1 同址：**收集期出站可复现**，且新判据把它判成了红 |
| M-5 | 按上游开关修源头 | `tests/conftest.py` 在任何测试模块导入 litellm 前置 `LITELLM_LOCAL_MODEL_COST_MAP=True` | `judged 0`、`blocked 0`、**exit 0** | 收集期**一次连接都不再发生**（不是「拦下了」，是**没有**） |
| M-6 | AC-2 凭据态无关 | `tests/api/test_runs_api.py`，`.env` 已载入 vs 未载入 | 两种状态 **16 passed**（同结论） | 结论不随凭据可得性变化；W-7 那种「环境签名」不再是判据的依赖 |
| M-7 | **两向复测**（同一棵树，只切那个开关） | `LITELLM_LOCAL_MODEL_COST_MAP=False` + `--collect-only` vs 默认（conftest 置 True） | 关掉固定 ⇒ `judged 1`/`blocked 1`/**exit 1**，归因点名 `test_adapter_core.py:5:<module>`；置上 ⇒ `judged 0`/`blocked 0`/**exit 0** | 「是谁在出网 + 修好了没有」两问都由**判据自己**回答：归因精确到模块级 import 那一行 |
| M-8 | **环境事实纠正**：文档地址到底可不可路由 | `scratch/measure_doc_address_reachability.py`（**撤防**后测环境本身） | RFC 5737 三个文档网段（TEST-NET-1/2/3）的地址与 `1.1.1.1` **全部** `CONNECTED`（0.02s；async 0.00s） | 本机 fake-IP 代理对**任意** IP 秒回 ⇒ 「文档地址=不可路由」是**错的**；证物的「不真出网」靠**判据先拦**，不靠地址。derive 稿与 P-1 的「不会真的出网」据此更正 |
| M-9 | **异步面复检（W-1）** | 独立复检的执行记录：`asyncio.open_connection("172.29.96.1", 31356)`（**撤防**等价场景）**成功握手**且 `judged 0` | 洞被证实：Windows Proactor 走 `_overlapped.ConnectEx`，绕开 `socket.socket.connect` | 判据补第二面（事件循环 `sock_connect`），见 P-4 |
| M-10 | **同一棵树、另一台机器（CI）**：默认门在**干净安装**下跑 | 推送提交 `87208aa` 的 M0 run（CI 作业 `quality-windows-latest`，日志 `scratch/ci-87208aa-win-job.log`） | `egress guard: FAIL — … 31 non-loopback destination(s)`，**全部**是 `57.150.192.193:443`，全部归因到各测试模块的 `import openhands.sdk` 行；本树同一轮是 `judged 771`/`blocked 8`（**8 = 探针**）⇒ **本机绿、CI 红** | 差异不是判据，是**环境**：CI 是全新安装。判据在 CI 上抓到了**第二条真实出站**，而本机因缓存已热**看不见**它 |
| M-11 | **定位并三相当场测量** | `scratch/probe_tokenizer_egress.py`（三模式：`cold-armed` / `cold-disarmed` / `warm-armed`，日志 `scratch/tokenizer-egress-*.log`） | ①`cold-armed`：`import litellm` 被拦，`PublicNetworkBlocked` 指向 `198.18.1.80:443`，缓存目录**空**；②`cold-disarmed`：导入成功，缓存里**落下一个文件** `9b5ad71b2ce5302211f9c61530b329a4922fc6a4`；③`warm-armed`：同一导入**零尝试**、缓存非空 | 源头 = litellm 首次导入时 `compression → token_counter → default_encoding` 调 `tiktoken.get_encoding("cl100k_base")`，**下载词表**到 litellm 自带的 tokenizers 目录（就是「第一次导入才发生、之后不再发生」的形态） |
| M-12 | **修源头（不含测试）** | `.github/workflows/m0-quality.yml` 四个 Python 作业在 `uv sync --frozen --dev` 之后加 `Prewarm the offline tokenizer cache`（`uv run --frozen --no-sync python -c "import litellm"`） | 预热门在**判据进程之外**跑（作业步骤，不是 pytest）⇒ 词表在判据装上前就已落地；判据本身**一行未改**、marker 面未动 | 修的是「第一次导入会下载」的条件，**不是**把出站判绿；CI 侧复验见 GOAL 迭代日志第 5 行的 CI 台账尾（本轮推送的 run 终态） |

**如实登记的边界**：M-3 定位到的是**第三方导入期出站**（litellm 元数据），不是产品代码调端点；
W-7 当初观测到的目标是中转站（`apihub.agnes-ai.com`）而不是 GitHub —— 本条**不声称**解释了 W-7 的
那一次，只声称：**默认门的收集期确实存在真实出站，且新判据能点名它**。

**M-10…M-12 带来的第二条纠正（比 M-8 更要紧）**：M-5 的 `judged 0` **不是**「默认门离线」的证明——
它只证明**这台机器此刻**离线。同一棵树在 CI 的干净安装下判据立刻抓到 31 条真实出站（M-10）。
「判据在本机绿」与「默认门离线」是两回事；**判据的价值恰恰在于它能在别人的机器上把本地缓存
掩盖掉的出站点出来**。这条也说明：只要那个第一次导入的下载条件还存在（R-6），「零出站」就是
**环境相关的**，不能写成无条件事实。

**产品侧残余（不在本 PLAN 射程，登记）**：同一开关在**产品进程**里没被置上（adapter 启用真实
runtime 时同样会 import litellm）⇒ 真实 runtime 的进程启动时会向 GitHub 发起一次元数据请求。
产品侧如何钉（compose/env/adapter 文档）属产品决策，**不**在本 PLAN 悄悄改。

### 按压记录（每一发都留证）

| # | 按压 | 期望 | 实测 |
| --- | --- | --- | --- |
| P-1 | `guard.disarm()`（只记账不拦） | 证物用例 RED | 5 个真实 FAILED（拿到 `ConnectTimeout` 而不是 `PublicNetworkBlocked`）；复原后 12 passed，`git diff` 空。**更正**：当时记的是「零真实出网」，M-8 证明**这条不成立**——撤防那一下连接**真的连上了**（代理秒回）。按压仍然成立（拦的是判据），但那次是**一次受控出站**，如实改记 |
| P-2 | 临时停用会话级红灯（`pytest_sessionfinish` 提前 return），只跑按压用例 | 吞掉异常后**整轮仍绿**（这就是修之前的形态） | `1 passed`、**exit 0** |
| P-3 | 恢复会话级红灯，同一发按压用例 | 用例仍绿，但**整轮红** | `24 passed`、**exit 1**，并打出目的地 / 类型 / nodeid / 调用链 |
| P-4 | **异步面**（W-1）：`scratch/press_async_face.py` 在同一进程里 armed → disarmed → re-armed | 撤防后**不再**被拦 | `armed: BLOCKED by the guard` ⇒ `disarmed: reached the wire: connected (!!)` ⇒ `re-armed: BLOCKED` —— 异步面确实是判据在拦（且这次撤防**真的连上了**，与 M-8 一致） |
| P-5 | **W-8 的错版按压**：把 `_loop_classes()` 临时改回「只装抽象基类」 | 新判据必须抓住这个错版 | **4 个用例真 FAILED**（两条异步拦截用例 + selector 身份用例 + 装/卸用例），并打出 `judged 3`/`blocked 0`——**异步尝试根本没进判定**，正是 W-1 的形态；复原后 28 passed / exit 0 |

**按压不动树**：P-2/P-3 的按压用例是**临时**加进判据自证文件的，按压后移除（`git status` 里不留痕）。

## 不做边界（写死）

- **不覆盖 DNS**：`getaddrinfo` 不经 socket；若将来要覆盖，需要单独设计（且本机 DNS 走 fake-IP
  代理 ⇒ 会误报，见 [[live-run-enablement-recipe]] 的同类教训）。
- **不覆盖子进程**：`pytest` 里 spawn 的解释器（`distributed` / docker sandbox / collector）
  有各自进程，**补丁不继承**。
- **不覆盖非 python 作业**：`typescript/*` 四作业与 `collector-quality` / `container-quality`
  各有独立进程与独立根（E-5）。
- **不覆盖 UDP**：`sendto` 不拦（本仓没有 UDP 面；如实登记而不是假装覆盖）。

## 实施清单

- [x] WP1 **定案（承重墙，先审后改）**：在候选面表上定案——判据形态、覆盖范围、分类来源（复用
      哪一处既有判据、是否需要把它暴露成公开助手）、放行面、拦截语义、**不做**边界（DNS / 子进程 /
      其它作业）。产出：定案 + 代价 + 回退路径。**先落记录再改代码**。（放行面在 WP3 依实测收窄，
      见「判定集合」一条的修订说明。）
- [x] WP2 **按定案落地**：守卫 + **常驻证物**（对不可路由文档网段地址的真实连接尝试被拦下）+
      **非空转正对照**（环回目的地不被拦）+ 归因 + 会话级红灯 + 文档同源（`AGENT_RUNTIME.md` §3.4）。
- [x] WP3 **测量（EC-05 的核心证据）**：默认门下跑全量并如实记录出站尝试数与发起者（M-1…M-4）；
      定位到源头后按上游开关修掉并复测（M-5）；凭据态两跑同结论（M-6）；三发按压留证（P-1…P-3）。
- [x] WP4 **门禁 + 复检 + 收口**：定向 → m0 23/23 → 治理绿 → RECHECK（**两遍独立复检**）→ GOAL 回写。

## 影响报告

- **产品面**：**零改动**。守卫住在测试树里；`endpoint_policy.destination_kind` 是**加性**改动
  （`return _host_kind(host)`，判定语义一字不改）。
- **测试进程行为**：`tests/conftest.py` 在导入期置 `LITELLM_LOCAL_MODEL_COST_MAP=True`
  （上游为离线场景提供的开关）。影响面**仅限测试进程**：litellm 改用 wheel 自带的 cost map
  副本，代价是成本表可能比远端旧——换来的是**收集期不再出网**且成本表**不随网络变**（可重复性）。
  操作者若显式设成别的值，守卫会把那次出站拦下并让整轮判红（**fail-closed，不静默**）。
- **文档**：`docs/architecture/AGENT_RUNTIME.md` 新增 §3.4，把「默认门离线」从约定改成
  **整轮结构判据**并写明射程与那条真实出站的处置。
- **Domain / Canonical State**：不动。**OpenAPI / 快照 / 前端**：不动（无 DTO / 路由变化）。
- **CI**：默认 CI 仍离线（且现在**可证**：收集期零连接）；live 用例按 marker 放行；
  未新增 workflow、未注入凭据。
- **上游**：不新增依赖、不改 pin；只用上游**已声明**的环境开关，不改上游代码。
- **观测隐私**：守卫只记**目的地 IP/端口 + nodeid + 调用链帧名**，不记任何请求内容（AGENTS §10）。

## 不做（写死，防扩边）

- **不**改 `endpoint_policy` 的判定语义（只可能**暴露**，不重写）。
- **不**碰 `ALLOW_PUBLIC_NETWORK`（E-6：语义属于产品策略面）。
- **不**为了让守卫不误伤而放行私有网段以外的任何类别；任何放行都要**逐条写明理由**。
- **不**把守卫做成「本轮没观测到出站 ⇒ 绿」的形态（AC-1 明文禁止）。
- **不**在 CI 里注入凭据、不把 live 开关写进任何文件。
- **不**顺手改产品侧 litellm 环境（同一开关在产品进程里的钉法属产品决策；只登记残余，不悄悄改）。
- **不**因为探针地址触发了某个门禁的正则误报就去改那个门禁（改地址即可；门禁本身的问题另行登记）。

## 已知残余（不在本 PLAN 射程，逐条登记）

| # | 残余 | 影响 | 谁来决定 |
| --- | --- | --- | --- |
| R-1 | **产品进程**未置 `LITELLM_LOCAL_MODEL_COST_MAP`：启用真实 runtime 时，进程会向 `raw.githubusercontent.com` 发起一次元数据请求 | 供应链/隐私面的一条第三方出站；不属「默认门离线」 | 产品决策（compose / adapter 文档 / 环境模板），另开条目 |
| R-2 | 判据射程外的出网口：**DNS（`getaddrinfo`）/ UDP（`sendto`）/ 子进程 / 非 python 作业 / 自定义事件循环实现**（如 uvloop 覆盖 `sock_connect` 时需另装） | 这些面上的出站仍不可见；本 PLAN **不声称**覆盖 | 若要覆盖需单独设计（DNS/UDP 那面还会被 fake-IP 代理与「局域网 DNS 解析器」搅：判 UDP 会把正常解析也判红） |
| R-5 | **环回转发代理**：`HTTP(S)_PROXY=http://127.0.0.1:...` 时目的地确实是本机 ⇒ 判据只看到环回，转发出去的那一跳不可见（复检测到：本地监听器真的收到了 `GET http://example.invalid/ping`） | 「默认门离线」在这条配置下**不再是结构事实**；生产与测试都不该依赖本地代理，但仓里没有任何东西阻止它 | 要覆盖需在**应用层**判（读请求行/CONNECT 目标），或对「默认门进程里存在代理环境变量」做前置断言——两条都超出 socket 拦截点，另行设计 |
| R-3 | `validate_bundle.py` 的「旧项目版本引用」正则会把 RFC 5737 TEST-NET-1 地址读成旧版本号 | 任何文档/测试里写 `192.0.2.x` 都会判红（本 PLAN 只绕开，不改门禁） | 门禁维护者（误报面：文档网段字面量） |
| R-4 | `.cursor/runtime/evolution_state.json` **没有跨进程锁**：两个并发进程同时碰它 ⇒ `WinError 5` 或 eval 失败（**已用两次并发调用复现**） | `framework/run_cursor_framework_evals` 会 flake；**m0 必须独占运行**（并发 pytest/hook/同一脚本的另一次调用都是嫌疑共现方） | 框架维护者；本循环的纪律是「m0 独占」 |
| R-6 | **CI 每次仍要下载一次那个词表**：预热门只是**把下载挪到判据进程之外**，并没有取消下载（M-12） | 判据射程内的出站是零（红门不再误报），但「默认 CI 完全离线」这句仍**不成立**——作业层面每轮仍有一次对外请求；断网环境里 CI 会退化成导入失败而不是判据红 | 要彻底离线需把该 blob **随仓库/镜像固化**（vendor 进镜像或私有源），属 CI 供应面决策；本轮如实登记，**不**声称已离线 |

## 回退路径（写明）

纯测试面改动：回退 = 删掉守卫模块与 `tests/conftest.py` 的接线（+ 若做了暴露助手的加性改动则一并
撤销），**不涉及** Domain / Canonical State / 数据迁移 / 产品行为。回退后既有 per-test 判据
（E-2）**原样仍在**，即回退是「判据变弱」，不是「判据消失」——这一点必须在 RECHECK 里写明。

## 状态历史

- 2026-09-22 derive：由 GOAL-20260921-010 的 EC-05 派生（`parent_goal` 投影 ALL_PLAN）。
  **只读代码/配置/日志，未发起任何真实调用**，实测得 E-1…E-8 与候选面表。**承重墙定为 WP1**：
  核心问题是「**整轮**的零出站如何成为**结构**事实，而不是逐用例的路径断言」，以及
  「放行面怎么设计才**不依赖环境**」（EC-05 明文禁止把判据弱化成依赖环境的形态）。
- 2026-09-22 WP2/WP3：守卫落地（拦 + 判两条机制、归因、点名豁免），三发按压留证；
  测量中判据**自己抓到一条真实的收集期出站**（litellm 导入期拉 model cost map，M-2…M-4），
  按上游开关修源头后复测 zero（M-5），凭据态两跑同结论（M-6）。
  **WP1 定案的放行面依实测收窄**（fake-IP 段落在 `private` ⇒ 只放环回），
  这条修订是本循环最重要的实测纠正。
  **一处可复用的自伤**（写下来免得再犯）：写自证用例时**三次**把子串当身份用
  （`"egress_guard" in "test_default_egress_guard.py"`、探针里占位名与 `CUSTOM_TIKTOKEN_CACHE_DIR`
  撞名、`"cold-disarmed".endswith("armed")` 为真）——凡是「名字包含/后缀」这类判据都要改成
  **身份或显式取值比较**，否则判据会在无提示的情况下判错方向。
- 2026-09-22 WP4/收口：**两遍独立复检**（第一遍证伪头号命题 ⇒ 补异步面；第二遍复验通过并指出
  W-8 ⇒ 改装具体循环类），`RECHECK-20260922-131` = **PASS_WITH_WARNINGS**（W-1/W-8 已修，其余逐条登记）；
  m0 全量在本树通过（**数字见 GOAL 迭代日志第 5 行**）；GOAL 的 EC-05 置 **PASS**。
- 2026-09-22 收口后 CI 回灌（M-10…M-12）：推送提交 `87208aa` 的 M0 在 `quality-windows-latest` **红**，
  判据在**干净安装**下点名 **31 条** `57.150.192.193:443` 真实出站（本机同轮 `judged 771`/`blocked 8`
  全为探针）⇒ 定位到 litellm 首次导入的 `tiktoken` 词表下载（M-11 三相当场测量），
  在 **workflow 作业步骤**里预热门修掉（M-12，判据与放行面**一行未改**）。
  **如实登记**：本机 M-5 的「zero」是**环境相关**的，不能当无条件事实；残余 **R-6**
  记明「下载只是被挪出判据进程，CI 并未完全离线」。
