/**
 * Example chrome data bridge（PLAN-040 WP-C fixture 隔离）。
 *
 * 共享 shell（TopBar/Sidebar）在 `source === "example"` 分支需要示例展示值。
 * fixture 业务 JSON 的读取集中于此（example-console 树内）；live 布局只引用本
 * 模块导出的展示常量，不再直接 import `data/*.json`。架构边界测试
 * （production-boundaries）强制 `example-console/data/` 只能被 example-console
 * 树内模块 import——防止新的业务 fixture 泄漏进 live 壳层。
 */

import exampleRun from "./data/run.json";
import workspaces from "./data/workspaces.json";

/** example 模式顶栏展示的 run id（纯展示，非业务状态）。 */
export const EXAMPLE_RUN_ID: string = exampleRun.id;

/** example 模式 workspace 切换器展示列表（类型保持 JSON 推断形）。 */
export const EXAMPLE_WORKSPACES = workspaces;
