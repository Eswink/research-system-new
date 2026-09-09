/** Wizard 步骤类型（独立模块避免 useWizardFlow ↔ useWizardActions 循环）。 */
export type WizardStep = "relay" | "test" | "models" | "done";
