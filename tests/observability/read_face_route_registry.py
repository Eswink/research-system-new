"""GOAL-024 EC-02 读面白名单：逐条路由的判定 + 两条纯函数自审（分区 / 命中越界）。

**口径**：读面**契约声明返回内容**的路由是**声明过的载体**（内容出现是业务真相）；
其余路由**必须零命中**。清单**逐条显式**（不存在第三种状态），并且：
理由为空、路径陈旧（不在路由树里）、路径未分类、白名单膨胀（声明面超过上界）
——四条都判红。纯函数在这里，实取与断言在 `test_privacy_read_face_canary.py`。
"""

from __future__ import annotations

from dataclasses import dataclass

DECLARED = "declared_content"
ZERO_HIT = "zero_hit"

_META = "只读元数据(id/状态/时间/digest/计数/枚举),契约不含用户或模型正文"
_CFG = "配置/注册面(端点/模型/工具/策略/角色/模板定义),契约不含任务内容"
_OPS = "运维面(告警/事故/数据健康/调度),契约不含任务内容"
_AGG = "聚合/预算/成本面(数值与货币),契约不含任务内容"
_FRAME = "框架文档路由(OpenAPI schema / Swagger / ReDoc),不含运行内容"
_VACUOUS = "本轮夹具没有该对象 ⇒ 观测到的只是空响应/404,该路由的内容面**未观测**;"


@dataclass(frozen=True, slots=True)
class ReadRouteRule:
    """一条读面路由的判定（`kinds` 非空 = 本轮有正控制）。"""

    path: str
    verdict: str
    note: str
    kinds: tuple[str, ...] = ()


#: 声明返回内容的路由（内容出现是**业务真相**，不是泄漏）。
DECLARED_CONTENT: tuple[ReadRouteRule, ...] = (
    ReadRouteRule(
        "/protocol-drafts/{draft_id}",
        DECLARED,
        "`ProtocolDraftViewDto.yaml_text` = 用户起草的协议正文(契约字段即内容)",
        ("prompt",),
    ),
    ReadRouteRule(
        "/protocol-drafts/{draft_id}/revisions",
        DECLARED,
        "`ProtocolDraftRevisionDto.yaml_text` = 不可变修订正文",
        ("prompt",),
    ),
    ReadRouteRule(
        "/protocol-drafts/{draft_id}/revisions/{revision}",
        DECLARED,
        "同上(单个修订正文)",
        ("prompt",),
    ),
    ReadRouteRule(
        "/artifacts/{artifact_id}/content",
        DECLARED,
        "该路由**就是**制品正文通道(字节即内容)",
        ("artifactbody",),
    ),
    ReadRouteRule(
        "/artifacts/{left_id}/diff/{right_id}",
        DECLARED,
        "制品正文之间的 diff(内容对比,必然含正文)",
        ("artifactbody",),
    ),
    ReadRouteRule(
        "/runs/{run_id}/claims",
        DECLARED,
        "`ClaimDto.statement` = 模型/用户撰写的论断正文",
        ("evidencebody",),
    ),
    ReadRouteRule(
        "/runs/{run_id}/export",
        DECLARED,
        "`ExportBundleDto.claims[].statement`(导出包含论断正文)",
        ("evidencebody",),
    ),
    ReadRouteRule(
        "/runs/{run_id}/lineage",
        DECLARED,
        "**实测**:`LineageNodeDto.text` 取自 claim statement"
        "(GOAL-20261006-031 EC-04 改名:`label`->`text`;值就是正文)",
        ("evidencebody",),
    ),
    ReadRouteRule(
        "/projects/{project_id}/lineage",
        DECLARED,
        "同上(项目级血缘图,`text` 同样取自 claim statement)",
        ("evidencebody",),
    ),
    ReadRouteRule(
        "/protocol-templates",
        DECLARED,
        "`ProtocolDraftTemplateDto.yaml_text` = 模板正文;"
        "模板来自产品内置目录、夹具未把金丝雀写进模板 ⇒ **本轮无正控制**",
    ),
    ReadRouteRule(
        "/protocol-templates/{template_id}",
        DECLARED,
        "同上(单模板正文);本轮无正控制",
    ),
    ReadRouteRule(
        "/projects/{project_id}/memory",
        DECLARED,
        "`MemoryRecordDto.content` = 记忆条目正文;" + _VACUOUS + "本轮 memory store 无条目",
    ),
    ReadRouteRule(
        "/runs/{run_id}/deliverable",
        DECLARED,
        "`DeliverableDto.deliverable` = 交付物 payload(内容);"
        + _VACUOUS
        + "本轮 run 终态 FAILED,available=false",
    ),
    ReadRouteRule(
        "/library/{resource_id}",
        DECLARED,
        "`LibraryResourceDto.description`/`content_ref` = 库条目正文与引用;"
        + _VACUOUS
        + "本轮无库条目",
    ),
    ReadRouteRule(
        "/projects/{project_id}/library",
        DECLARED,
        "库条目列表(条目 DTO 含 description);" + _VACUOUS + "本轮库为空",
    ),
)

