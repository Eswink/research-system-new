# Research OS · Control Plane

一套完整的科研平台控制面板 UI 原型(React + Babel Standalone,纯静态 HTML 交付)。

## 交付内容

### 顶层 HTML 入口
- **App.html** — 主应用入口(完整应用外壳 AppShell,包含全部子屏幕)
- **Overview.html** — 概览视图(独立页)
- **Command Center.html** — 指挥中心视图(独立页)

> 推荐先打开 `App.html`。它加载全部屏幕组件,支持左侧导航切换。

### 目录结构
```
├── App.html                    主入口(推荐)
├── Overview.html               概览独立页
├── Command Center.html         指挥中心独立页
├── styles/
│   └── tokens.css              设计令牌(颜色 / 间距 / 字号)
├── components/
│   ├── AppShell.jsx            应用外壳(导航 + 路由)
│   ├── atoms.jsx               基础原子组件
│   ├── charts.jsx              图表组件
│   ├── patterns.jsx            复合模式组件
│   ├── i18n.jsx                国际化(zh-CN / en)
│   └── LoadingOverlay.jsx      加载状态
├── screens/                    30+ 业务屏幕(Projects / Experiments / Datasets / …)
├── data/
│   ├── fixtures.js             基础模拟数据
│   └── fixtures_ext.js         扩展模拟数据
├── tweaks_panel.jsx            设计调参面板
└── design_handoff_protocol_visual_editor/
                                协议可视化编辑器交付子包(含 README)
```

## 本地运行

因为使用了 `<script type="text/babel">` 就地转译,必须通过 HTTP 服务打开(不能双击 `file://` 打开)。

任选一种方式在项目根目录启动:

```bash
# Python 3
python3 -m http.server 8080

# Node
npx serve .

# 或用 VSCode 的 Live Server 插件
```

然后浏览器访问:`http://localhost:8080/App.html`

## 技术栈
- **React 18.3.1** + **ReactDOM 18.3.1**(UMD 开发版,CDN)
- **@babel/standalone 7.29.0**(浏览器端 JSX 转译)
- **Google Fonts**: IBM Plex Sans / JetBrains Mono
- 纯静态 —— 无构建、无 Node 依赖

## 主题 & 语言
- 主题:`<html data-theme="dark|light">` 切换(默认 dark)
- 密度:`<html data-density="compact|normal|comfortable">`
- 语言:内置 `I18nProvider`,支持中英切换(见 `components/i18n.jsx`)

## 已知说明
- 首次加载需下载 CDN 的 React / Babel(约 400KB),建议保持网络畅通
- 所有数据均为 fixtures 模拟数据,可直接对接后端 API 替换 `data/*.js`
- 生产环境建议将 JSX 预编译并去掉 `@babel/standalone`
