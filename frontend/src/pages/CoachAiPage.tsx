import { useState } from "react";
import { ApiError } from "../api/client";
import { applyCoach, revertCoach } from "../api/coach";

type CoachResult = {
  label: string;
  payload: unknown;
};

export default function CoachAiPage() {
  const [planId, setPlanId] = useState(2);
  const [isoWeek, setIsoWeek] = useState("2026-W03");
  const [revertLast, setRevertLast] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CoachResult | null>(null);
  const [showJson, setShowJson] = useState(false);

  const handleError = (err: unknown) => {
    if (err instanceof ApiError) {
      setError(`${err.message}`);
      return;
    }
    setError("Error desconocido");
  };

  const handleDryRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await applyCoach(planId, { week: isoWeek, dry_run: true });
      setResult({ label: "Dry-run completado", payload: data });
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await applyCoach(planId, { week: isoWeek, dry_run: false });
      setResult({ label: "Ajustes aplicados", payload: data });
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRevert = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await revertCoach(planId, { last: revertLast });
      setResult({ label: "Reversión completada", payload: data });
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="section-header">
          <div>
            <h1>CoachAI · Utilidades</h1>
            <p>Ejecuta, revisa y revierte ajustes de forma controlada.</p>
          </div>
          <button
            className="ghost"
            onClick={() => setShowJson((prev) => !prev)}
          >
            {showJson ? "Ocultar JSON" : "Mostrar JSON"}
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="layout-grid">
        <div className="panel">
          <div className="section-header">
            <h2>Parámetros</h2>
            <p>Selecciona plan y semana a analizar.</p>
          </div>
          <div className="controls-grid">
            <div>
              <label>Plan ID</label>
              <input
                type="number"
                min={1}
                value={planId}
                onChange={(e) => setPlanId(Number(e.target.value))}
              />
            </div>
            <div>
              <label>ISO Week</label>
              <input
                value={isoWeek}
                onChange={(e) => setIsoWeek(e.target.value)}
              />
            </div>
            <div>
              <label>Revertir últimos</label>
              <input
                type="number"
                min={1}
                value={revertLast}
                onChange={(e) => setRevertLast(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="button-row">
            <button disabled={loading} onClick={handleDryRun}>
              Dry-run
            </button>
            <button disabled={loading} className="secondary" onClick={handleApply}>
              Aplicar
            </button>
            <button disabled={loading} className="ghost" onClick={handleRevert}>
              Revertir
            </button>
          </div>
        </div>

        <aside className="panel sidebar-panel">
          <div className="section-header">
            <h2>Resultado</h2>
            <p>{result?.label ?? "Sin acciones ejecutadas."}</p>
          </div>
          {result ? (
            <div className="panel nested-panel">
              <strong>{result.label}</strong>
              {showJson && (
                <pre className="json">{JSON.stringify(result.payload, null, 2)}</pre>
              )}
              {!showJson && (
                <p className="muted">
                  Activa el JSON para revisar el detalle de la ejecución.
                </p>
              )}
            </div>
          ) : (
            <p className="muted">Ejecuta una acción para ver el resultado.</p>
          )}
        </aside>
      </section>
    </div>
  );
}
