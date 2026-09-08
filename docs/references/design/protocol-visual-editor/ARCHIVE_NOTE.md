# 设计参考归档：Protocol Visual Editor（协议可视化编辑器）

- 来源：`C:/Users/googl/Desktop/design_handoff_protocol_visual_editor/`（用户交付的设计包，2026-09-08 归档）。
- 性质：**设计参考，非产品契约**。包内 README 明确说明这是 HTML/Babel-standalone 原型，
  应在目标代码库中"重建"而非直接 lift 代码。
- 授权计划：[PLAN-20260908-033](../../../../.cursor/plans/tasks/PLAN-20260908-033-research-console-rebuild.md)
  （Cursor Plan：`.cursor/plans/research_console_全站重建_9c821507.plan.md`）。

## 内容清单

| 文件 | 内容 |
| --- | --- |
| `README.md` | 设计交付说明（583 行）：视图结构、7 个 Form 区块、校验规则表、令牌引用、 recrecation checklist |
| `source/styles/tokens.css` | 设计令牌（dark 默认 + light 主题 + density + 基础样式/按钮/chip/row） |
| `source/screens/DryRun.jsx` | 双栏布局：左编辑器 + 右 Preflight 报告（状态条 + 5 个 zone） |
| `source/screens/ProtocolEditor.jsx` | 编辑器主状态、validate()、serialize()（演示级） |
| `source/screens/ProtocolEditor.parts.jsx` | Chrome/横幅/区块导航/Action bar/模板选择/YAML 视图/Field 原语 |
| `source/screens/ProtocolEditor.sections.jsx` | 7 个区块表单 + ChipMultiSelect/TemperatureGrid/BudgetDonut/SegmentedField |
| `screens/*.jpg` | 5 张设计截图（manifest/evaluation/budget/gates/policy） |

## 明确不进入生产的部分（设计稿 → 真实契约裁决）

| 设计稿概念 | 处置 | 真实契约 |
| --- | --- | --- |
| `protocol_version: 1.4`（锁定展示） | 不采用 | 工程版本只来自根 `VERSION`；协议版本由 `protocol.schema.json` 的 `version` 字段约束 |
| `manifest.id`（运行时分配） | 改为只读展示真实 `protocol.id` | schema 要求 `^[a-z0-9]+(?:_[a-z0-9]+)*_v[0-9]+_[0-9]+_[0-9]+$` |
| `objectives` / `evaluation` / `budget.cap_minor` / `policy` 等区块 | **不作为协议字段**（schema `additionalProperties: false` 会拒绝） | Form 区块重建为真实字段：`id/version/phases（strategy/depends_on/roles/capabilities/task_contract/gate/stop_conditions/timeout）`；budget/policy 改为只读投影 |
| 金额 `minor = USD × 100000` | 不采用 | 金额与展示以服务端 DTO 为准；未知显示 UNKNOWN |
| 演示管理员开关（Tweaks `protocolAdminMode`） | 不采用 | 无演示开关；policy 展示为服务端只读投影 |
| `errorLevel` 注入假错误、固定摘要 `37b2c9…`、固定 preflight 数据 | 不采用 | 校验来自服务端 compile/preflight；digest 来自真实响应 |
| Google Fonts CDN / Babel standalone | 不采用 | 本地字体回退栈；保持现有 CSP |
| YAML serialize 字符串拼接 | 不采用 | 文档语法树 YAML 库，保留注释与格式 |
| `ETHICS_GATE` 枚举 | 不采用 | schema gate 枚举：POLICY/BUDGET/QUALITY/HUMAN/SECURITY/PUBLISH_GATE |

## 设计资产复用范围

- 视觉令牌（颜色/间距/圆角/阴影/motion/focus ring）**逐值复用**。
- 交互结构复用：Chrome 工具条、DIRTY 徽章、错误横幅（可展开跳转）、区块导航
  （错误计数徽章）、sticky Action bar（Discard/Apply + 状态语义）、模板下拉、
  双模式切换、Field/Tooltip/SectionHeader 原语、双栏 Preflight 报告（6 信息区）。
- 状态四重编码原则（形状+图标+文字+颜色）全站沿用。
