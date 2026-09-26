---
id: MEM-20260926-143
title: "写面认证面的四条硬约束；单 token 只能证明「经过认证」不能证明「是谁」；加 4 行也能撞 50 行函数门禁"
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
scope: repository
confidence: 0.9
review_after: 2027-03-26
source_plans:
  - .cursor/plans/tasks/PLAN-20260926-190-principal-model-and-write-face-auth.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260926-191-principal-model-and-write-face-auth-recheck.md
supersedes: []
tags: [authentication, principal, contextvar, middleware, credential-discipline, scale-gate, trust-domain, goal-019]
---

## 做了什么

给控制面加了**主体模型 + 最小认证面**（GOAL-019 EC-01 / EC-02）：
`Principal` 域值对象（id + 类型，**无**租户/角色）；写面（`_MUTATING_METHODS`）
`Authorization: Bearer` 认证中间件（token 从环境变量读、`hmac.compare_digest`
常数时间比较、留空即关闭并在启动时显式警告）；请求主体经
`packages/application/principal_context.py`（contextvar）落到 canonical 事件
（`EventEnvelope.actor`）并在读面可见。**全量 m0 = 23/23**；18 条判据 + 三次按压。

## 为什么这样做

1. **"复用同一分类"要连**例外集**一起想清楚，而不是只复用那个 `frozenset`。**
   幂等面有 `_ANALYSIS_ACTIONS`（分析类 POST 不要求 `Idempotency-Key`），
   那是**幂等**语义的例外。认证面按**方法**分类 ⇒ 分析类 POST **照样要 token**。
   把它当成"同一条分类所以例外也一样"会让一批端点静默免认证。**结论**：
   复用分类 ≠ 复用例外集；例外集必须逐面重新判定并留证。
2. **单一共享 token ⇒ 单一主体。不要做「调用方自报身份」。**
   若允许请求头声明 `X-Principal-Id`，在没有逐调用方凭据的前提下那只可被**伪造**，
   于是系统会**看起来有归因、其实可冒充**——比"没有归因"更坏（它会让人据此做判断）。
   所以 `kind` 固定为 `SERVICE`，"是谁"这一维**如实留空**，边界写进文档与警告文案。
3. **环境式（contextvar）请求上下文是最小缝，但**读点必须回退既有常量**。**
   `RunOrchestrationService` / `EventSink` 是**应用级单例**，主体系**每请求不同**；
   改构造/调用签名会把 principal 穿进几十个调用点，并顶到**两个 450 行零余量文件**
   （`composition.py` / `run_orchestration/service.py`）。用 contextvar 后改**一个读点**
   （`eventing._event_actor`）即可，且 `None` ⇒ 原样返回 `sink._actor`
   ⇒ **未启用认证时行为逐字不变**（这是 EC 的硬判据，不是"顺手"）。
   实测：中间件在 `call_next` **之前**设置 ⇒ 端点内可见（BaseHTTPMiddleware 的
   下游任务复制当前上下文）。
4. **复用另一个信任域的模块前，先读它的包 `__init__`。**
   想复用 worker 网关的 `extract_bearer`，但 `services/api/worker_gateway/__init__.py`
   **急切**导入 `create_worker_app` / `WorkerGatewayDeps` / `WorkerGatewaySettings`
   （其 docstring 自己写着"与 Control Plane 分开，以便 worker 信任域有自己的 auth"）
   ⇒ 复用会把整个 worker 信任域拉进控制面的**导入图**。改为自带 7 行解析器，
   **只沿用同一原语与同一不变量**（`hmac.compare_digest`；空值永不匹配）。
5. **"加 4 行"也能撞 50 行函数门禁——而且只有全量 m0 会告诉你。**
   `create_app` 原本 **47 行**（离 50 行门禁只剩 3 行），加 6 行后 **53 行**判红。
   同一轮还有 `python/format-check` 红（新测试文件没被我先前的手工
   `ruff format --check` 文件清单覆盖）。**两处定向套件当时都是绿的**——
   所以"受影响套件全绿"**不能**替代全量门；**本地不绿不得 push 的判据必须是全量 m0**。
   修法：把装配抽成 `_install_write_face_auth(app)`，`create_app` 回到 48 行。
6. **凭据纪律最有力的反证形态 = 「名字出现 1 次且从不赋值」。**
   `rg "RESEARCHOS_CONTROL_PLANE_TOKEN"` 全工作树**恰好 1 次**（读环境变量的名字常量），
   `RESEARCHOS_CONTROL_PLANE_TOKEN\s*=` **零命中** ⇒ 值只可能存在于运行进程的环境变量里。
   比"我没写进去"更强的说法是"**没有任何可写点**"。同理：`token ==` 形态零命中 +
   唯一比较是 `hmac.compare_digest`。测试夹具用**计算出来的合成值**
   （承 `tests/api/conftest.py` 的 `_FIXTURE_ENDPOINT_KEY` 纪律），并在 docstring 写明
   它**不是**真实凭据。

## 怎么做与复现

```bash
# 1) 三态 + 附随判据（18 条）
.venv/Scripts/python.exe -m pytest tests/api/test_principal_auth.py -q
# 2) 凭据纪律（应当恰好 1 条；第二条应为空）
rg -n "RESEARCHOS_CONTROL_PLANE_TOKEN" --glob '!.git/**' --glob '!.venv/**' --glob '!node_modules/**'
rg -n "RESEARCHOS_CONTROL_PLANE_TOKEN\s*=" --glob '!.git/**' --glob '!.venv/**'
# 3) 常数时间比较（不许 == 比 token）
rg -n "compare_digest" services packages
rg -n "token\s*==|==\s*.*token" services/api/middleware.py
# 4) Idempotency 语义一字未动（AST 取源码段 + sha256[:16] 对 HEAD 比较）
#    IdempotencyMiddleware / .dispatch / _is_analysis_post / _problem 四个哈希应全等
#    （脚本见 RECHECK-20260926-191 第四节）
# 5) 全量门（独占、DSN 固化、仓库 .venv）
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

## 适用边界

- **本轮的主体只能回答「是不是经过认证的调用方」，不能回答「是哪一个」。**
  逐调用方身份需要**逐调用方凭据**（未来工作 / M18 面）；`kind` 固定 `SERVICE`
  是有意的诚实选择，不是遗漏。
- **主体只以字符串形态落在 `outbox_events.envelope_json.actor`**：没有独立列 / 外键 /
  约束 ⇒ 本轮的约束是**代码级**（读点回退 + 单元判据），**不是**数据库级；
  将来任何直接构造 `EventEnvelope` 的路径都能绕过。
- **读点回退只管经 `publish_event` 的事件**；`system:workflow-engine` 等
  **系统自身动作**的 actor 常量**有意保留**（不是"漏改"）。
- **认证只在进程内生效**：反代 / TLS / 多副本**未验证**，也不在本 GOAL 范围。
- `services/api/app.py` 已 **327 行**（>300 软阈值）且 `create_app` 抽助手后才合规
  ⇒ 再加装配行会**再次**撞门禁。
- **不得**因新增认证面而宣称项目安全：`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论）
  原样保留。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260926-190-principal-model-and-write-face-auth.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260926-191-principal-model-and-write-face-auth-recheck.md`
- 相关记忆：`MEM-20260925-141`（一个开关一个读取点 / 判据自身恒真）、
  `MEM-20260925-140`（判据要有权威面与配对）、
  `MEM-20260924-125`（先等本地门到终态再推送）
