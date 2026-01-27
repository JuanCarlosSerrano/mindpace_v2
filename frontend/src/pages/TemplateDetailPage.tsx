import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getTemplateDetail } from "../api/templates";
import type { TemplatePreview } from "../api/types";

export default function TemplateDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [template, setTemplate] = useState<TemplatePreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      const parsed = Number(id);
      if (Number.isNaN(parsed)) {
        setError("Plantilla inválida");
        navigate("/templates", { replace: true });
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const data = await getTemplateDetail(parsed);
        setTemplate(data);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setError("Plantilla no encontrada");
        } else {
          setError("Error al cargar la plantilla");
        }
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [id]);

  return (
    <div className="page">
      <header className="hero">
        <div className="section-header">
          <div>
            <h1>Detalle de plantilla</h1>
            <p>Resumen de enfoque semanal y detalles clave.</p>
          </div>
          <Link className="button-link ghost" to="/templates">
            ← Volver
          </Link>
        </div>
      </header>

      <section className="layout-grid">
        <div className="panel">
        {loading && <p className="muted">Cargando…</p>}
        {error && <div className="error">{error}</div>}

        {template && (
          <div className="template-detail">
            <div className="template-detail__header">
              <div>
                <h2>{template.name}</h2>
                <p className="muted">{template.description}</p>
              </div>
              <span className="pill info">{template.level ?? "nivel"}</span>
            </div>
            <div className="template-card__meta">
              <span>{template.duration_weeks} semanas</span>
              <span>{template.estimated_weekly_load} carga/sem</span>
              <span>{template.goal}</span>
            </div>
            <div className="tag-row">
              {template.tags.map((tag) => (
                <span key={`detail-${tag}`} className="tag-pill">
                  {tag}
                </span>
              ))}
            </div>

            <div className="preview-table">
              <div className="preview-row preview-head">
                <span>Semana</span>
                <span>Carga estimada</span>
                <span>Foco</span>
              </div>
              {template.weekly_preview.map((week) => (
                <div key={week.week} className="preview-row">
                  <span>W{week.week}</span>
                  <span>{week.load}</span>
                  <span>{week.focus_tags.join(", ") || "-"}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        </div>

        {template && (
          <aside className="panel sidebar-panel">
            <h2>Resumen rápido</h2>
            <div className="stat-card">
              <span className="stat-label">Duración</span>
              <span className="stat-value">{template.duration_weeks} semanas</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Carga semanal</span>
              <span className="stat-value">
                {template.estimated_weekly_load ?? "-"}
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Objetivo</span>
              <span className="stat-value">{template.goal ?? "-"}</span>
            </div>
          </aside>
        )}
      </section>
    </div>
  );
}
