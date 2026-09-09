// Pure helpers for tools/dev_backend.mjs — extracted so node:test can cover
// them without spawning docker/uv. No IO, no process access.

// Parse a .env-style file body into {key: value}; skips comments/blank lines,
// strips matching surrounding quotes, later keys win.
export function parseDotEnv(body) {
  const out = {};
  for (const line of body.split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (!match) continue;
    let value = match[2].trim();
    if (
      (value.startsWith('"') && value.endsWith('"') && value.length >= 2) ||
      (value.startsWith("'") && value.endsWith("'") && value.length >= 2)
    ) {
      value = value.slice(1, -1);
    }
    out[match[1]] = value;
  }
  return out;
}

// Extract {host, port} from a postgres DSN; null when the shape is not
// postgresql://user@host[:port]. The `[^@]*` authority tolerates passwords
// containing ':'; host/port are anchored after the LAST '@' so such passwords
// cannot be mistaken for the port separator. No-credential DSNs return null —
// the host/port would be ambiguous and the caller must fail with guidance.
export function parseDsnEndpoint(dsn) {
  if (typeof dsn !== "string") return null;
  const match = dsn.match(/^(?:postgres|postgresql):\/\/[^@]*@([^:/]+)(?::(\d+))?/);
  if (!match) return null;
  return { host: match[1], port: match[2] ? Number(match[2]) : 5432 };
}

// Gateway bind defaults from env (worker_gateway/__main__.py semantics).
export function gatewayBind(env) {
  return {
    host: env.RESEARCHOS_WORKER_GATEWAY_HOST || "127.0.0.1",
    port: env.RESEARCHOS_WORKER_GATEWAY_PORT || "8081",
  };
}

// Apply .env values only for keys the host environment has not set —
// host env is authoritative (same precedence as `set -a; . ./.env`).
export function mergeEnv(hostEnv, dotenv) {
  const out = { ...hostEnv };
  for (const [key, value] of Object.entries(dotenv)) {
    if (out[key] === undefined) out[key] = value;
  }
  return out;
}
