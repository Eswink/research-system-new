# Console 自托管字体来源与许可证（PLAN-20260908-034 T04）

生产不加载 Google Fonts / CDN。控制台所需两个字体族已固定来源、版本、许可证与
内容摘要，自托管于 `apps/web/public/fonts/`（CSS 见 `apps/web/src/styles/fonts.css`，
由参考预览 `docs/references/design/console-design/preview/fonts/` 同一批文件复制）。

## 字体族

| 家族 | 字重 | 许可证 | 上游 |
| --- | --- | --- | --- |
| IBM Plex Sans | 300/400/500/600 | SIL Open Font License 1.1 | IBM（google/fonts 仓库收录） |
| JetBrains Mono | 400/500/600 | SIL Open Font License 1.1 | JetBrains（google/fonts 仓库收录） |

两者均为 OFL-1.1，允许自托管与再分发（保留许可证）。

## 获取方式与固定

- 来源：Google Fonts css2 API，请求参数
  `family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap`，
  现代浏览器 UA（确保 woff2 格式）。
- 下载与本地化脚本：`docs/references/design/console-design/preview/pin-deps.mjs`
  （幂等；文件名即内容 sha256 摘要前 16 位，`+`/`/` 替换为 `_`）。
- 逐文件 sha256 摘要（Git Bash 于 `apps/web/public/fonts/` 计算）：

```text
d160e20920ae4d6556518d352d3af27a74e9b0de3d8fe17b1c1044fc75aa2f81  0WDiCSCuTWVWUY01.woff2
db5ff4db83e580426280e9337a58dc57d3a83784a1b03ad80914651594441d52  21_024PlgEJigOkz.woff2
e17cfd15fb96909d64095015f958207063a0c07191da3512df7d560a781aebdf  4Xz9FfuWkJ1kCVAV.woff2
e2291e842cf5af167122a22881a740c7f2dda7716f1e8cd76680264f4a859470  4ikehCz1rxZxIqIo.woff2
f598dd0700f155e2facfaa8ecfacace397d4c2c153e9ce37ab7ad310e8505bc2  9ZjdBwDxVeL6z6qO.woff2
0a557721b1f8b36d3f3f84442689a71ca4a744300abcb46a1953f51bfc663b66  ClV3IbH4s20_P4RE.woff2
62213be8a78b42f1e29d1452d91e2f8b3e745572a9dd98d3941e39fa00b37d76  YiE76KeLQvHinRRS.woff2
73e7f7b1c980416ae0c2461268b14c7cfcce0668e683dc43fbb11a82a227b9f2  c_f3scmAQWrgwkYS.woff2
7d0037a170882a49e65a45c38ef195237bb07b1cc791d078379f0ac0d7ae1935  fQA3oXCIKknmWkXD.woff2
83c005d49d8a6a50474c73a5a36ac0468076e9c4a29da7bdb14995d80560a5be  g8AF1J2KalBHTHOl.woff2
9409ee21811f0f5272b7e1d828fe8838005b0573481ef906e7e55b63f6610ab0  lAnuIYEfD1Jyt_HY.woff2
c89b9cc0bc6262bd4f8d8494b6961601f3aefa829d08c2e3635f4d501d3a47c2  yJucwLxiYr1PjYSU.woff2
```

- 校验方法：对 `apps/web/public/fonts/` 全部 woff2 计算 sha256 与上表比对；
  文件名即摘要前缀，任何内容漂移都会使 `fonts.css` 的引用失效。
- 中文字符（PingFang SC / Microsoft YaHei）走系统回退栈，不分发 CJK 字体。

## 变更纪律

新增/更新字体必须先核对此处来源、许可证、确切版本与摘要，再更新
`public/fonts/`、`src/styles/fonts.css` 与本文件；禁止浮动 CDN 引用。
