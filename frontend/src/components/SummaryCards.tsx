import type { WeeklySummary } from "../api/types";

type Props = {
  summary: WeeklySummary;
};

export default function SummaryCards({ summary }: Props) {
  return (
    <div className="grid-two">
      <div className="summary-card">
        <h3>Plan</h3>
        <div className="flex">
          <span>Sesiones: {summary.plan.sessions_count}</span>
          <span>Volumen: {summary.plan.volume_km_total} km</span>
        </div>
        <p className="muted">
          Tipos:{" "}
          {Object.entries(summary.plan.by_type)
            .map(([k, v]) => `${k} (${v})`)
            .join(", ")}
        </p>
      </div>
      <div className="summary-card">
        <h3>Real</h3>
        <div className="flex">
          <span>Sesiones: {summary.real.sessions_count}</span>
          <span>Volumen: {summary.real.volume_km_total} km</span>
          <span>Coverage: {summary.real.coverage_ratio ?? "-"}</span>
        </div>
      </div>
      <div className="summary-card">
        <h3>Compliance</h3>
        <div className="flex">
          <span>Estado: {summary.compliance.status}</span>
          <span>Ratio vol: {summary.compliance.ratio_volume ?? "-"}</span>
          <span>Ratio ses: {summary.compliance.ratio_sessions ?? "-"}</span>
        </div>
      </div>
      <div className="summary-card">
        <h3>Load</h3>
        <div className="flex">
          <span>Índice: {summary.load.load_index ?? "-"}</span>
          <span>Tendencia: {summary.load.trend ?? "-"}</span>
        </div>
      </div>
    </div>
  );
}
