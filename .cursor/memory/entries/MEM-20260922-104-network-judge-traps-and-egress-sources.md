---
id: MEM-20260922-104
title: "网络判据的五个现场陷阱（实测）：Proactor 绕开 socket.connect 补丁；本机代理对任意 IP 秒回（「文档地址=不可路由」是错的，撤防即真出网）；litellm 导入期拉 cost map（默认门/CI 收集期真出网）；validate_bundle 把 TEST-NET-1 读成旧版本号；framework evals 共享状态文件无跨进程锁"
status: ACTIVE
created_at: 2026-09-22
updated_at: 2026-09-22
scope: repository
confidence: 0.9
review_after: 2027-09-22
source_plans:
  - .cursor/plans/tasks/PLAN-20260922-131-offline-gate-structural-judge.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260922-131-offline-gate-structural-judge.md
supersedes: []
tags:
  - egress
  - test-gate
  - windows
  - litellm
  - framework-evals
  - goal-010
---

# 网络判据的五个现场陷阱（GOAL-010 EC-05 实测）

## 做了什么

把「默认测试运行零出站」做成**整轮结构判据**（`tests/egress_guard.py` + `tests/conftest.py` 接线）：
拦截点**拦**（`socket.socket.connect` / `connect_ex` 与两个具体事件循环类的 `sock_connect`，
先于任何数据包抛错）+ 会话收尾**判**（按记录把整轮判红，即使调用方吞掉异常）。
过程中踩到并**用命令复现**了五个**环境/上游**事实，抽出来复用。

## 为什么这样做

- **判据必须判「发生」而不是「形态」**：既有的「零出站」判据是逐用例 mock `socket.socket`，
  判的是**某条路径**——没人想到的路径天然逃逸（`RECHECK-121` W-7 的真实出站就是这么漏的）。
- **判据必须能自己归因**：一条「有人出网」而不指出「谁出网、从哪一行」的记录，等于把定位成本
  留给人工观察；实测正是靠归因才把「litellm 导入期拉 cost map」这条路径点名到**模块级 import 那一行**。
- **只有「拦」不够**：库会把连接失败当常规错误**吞掉**，收集期/用例外更没有用例可判红——
  所以「按记录判红」是第二条机制，缺它就等于默认门仍然可能悄悄出网。

## 怎么做与复现

1. **异步栈绕开同步补丁（Windows）**：Proactor 事件循环走 `IocpProactor.connect` →
   `_overlapped.ConnectEx`，**一次都不经过** `socket.socket.connect`。复现：武装守卫后
   `asyncio.open_connection(<LAN IP>)` **成功握手**且判据 `judged 0`。修法：同时替换
   `asyncio.selector_events.BaseSelectorEventLoop.sock_connect` 与
   `asyncio.proactor_events.BaseProactorEventLoop.sock_connect`。**别装抽象基类**
   （`asyncio.events.AbstractEventLoop.sock_connect` 是 `raise NotImplementedError` 桩，
   对实际循环不可达——装了等于没装，selector 面只是被同步面兜住）。
   复原要点：`{类: (该类是否自带该属性, 原件)}`，不自带的用 `delattr`，否则会把继承函数
   固化进子类 `__dict__`（实测这条让「复原」判据先红了）。
2. **本机没有「不可路由」地址可用**：fake-IP/TUN 代理对**任意** IP 秒回连接——撤防后实测
   TEST-NET-1/-2/-3 的地址与 `1.1.1.1` **全部** 0.02s 内 `CONNECTED`（脚本：
   `scratch/measure_doc_address_reachability.py`）。推论：**任何「撤掉网络守卫做按压」的实验
   都会真的出网**；按压取最小次数并如实登记，判据的安全性只来自「先于 SYN 拦下」。
3. **litellm 在导入期就去公网拉 model cost map**：`httpx.get(<raw.githubusercontent.com 的
   model_prices_and_context_window.json>, timeout=5)`，失败才回退 wheel 自带副本；
   `import openhands.sdk` 会把 litellm 拖进来 ⇒ **默认门与 CI 在收集期就出网**。
   修法：在**任何测试模块 import litellm 之前**置 `LITELLM_LOCAL_MODEL_COST_MAP=True`。
   两向复测：置上 ⇒ `judged 0/blocked 0`；置 `False` ⇒ 判据点名 `test_adapter_core.py:5:<module>`。
4. **`validate_bundle.py` 的「旧项目版本引用」正则误报**：它的模式是
   `(?<![0-9])v?(?:0\.2\.<N>|0\.3\.0)(?![0-9])`，于是 RFC 5737 **TEST-NET-1** 的地址字面量
   （`0.2.` 后跟一位数字）会被读成旧版本号 ⇒ 任何写它的文件（含 PLAN/RECHECK/MEM 与 scratch）
   都判红。修法：网络证物改用 **TEST-NET-2**（`198.51.100.0/24`）或在文本里写成 `192.0.2.x`；
   **不要**为此改门禁（那是误报面，另行登记）。
5. **`.cursor/runtime/evolution_state.json` 没有跨进程锁**：两次并发调用
   `run_cursor_framework_evals.py` ⇒ 一次 `PermissionError: [WinError 5]`（同一路径族）＋
   另一次 eval 语义失败；**单次调用 PASS**（本轮实测复现）。推论：**m0 必须独占运行**
   （并发 pytest / hook / 同一脚本的另一次调用都是嫌疑共现方）；这解释了历史上两次 m0 的同名 flake。

## 适用边界

- **射程**：TCP 连接点两个面（同步 + 异步的具体循环类，`AF_INET`/`AF_INET6`）。
- **不在射程**：DNS（`getaddrinfo`）、UDP（`sendto`）、子进程、非 python 作业、
  **自实现 `sock_connect` 的第三方循环**（如 uvloop）、**环回转发代理**
  （`HTTP(S)_PROXY=127.0.0.1` 时目的地确实是本机，判决只有环回——要覆盖需在应用层判）。
- 判据自证用的豁免必须**点名**地址，不能整段放行；被豁免的阻断仍然会被拦下（只免「会话级红灯」）。

## 来源

- `tests/egress_guard.py`（判据本体，docstring 记录射程与两处实测纠正）；
  `tests/conftest.py`（导入期武装 + `LITELLM_LOCAL_MODEL_COST_MAP` + 会话级红灯）；
  `tests/architecture/python/test_default_egress_guard.py`（28 条自证与按压判据）。
- `PLAN-20260922-131`（M-1…M-9 测量表 / P-1…P-5 按压表 / R-1…R-5 残余）；
  `RECHECK-20260922-131`（两遍独立复检；W-1、W-8 是本条 1/2 的来源）。
- 上游：litellm `litellm_core_utils/get_model_cost_map.py`（开关与该 URL 的出处）；
  `validate_bundle.py:277`（第 4 条的正则）。
