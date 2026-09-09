# console-design 设计来源归档（PLAN-20260908-034 T01）

## 原始来源

- 交付包路径：`C:\Users\googl\Desktop\project`（用户提供的完整设计交付包）。
- 归档时间：2026-09-08。
- 全部源文件逐字节复制于本目录（`components/`、`screens/`、`styles/`、`data/`、
  `tweaks_panel.jsx`、`App.html`、`Overview.html`、`Command Center.html`、
  `SOURCE_README.md`）。
- 文件摘要：`source-digests.txt`（SHA-256，对原始交付包计算）。
- 本归档只作视觉依据与参考预览，**不进入产品构建**；产品代码不 import 本目录。

## 入口关系

- `App.html`：主入口。加载顺序 data/fixtures → atoms/charts/patterns/i18n/
  LoadingOverlay/tweaks_panel → 30 个 screens → AppShell.jsx → boot。
  协议编辑器加载顺序有硬约束：`ProtocolEditor.jsx`（常量与主组件）→
  `.parts.jsx` → `.sections.jsx` → `DryRun.jsx`。
- `Command Center.html`：独立 2560×1440 大屏设计，单独实现（路由 `#/command-center`）。
- `Overview.html`：设计画板总览，仍含旧五域说明与旧入口
  （`App.html?_screen=assets/endpoints`、`states/matrix` 等），仅作辅助材料，
  不替代 AppShell.jsx 的八域导航，也不增加重复产品页面。

## 子包差异核对

`design_handoff_protocol_visual_editor/source/` 与顶层同名文件逐一 `cmp` 比较：

| 文件 | 结果 |
| --- | --- |
| screens/ProtocolEditor.jsx | IDENTICAL |
| screens/ProtocolEditor.parts.jsx | IDENTICAL |
| screens/ProtocolEditor.sections.jsx | IDENTICAL |
| screens/DryRun.jsx | IDENTICAL |
| styles/tokens.css | IDENTICAL |

重复只登记一次；子包副本保留于 `subpackage_protocol_visual_editor/` 备查。
子包 `README.md`（协议编辑器交付说明）与 `screens/*.jpg`（5 张区块参考照）一并归档。

## 参考预览（依赖已 pin）

`preview/` 为可离线复现的参考预览：

- `pin-deps.mjs` 下载并校验 CDN 依赖后重写 HTML 引用：
  - React 18.3.1 UMD dev — `sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L`
  - ReactDOM 18.3.1 UMD dev — `sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm`
  - @babel/standalone 7.29.0 — `sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y`
  - Google Fonts IBM Plex Sans(300/400/500/600) + JetBrains Mono(400/500/600)
    woff2 共 12 个，本地化于 `preview/fonts/`（文件名含内容摘要）。
- 复现：`node pin-deps.mjs`（幂等，digest 匹配即跳过）。
- 预览页状态经 localStorage 种子控制：`ros.domain`、`ros.tab`、`ros.lang`；
  主题/密度为 React 初始值（dark/normal），截图时经 `data-theme`/`data-density`
  属性切换。

## 逐页参考图

`reference/` 由 `preview/capture-reference.mjs` 生成（Playwright，1440×900；
Command Center 2560×1440）：

- 主图集：31 个设计页 + command-center，dark × normal × zh-CN。
- 高风险页（plan-protocol、library-endpoints、run-timeline、run-approvals、
  evidence-claims、insights-cost-analytics）另采双主题×双密度×中英文完整 8 组合。
- 复现：`node capture-reference.mjs`（依赖 apps/web 的 @playwright/test）。
- 这些图是**设计对照基准**；实现回归截图基线须待视觉对照通过后另行批准，
  两者不混用。

## 已知设计侧限制（实施时按契约调整并记录差异）

- 原型数据全部来自 `data/fixtures.js` / `fixtures_ext.js` 模拟数据。
- 协议编辑器原型字段（`manifest/objectives/evaluation/budget/policy`、
  `protocol_version 1.4`）与仓库 `schemas/protocol.schema.json` 真实顶层
  （`id/version/phases`）不一致——以仓库 Schema 为准。
- Tweaks 面板、演示管理员开关、`window.open("Command Center.html")` 外链、
  Google Fonts CDN 引用不进入产品。
- 密度：README 提及 comfortable，但 tokens.css 只实现 compact/normal——
  产品保持 normal/compact 两档。
