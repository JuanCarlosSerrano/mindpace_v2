import { useState } from "react";
import { ApiError } from "../api/client";
import { applyCoach, revertCoach } from "../api/coach";
import { getWeekSummary } from "../api/dashboard";
import { postFeedback } from "../api/feedback";
import type { WeeklySummary } from "../api/types";
import ActionsHistory from "../components/ActionsHistory";
import AlertsPanel from "../components/AlertsPanel";
import FeedbackForm from "../components/FeedbackForm";
import RecommendationsList from "../components/RecommendationsList";
import SummaryCards from "../components/SummaryCards";
import WeekPicker from "../components/WeekPicker";

export default function WeekDashboardPage() {
  const [planId, setPlanId] = useState(2);
  const [athleteId, setAthleteId] = useState(1);
  const [isoWeek, setIsoWeek] = useState("2026-W03");
  const [revertLast, setRevertLast] = useState(1);
  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showJson, setShowJson] = useState(false);

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

  const handleDryRun = async () => {
    setLoading(true);
    setError(null);
    try {
      await applyCoach(planId, { week: isoWeek, dry_run: true });
      await loadWeek();
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
      await applyCoach(planId, { week: isoWeek, dry_run: false });
      await loadWeek();
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
      await revertCoach(planId, { last: revertLast });
      await loadWeek();
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <div className="page">
        <header className="hero">
          <h1>MindPace Weekly Dashboard</h1>
          <p>
            WeeklySummary + feedback + CoachAI, en una sola vista explicable.
          </p>
        </header>

        <section className="panel controls">
          <WeekPicker
            planId={planId}
            athleteId={athleteId}
            isoWeek={isoWeek}
            onPlanIdChange={setPlanId}
            onAthleteIdChange={setAthleteId}
            onWeekChange={setIsoWeek}
          />
          <div className="button-row">
            <button disabled={loading} onClick={loadWeek}>
              Cargar semana
            </button>
            <button disabled={loading} className="secondary" onClick={handleDryRun}>
              Dry-run Coach
            </button>
            <button disabled={loading} onClick={handleApply}>
              Aplicar Coach
            </button>
            <button disabled={loading} className="ghost" onClick={handleRevert}>
              Revertir últimos
            </button>
            <input
              type="number"
              min={1}
              value={revertLast}
              onChange={(e) => setRevertLast(Number(e.target.value))}
              style={{ maxWidth: 80 }}
            />
            <button
              disabled={loading}
              className="ghost"
              onClick={() => setShowJson((v) => !v)}
            >
              {showJson ? "Ocultar JSON" : "Mostrar JSON"}
            </button>
          </div>
        </section>

        {error && <div className="error">{error}</div>}

        {summary && (
          <>
            <SummaryCards summary={summary} />
            <AlertsPanel summary={summary} />
            <RecommendationsList recommendations={summary.coach.recommended} />
            <FeedbackForm
              athleteId={athleteId}
              planId={planId}
              isoWeek={isoWeek}
              onSubmit={handleFeedback}
              disabled={loading}
            />
            <ActionsHistory summary={summary} />
            {showJson && <pre className="json">{JSON.stringify(summary, null, 2)}</pre>}
          </>
        )}
      </div>
    </main>
  );
}