#: 必须零命中的路由（逐条理由非空）。
ZERO_HIT_ROUTES: tuple[ReadRouteRule, ...] = (
    ReadRouteRule("/approvals", ZERO_HIT, _META),
    ReadRouteRule(
        "/artifacts/{artifact_id}",
        ZERO_HIT,
        "制品**元数据**(id/digest/size/verified);正文只能走 `/content` —— 列表/详情面不得回内容",
    ),
    ReadRouteRule("/cluster/workers", ZERO_HIT, _META),
    ReadRouteRule("/cost/daily", ZERO_HIT, _AGG),
    ReadRouteRule("/docs", ZERO_HIT, _FRAME),
    ReadRouteRule("/docs/oauth2-redirect", ZERO_HIT, _FRAME),
    ReadRouteRule(
        "/evaluations/trend", ZERO_HIT, _AGG + ";" + _VACUOUS + "本轮该面 503(无评估存储)"
    ),
    ReadRouteRule("/experiment-plans", ZERO_HIT, _META),
    ReadRouteRule("/health", ZERO_HIT, "组成摘要: composition / version / pricing_degraded(布尔)"),
    ReadRouteRule(
        "/llm-endpoints", ZERO_HIT, _CFG + ";凭据只给 configured/missing 状态,不回显明文"
    ),
    ReadRouteRule("/llm-endpoints/{endpoint_id}", ZERO_HIT, _CFG + ";同上"),
    ReadRouteRule("/llm-endpoints/{endpoint_id}/health", ZERO_HIT, _META),
    ReadRouteRule("/models", ZERO_HIT, _CFG),
    ReadRouteRule("/models/{model_id}", ZERO_HIT, _CFG),
    ReadRouteRule("/models/{model_id}/compatibility", ZERO_HIT, _META),
    ReadRouteRule("/notifications", ZERO_HIT, _META),
    ReadRouteRule("/openapi.json", ZERO_HIT, _FRAME),
    ReadRouteRule("/ops/schedules", ZERO_HIT, _OPS),
    ReadRouteRule("/policy/capabilities", ZERO_HIT, _CFG),
    ReadRouteRule("/projects", ZERO_HIT, _META),
    ReadRouteRule("/projects/{project_id}/agents", ZERO_HIT, _CFG),
    ReadRouteRule("/projects/{project_id}/cost-forecast", ZERO_HIT, _AGG),
    ReadRouteRule("/projects/{project_id}/experiment-queue", ZERO_HIT, _META),
    ReadRouteRule("/projects/{project_id}/experiments", ZERO_HIT, _META),
    ReadRouteRule("/projects/{project_id}/ops/alert-rules", ZERO_HIT, _OPS),
    ReadRouteRule("/projects/{project_id}/ops/alerts", ZERO_HIT, _OPS),
    ReadRouteRule("/projects/{project_id}/ops/data-health", ZERO_HIT, _OPS + "(计数)"),
    ReadRouteRule("/projects/{project_id}/ops/incidents", ZERO_HIT, _OPS),
    ReadRouteRule(
        "/projects/{project_id}/protocol-drafts",
        ZERO_HIT,
        "`ProtocolDraftSummaryDto` 明文「草稿列表项(**不含正文**)」 —— 这条是契约断言,不是猜测",
    ),
    ReadRouteRule("/projects/{project_id}/runs", ZERO_HIT, _META + "(run 摘要: id/状态/digest)"),
    ReadRouteRule("/projects/{project_id}/settings", ZERO_HIT, _CFG),
    ReadRouteRule("/redoc", ZERO_HIT, _FRAME),
    ReadRouteRule("/roles", ZERO_HIT, _CFG),
    ReadRouteRule(
        "/runs/{run_id}",
        ZERO_HIT,
        "`RunDetailDto`: digest/状态/派发/重建判词/执行体;冻结正文只有 digest,没有正文本身",
    ),
    ReadRouteRule("/runs/{run_id}/approvals", ZERO_HIT, _META),
    ReadRouteRule(
        "/runs/{run_id}/artifacts",
        ZERO_HIT,
        "制品**列表**只给 id/digest/size/verified;正文必须走 `/content`",
    ),
    ReadRouteRule("/runs/{run_id}/cost", ZERO_HIT, _AGG),
    ReadRouteRule("/runs/{run_id}/cost-forecast", ZERO_HIT, _AGG),
    ReadRouteRule(
        "/runs/{run_id}/events",
        ZERO_HIT,
        "运行事件投影(类型/时间/摘要),不含任务输入与提示词",
    ),
    ReadRouteRule(
        "/runs/{run_id}/evidence",
        ZERO_HIT,
        "`EvidenceDto` 只给 digest/source_ref/来源标签 —— 正文在制品侧,不在这里",
    ),
    ReadRouteRule(
        "/runs/{run_id}/experiments",
        ZERO_HIT,
        _META + "; GOAL-20261008-035 EC-02 起另带**复现审计读数**"
        "(`audit_digest` / `audit_status` / `audit_verified` / `audit_findings`):"
        "digest 与判词按模板只含**制品 id 与锚点名**(ARTIFACT_CORRUPTED 点名制品 id、"
        "CODE_DIGEST_NOT_PINNED 谈快照覆盖面),不含制品正文;"
        "**一等边界**:`message` 是域函数渲染的模板句,新增锚点时须重走本登记",
    ),
    ReadRouteRule("/runs/{run_id}/placement", ZERO_HIT, _META + "(放置/后端/就绪判词)"),
    ReadRouteRule(
        "/runs/{run_id}/reviews",
        ZERO_HIT,
        "`ReviewFindingDto.findings` = 判据名 + **声明派生的**标识符/枚举/计数"
        "(合约声明的制品名、测试名、指标名、policy 决定、覆盖计数),按判据模板不嵌正文;"
        "**一等边界**:`SCHEMA_VALID` 判负时判词含校验器错误文本"
        "(`schema violation: …`),该文本**可能**引用输出片段 —— 故这条面是"
        "「按模板不含正文」而非「结构性保证零正文」(GOAL-035 EC-01 登记;本轮金丝雀未命中该类)",
    ),
    ReadRouteRule(
        "/runs/{run_id}/tasks",
        ZERO_HIT,
        "`TaskDto` 只给 id/契约/代理/状态/尝试次数 —— 任务输入不在这条读面上",
    ),
    ReadRouteRule(
        "/runs/{run_id}/telemetry",
        ZERO_HIT,
        "`RunTelemetryDto` 明文「不含任何 vendor 数据」(只有计数与 digest)",
    ),
    ReadRouteRule("/runs/{run_id}/usage", ZERO_HIT, _AGG),
    ReadRouteRule(
        "/runs/{run_id}/workspace-snapshots",
        ZERO_HIT,
        _META + "(快照摘要);" + _VACUOUS + "本轮无快照",
    ),
    ReadRouteRule("/team-templates", ZERO_HIT, _CFG),
    ReadRouteRule("/tool-packs", ZERO_HIT, _CFG),
    ReadRouteRule("/tool-provider-registrations", ZERO_HIT, _CFG),
    ReadRouteRule("/tool-providers", ZERO_HIT, _CFG),
    ReadRouteRule("/workspace-snapshots", ZERO_HIT, _META),
    ReadRouteRule(
        "/workspace-snapshots/{digest}/files",
        ZERO_HIT,
        "文件树只给 path/size/sha256;" + _VACUOUS + "本轮无快照",
    ),
    ReadRouteRule(
        "/workspace-snapshots/{left}/diff/{right}",
        ZERO_HIT,
        "变更只给 path/kind;" + _VACUOUS + "本轮无快照",
    ),
)

