import { Chip } from "../../components/Chip";

/** 启用态 chip（独立模块：避免列定义与面板互相 import 形成环）。 */
export function EnabledChip({ enabled }: { enabled: boolean }) {
  return <Chip tone={enabled ? "accent" : "warn"}>{enabled ? "ON" : "OFF"}</Chip>;
}
