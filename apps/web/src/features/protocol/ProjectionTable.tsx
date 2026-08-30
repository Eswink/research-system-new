import type { AgentSpecDto, DryRunProjectionDto } from "../../api/types";

const agentModel = (projection: DryRunProjectionDto, agent: AgentSpecDto): string => {
  return projection.agent_models[agent.id] ?? agent.model_binding.value ?? "inherit";
};

export function ProjectionTable({
  projection,
  agents,
}: {
  projection: DryRunProjectionDto;
  agents: AgentSpecDto[];
}) {
  const costMinor = projection.estimated_cost_minor ?? null;
  const costText =
    costMinor === null
      ? "not estimated"
      : [
          String(costMinor),
          projection.estimated_cost_currency ?? "currency unavailable",
          "minor units",
        ].join(" ");
  return (
    <div data-testid="dry-run-projection">
      <h3>Projected Team</h3>
      <table>
        <thead>
          <tr>
            <th>Agent</th>
            <th>Role</th>
            <th>Model</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((agent) => (
            <tr key={agent.id}>
              <td>{agent.id}</td>
              <td>{agent.role}</td>
              <td>{agentModel(projection, agent)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Resources</h3>
      <p data-testid="dry-run-cost">Estimated cost: {costText}</p>
      <p>Approval actions: {projection.approval_actions.join("; ") || "none"}</p>
      <p>Budget reservations: {String(projection.budget_reservations.length)}</p>
    </div>
  );
}