#: 本轮**无法实取**的零命中路由（缺对象 id ⇒ 连空响应都取不到;逐条点名,不许静默跳过）。
UNEXERCISED_ZERO_HIT: tuple[str, ...] = (
    "/workspace-snapshots/{digest}/files",
    "/workspace-snapshots/{left}/diff/{right}",
)

#: 本轮**无法实取**的声明载体（缺对象 id;逐条点名）。
UNEXERCISED_DECLARED: tuple[str, ...] = ("/library/{resource_id}",)

#: 白名单**上界**：声明面不许膨胀（否则把任何路由标成"声明内容"就能全绿）。
MAX_DECLARED = 15
#: 零命中面**下界**：受判路由数量不许收缩。
MIN_ZERO_HIT = 45
#: 零命中面里**实取到非空响应**的路由下界（防空转绿）。
MIN_EXERCISED = 40


def all_rules() -> tuple[ReadRouteRule, ...]:
    return DECLARED_CONTENT + ZERO_HIT_ROUTES


def _rule_findings(rule: ReadRouteRule, seen: set[str]) -> list[str]:
    """单条登记的自审（理由 / 重复 / 未知判定）。"""
    findings: list[str] = []
    if not rule.note.strip():
        findings.append(f"理由为空:{rule.path}")
    if rule.path in seen:
        findings.append(f"重复分类:{rule.path}")
    seen.add(rule.path)
    if rule.verdict not in (DECLARED, ZERO_HIT):
        findings.append(f"未知判定:{rule.path}={rule.verdict}")
    return findings


