/** e2e API 替身的样例 fixture 常量（从 stub-api.ts 拆出）。 */

export type Handler = (url: URL, body: unknown) => { status: number; body: unknown };

export const VALID_YAML = [
  "id: sort_analysis_v1_0_1",
  "version: 0.4.0",
  "phases:",
  "  - id: execution",
  "    strategy: single_agent",
  "    required_roles:",
  "      - {role: experiment_engineer, min_instances: 1, max_instances: 1}",
  "    task_contract: sort_analysis_execution",
  "    timeout_seconds: 120",
].join("\n");

export const ENDPOINT = {
  id: "ep-1",
  name: "main",
  protocol: "OPENAI_COMPATIBLE",
  base_url: "https://relay.example",
  api_style: "chat_completions",
  enabled: true,
  credential: "configured",
  request_timeout_seconds: 30,
  max_retries: 3,
  concurrency_limit: 4,
  version: "1",
};

export const DRAFT = {
  draft_id: "pdraft_00000001",
  project_id: "example-project",
  name: "draft",
  revision: 1,
  yaml_text: VALID_YAML,
  source_digest: "sha256:aaaaaaaa",
  created_at: "2026-09-08T00:00:00Z",
  updated_at: "2026-09-08T00:00:00Z",
};
