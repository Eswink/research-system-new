import type { LlmEndpointReadDto } from "../../api/types";

export function EndpointsHome({
  endpoints,
  onAddRelay,
}: {
  endpoints: LlmEndpointReadDto[];
  onAddRelay: () => void;
}) {
  return (
    <section>
      <h2>Configured Endpoints</h2>
      {endpoints.map((endpoint) => (
        <article key={endpoint.id} data-testid="endpoint-card">
          <h3>{endpoint.name}</h3>
          <p>{endpoint.base_url}</p>
          <p>
            credential: <strong>{endpoint.credential}</strong> · api_style:{" "}
            {endpoint.api_style}
          </p>
        </article>
      ))}
      <button type="button" onClick={onAddRelay}>
        Add Relay
      </button>
    </section>
  );
}