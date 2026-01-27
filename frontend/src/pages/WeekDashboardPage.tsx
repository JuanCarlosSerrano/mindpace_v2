import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { getWeekSummary } from "../api/dashboard";
import { postFeedback } from "../api/feedback";
import { Link } from "react-router-dom";
import type { PlanSessionDetail, WeeklySummary } from "../api/types";
import ActionsHistory from "../components/ActionsHistory";
import AlertsPanel from "../components/AlertsPanel";
import FeedbackForm from "../components/FeedbackForm";
import PlanSessionsList from "../components/PlanSessionsList";
import RecommendationsList from "../components/RecommendationsList";
import WeekPicker from "../components/WeekPicker";

const GROUPS = [
  {
    id: 1,
    name: "Grupo Alpha",
    athletes: [
      { id: 1, name: "Atleta 1" },
      { id: 2, name: "Atleta 2" },
      { id: 3, name: "Atleta 3" },
    ],
  },
  {
    id: 2,
    name: "Grupo Tempo",
    athletes: [
      { id: 4, name: "Atleta 4" },
      { id: 5, name: "Atleta 5" },
    ],
  },
];

const formatValue = (value: number | string | null | undefined, suffix = "") =>
  value === null || value === undefined || value === ""
    ? "-"
    : `${value}${suffix}`;

const getUpcomingSessions = (sessions: PlanSessionDetail[] | undefined) => {
  if (!sessions) return [];
  const today = new Date();
  return sessions
    .map((session) => ({ ...session, dateObj: new Date(session.date) }))
    .filter((session) => !Number.isNaN(session.dateObj.getTime()))
    .filter((session) => session.dateObj >= today)
    .sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime())
    .slice(0, 5);
};

