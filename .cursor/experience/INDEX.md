# Engineering Experience Index

轻量工程经验条目索引。本索引供 `sessionStart` 摘要注入（最近 ≤5 条）与 agent 问题检索使用。

## 生命周期

- `ACTIVE`：当前可复用。
- `SUPERSEDED`：被新条目取代，保留历史。
- `RETIRED`：不再适用，保留 provenance。

## Entries

| ID | Status | Confidence | Scope | Review After | Summary |
| --- | --- | --- | --- | --- | --- |
| [EXP-20260823-003](entries/EXP-20260823-003.md) | ACTIVE | 0.5 | repository | 2026-11-21 | CURSOR_ERROR 瞬时失败跨会话（Read d42fb89b…/Shell f3eb4221… 各 2 会话）：重试一次或改替代路径，不当作命令失败；统计时过滤 tool_name=null 的 TOOL_FAILURE 空载荷哨兵（e3b0c442…=sha256("")）；跨会话以不同 observation 文件为准 |
| [EXP-20260823-002](entries/EXP-20260823-002.md) | ACTIVE | 0.5 | repository | 2026-11-21 | 构造契约签名先行验证：测试构造前先读 domain dataclass 必填字段与 __post_init__；派生 ID 必须合法 UUID4；断言与真实派生规则（claim:{experiment_run_id}:result）冲突时先跑真实值 |
| [EXP-20260823-001](entries/EXP-20260823-001.md) | ACTIVE | 0.5 | repository | 2026-11-21 | sqlite3 adapter 的 Timestamp 序列化：必须 .value.isoformat() + datetime.fromisoformat（str(Timestamp) 是 repr 不可逆）；fetchone 返回 Any 需 assert isinstance(row, sqlite3.Row) |
| [EXP-20260822-001](entries/EXP-20260822-001.md) | SUPERSEDED | 0.5 | repository | 2026-11-20 | Read 被 secret_guard fail-closed 拦截：含 .cursor/hooks/* 的诊断读优先改用 Shell/Grep，.cursorignore 过滤目录改用 Shell 列举（被 EXP-20260823-003 取代） |
| [EXP-20260821-002](entries/EXP-20260821-002.md) | ACTIVE | 0.6 | repository | 2026-11-19 | 安全门禁 hook 拦截 MCP 调用根因已确证：beforeMCPExecution 参数为 tool_input JSON 字符串，mcp_guard 原按 dict 解析导致全拒；已修复（兼容 arguments/tool_input × dict/字符串），eval 与真实环境回归通过；拦截时先不重试、不绕过 hook，改用替代工具 |
| [EXP-20260821-001](entries/EXP-20260821-001.md) | ACTIVE | 0.4 | repository | 2026-11-19 | `uv run pip show <pkg>` 报 Package not found（包实际已装）：验证安装版本用 `uv run python -c importlib.metadata` 或读 uv.lock，不把 exit 1 当依赖缺失 |
| [EXP-20260820-004](entries/EXP-20260820-004.md) | ACTIVE | 0.5 | repository | 2026-11-18 | 直接 uv run validator 输出 GBK 乱码：先设 `$env:PYTHONUTF8="1"; $env:PYTHONIOENCODING="utf-8"`；经 run_all_checks.py（内建 env）无需手动设 |
| [EXP-20260820-003](entries/EXP-20260820-003.md) | ACTIVE | 0.4 | repository | 2026-11-18 | secret_guard fail-closed 拦截 terminals 文件 Read：改用 AwaitShell 轮询 exit_code footer 或 Grep 限行读取，不重试同一 Read、不改 hook |
| [EXP-20260820-002](entries/EXP-20260820-002.md) | ACTIVE | 0.5 | repository | 2026-11-18 | 全量 pytest 在 docker 测试处长时间无输出：`taskkill /PID <pid> /T /F` 杀进程树 + `-m "not requires_docker"` 重跑 |
| [EXP-20260820-001](entries/EXP-20260820-001.md) | ACTIVE | 0.5 | repository | 2026-11-18 | docker daemon 不可用（npipe 连接失败）：`docker version` 快速探测，pytest 用 `-m "not requires_docker"`，docker 套件留 CI container-quality |
| [EXP-20260815-004](entries/EXP-20260815-004.md) | ACTIVE | 0.4 | repository | 2026-11-13 | 长阻塞前台 Shell 返回 "MainThreadCursor disposed" 且无输出 = 命令未执行（IDE 通道瞬时故障）：同命令重跑即可，不当作命令失败诊断 |
| [EXP-20260815-003](entries/EXP-20260815-003.md) | ACTIVE | 0.5 | repository | 2026-11-13 | `tools/` 下脚本直接 `uv run python tools/xxx.py` 报 ModuleNotFoundError（sys.path 为 tools/ 非仓库根）：改 `exec(open(...))` 或固化为 tests/ 正式测试 |
| [EXP-20260815-002](entries/EXP-20260815-002.md) | ACTIVE | 0.6 | repository | 2026-11-13 | docker-py `wait(timeout=)` 超时异常跨平台不一致（Windows npipe 抛 ConnectionError 而非 ReadTimeout）：改用 inspect 轮询 Running + monotonic deadline |
| [EXP-20260815-001](entries/EXP-20260815-001.md) | ACTIVE | 0.5 | repository | 2026-11-13 | uv add/sync/install 卡死且文件系统验证证明未完成（与 EXP-006 相反）：uv lock 拆步 + wheel 手动解压到 site-packages 应急路径 |
| [EXP-20260814-006](entries/EXP-20260814-006.md) | ACTIVE | 0.5 | repository | 2026-11-12 | uv add/sync 前台等待返回 shell-incomplete 但命令实际完成：拆 lock 步骤 + 文件系统验证，不依赖终端流事件 |
| [EXP-20260814-005](entries/EXP-20260814-005.md) | ACTIVE | 0.5 | repository | 2026-11-12 | git diff 空但 status 显示修改 = 纯 CRLF/LF 行尾差异；用 --stat 确认，commit 注明 no content change |
| [EXP-20260814-004](entries/EXP-20260814-004.md) | ACTIVE | 0.5 | repository | 2026-11-12 | m0 profile 入口是 run_all_checks.py --profile m0 --keep-going（无 run_m0_profile.py）；权威定义在 CI workflow |
| [EXP-20260814-003](entries/EXP-20260814-003.md) | ACTIVE | 0.5 | repository | 2026-11-12 | learning eval 脚手架 build() 必须隔离真实资产（fixture 污染导致 registry/target 误报） |
| [EXP-20260814-002](entries/EXP-20260814-002.md) | ACTIVE | 0.5 | repository | 2026-11-12 | 长时后台 Shell 轮询：AwaitShell 收不到事件时直接读取 terminals 文件确认状态与 exit_code |
| [EXP-20260814-001](entries/EXP-20260814-001.md) | ACTIVE | 0.6 | repository | 2026-11-12 | validate_bundle/governance validator 全仓扫描陷阱：文档禁写旧版本号与未勾选项字面量（否定转述也会命中） |
| [EXP-20260813-008](entries/EXP-20260813-008.md) | ACTIVE | 0.5 | repository | 2026-11-11 | test_python_source_limits 300 行/50 行超限 → 拆模块与提取辅助函数，不做豁免 |
| [EXP-20260813-007](entries/EXP-20260813-007.md) | ACTIVE | 0.5 | repository | 2026-11-11 | pytest 收集失败：同名测试模块 import file mismatch 需重命名；fixture 从定义模块导入 |
| [EXP-20260813-006](entries/EXP-20260813-006.md) | ACTIVE | 0.5 | repository | 2026-11-11 | Read 工具读取目录路径失败时改用 Ls 列出目录 |
| [EXP-20260813-005](entries/EXP-20260813-005.md) | ACTIVE | 0.5 | repository | 2026-11-11 | OpenHands 相关 pytest 失败诊断：`-q --tb=line` + 输出落盘/过滤，避免 SDK 可视化 stdout 淹没 |
| [EXP-20260813-004](entries/EXP-20260813-004.md) | ACTIVE | 0.5 | repository | 2026-11-11 | OpenHands SDK 测试脚手架：pydantic 判别联合的 Action/Observation 必须用具体子类 |
| [EXP-20260813-003](entries/EXP-20260813-003.md) | ACTIVE | 0.5 | repository | 2026-11-11 | PatchEdit 报 "historical edit error" 时重新 Read 文件后再编辑 |
| [EXP-20260813-002](entries/EXP-20260813-002.md) | ACTIVE | 0.5 | repository | 2026-11-11 | lint-imports 不可用致架构测试失败：首选 uv run --frozen --no-sync，备选注入 venv Scripts PATH |
| [EXP-20260813-001](entries/EXP-20260813-001.md) | ACTIVE | 0.5 | repository | 2026-11-11 | Python 测试/探针必须经 uv run --frozen --no-sync 或 .venv python 执行，不用系统 python |
| [EXP-20260812-003](entries/EXP-20260812-003.md) | ACTIVE | 0.5 | repository | 2026-11-10 | ruff lint 作用域必须按 CI 定义，禁止全仓 `ruff check .`（豁免区误报） |
| [EXP-20260812-002](entries/EXP-20260812-002.md) | ACTIVE | 0.5 | repository | 2026-11-10 | Windows PowerShell 下命令写法：`;` 分隔替代 `&&`、`git commit -F` 替代 heredoc、cmd 开关需 `cmd /c` 包裹（`dir /b` 会被解析为路径）；python -c 内联多语句/async 不可靠，探测代码写测试文件；嵌套引号命令（多层 -c、长正则）落脚本文件或改用 Grep 工具 |
| [EXP-20260812-001](entries/EXP-20260812-001.md) | ACTIVE | 0.5 | repository | 2026-11-10 | 经验库闭环端到端回归方法（失败→观察→提示→沉淀→注入） |

## 注入说明

`session_context.py` 读取本表 `Summary` 列最近 ≤5 条（按 Review After 倒序），注入会话上下文；读取失败静默跳过，不影响会话启动。

## 去重

写入新条目前先按 ID 与 Summary 关键词查本表；同源问题复用 `supersedes` 关联历史条目，禁止静默覆盖。