def _bound_findings() -> list[str]:
    """上下界：声明面不许膨胀，零命中面不许收缩。"""
    findings: list[str] = []
    if len(DECLARED_CONTENT) > MAX_DECLARED:
        findings.append(f"声明面超过上界:{len(DECLARED_CONTENT)} > {MAX_DECLARED}")
    if len(ZERO_HIT_ROUTES) < MIN_ZERO_HIT:
        findings.append(f"零命中面低于下界:{len(ZERO_HIT_ROUTES)} < {MIN_ZERO_HIT}")
    return findings


def partition_findings(paths: tuple[str, ...]) -> list[str]:
    """分区自审：未分类 / 重复 / 陈旧 / 空理由 / 面上下界。"""
    findings: list[str] = []
    seen: set[str] = set()
    for rule in all_rules():
        findings.extend(_rule_findings(rule, seen))
    known = {rule.path for rule in all_rules()}
    findings.extend(f"未分类的读面路由:{path}" for path in paths if path not in known)
    findings.extend(f"陈旧登记(路由树里没有):{path}" for path in sorted(known - set(paths)))
    findings.extend(_bound_findings())
    return findings


def verify_route(route: ReadRouteRule, kinds: list[str]) -> list[str]:
    """单路由核验（纯函数）：声明载体必须有它声明的内容;零命中面必须一个都不许有。"""
    if route.verdict == ZERO_HIT:
        return [f"零命中路由出现金丝雀:{route.path} 命中 {kinds}"] if kinds else []
    missing = sorted(set(route.kinds) - set(kinds))
    return [f"声明载体没看到它声明的内容:{route.path} 缺 {missing}"] if missing else []