export default function WeekDashboardPage() {
  const [groupId, setGroupId] = useState(1);
  const [planId, setPlanId] = useState(2);
  const [athleteId, setAthleteId] = useState(1);
  const [isoWeek, setIsoWeek] = useState("2026-W03");
  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const selectedGroup = useMemo(
    () => GROUPS.find((group) => group.id === groupId) ?? GROUPS[0],
    [groupId]
  );
  const upcomingSessions = useMemo(
    () => getUpcomingSessions(summary?.plan.sessions_detail),
    [summary]
  );
  const alertItems = useMemo(() => {
    if (!summary) return [];
    return [...summary.alerts.plan, ...summary.alerts.real_risk];
  }, [summary]);
  const pendingFeedback = useMemo(() => {
    if (!summary) return null;
    const planned = summary.plan.sessions_count ?? 0;
    const feedback = summary.feedback.count ?? 0;
    return Math.max(0, planned - feedback);
  }, [summary]);
  const athleteRows = selectedGroup?.athletes ?? [];

  useEffect(() => {
    if (!selectedGroup) return;
    const hasAthlete = selectedGroup.athletes.some(
      (athlete) => athlete.id === athleteId
    );
    if (!hasAthlete && selectedGroup.athletes[0]) {
      setAthleteId(selectedGroup.athletes[0].id);
    }
  }, [selectedGroup, athleteId]);

  const handleError = (err: unknown) => {
    if (err instanceof ApiError) {
      if (err.status === 400) {
        const maxWeek =
          typeof err.details === "object" &&
          err.details &&
          "detail" in err.details &&
          typeof (err.details as { detail?: { max_week?: number } }).detail
            ?.max_week === "number"
            ? (err.details as { detail: { max_week: number } }).detail.max_week
            : undefined;
        setError(
          maxWeek ? `Semana inválida (máx ${maxWeek})` : "Semana inválida"
        );
        return;
      }
      if (err.status === 404) {
        setError("No hay datos para esa semana");
        return;
      }
      if (err.status === 500) {
        setError("Error interno (avisa al entrenador 😅)");
        return;
      }
      setError(`${err.message}: ${JSON.stringify(err.details)}`);
      return;
    }
    setError("Error desconocido");
  };

  const loadWeek = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getWeekSummary(planId, isoWeek);
      setSummary(data);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (payload: {
    date: string;
    rpe?: number;
    fatigue?: number;
    soreness?: number;
    pain?: boolean;
    notes?: string;
    plan_id?: number;
  }) => {
    setLoading(true);
    setError(null);
    try {
      await postFeedback(athleteId, payload);
      await loadWeek();
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page dashboard">
      <header className="dashboard-hero">
        <div>
          <span className="eyebrow">Entrenador</span>
          <h1>Control semanal · {isoWeek}</h1>
          <p>
            Vista táctica del plan, cumplimiento y acciones del CoachAI para tu
            grupo activo.
          </p>
          <div className="hero-meta">
            <span>{selectedGroup?.name ?? "Grupo activo"}</span>
            <span>Plan activo #{planId}</span>
            <span>Atleta foco #{athleteId}</span>
            <span>
              Datos {summary?.meta.data_confidence_ratio ?? "-"}% confianza
            </span>
          </div>
        </div>
        <div className="hero-card">
          <div className="controls-grid">
            <div>
              <label>Grupo</label>
              <select
                value={groupId}
                onChange={(e) => setGroupId(Number(e.target.value))}
              >
                {GROUPS.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>Atleta foco</label>
              <select
                value={athleteId}
                onChange={(e) => setAthleteId(Number(e.target.value))}
              >
                {athleteRows.map((athlete) => (
                  <option key={athlete.id} value={athlete.id}>
                    {athlete.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <WeekPicker
            planId={planId}
            isoWeek={isoWeek}
            onPlanIdChange={setPlanId}
            onWeekChange={setIsoWeek}
          />
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="layout-grid">
        <div className="dashboard-main">
          <div className="overview-grid">
            <div className="panel compact-card">
              <h2>Feedback sin contestar</h2>
              <strong className="big-number">
                {formatValue(pendingFeedback ?? null)}
              </strong>
              <p className="muted">
                {summary
                  ? "Pendiente según sesiones planificadas"
                  : "Carga una semana para ver pendientes"}
              </p>
            </div>
            <div className="panel compact-card">
              <h2>Próximos entrenamientos</h2>
              {upcomingSessions.length ? (
                <ul className="card-list">
                  {upcomingSessions.map((session) => (
                    <li key={session.id}>
                      <span>{session.date}</span>
                      <strong>{session.tipo_sesion ?? "sesion"}</strong>
                      <small>
                        {formatValue(session.volumen_objetivo, " km")}
                      </small>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">
                  {summary ? "Sin sesiones próximas." : "Carga una semana."}
                </p>
              )}
            </div>
            <div className="panel compact-card">
              <h2>Alertas de atletas</h2>
              {alertItems.length ? (
                <ul className="card-list">
                  {alertItems.map((alert) => (
                    <li key={alert}>
                      <span>{alert}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">
                  {summary ? "Sin alertas activas." : "Carga una semana."}
                </p>
              )}
            </div>
          </div>
          {summary ? (
            <div className="panel">
              <details open>
                <summary>Alertas y recomendaciones</summary>
                <AlertsPanel summary={summary} />
                <RecommendationsList recommendations={summary.coach.recommended} />
              </details>
              <details>
                <summary>Sesiones planificadas</summary>
                <PlanSessionsList summary={summary} />
              </details>
              <details>
                <summary>Feedback del atleta</summary>
                <FeedbackForm
                  athleteId={athleteId}
                  planId={planId}
                  isoWeek={isoWeek}
                  onSubmit={handleFeedback}
                  disabled={loading}
                />
              </details>
              <details>
                <summary>Historial de acciones</summary>
                <ActionsHistory summary={summary} />
              </details>
            </div>
          ) : (
            <div className="panel empty-state">
              Carga una semana para ver alertas y detalles del plan.
            </div>
          )}
        </div>

        <aside className="panel sidebar-panel">
          <div className="section-header">
            <h2>Accesos directos</h2>
            <p>{summary ? "CoachAI y control semanal" : "Carga una semana"}</p>
          </div>
          <div className="button-col">
            <button disabled={loading} onClick={loadWeek}>
              Cargar semana
            </button>
            <Link className="button-link ghost" to="/coach-ai">
              Ir a CoachAI
            </Link>
          </div>
        </aside>
      </section>
    </div>
  );
}
