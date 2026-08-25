export function ModelsStep({
  busy,
  error,
  onProbe,
}: {
  busy: boolean;
  error: string | null;
  onProbe: () => void;
}) {
  return (
    <div data-testid="wizard-models-step">
      <p>Models on endpoint: （在 Models 页添加 / 或点击 Probe First Model）</p>
      {error !== null && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button type="button" onClick={onProbe} disabled={busy}>
        {busy ? "Probing…" : "Probe First Model"}
      </button>
    </div>
  );
}