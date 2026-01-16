import type { WeeklySummary } from "../api/types";

type Props = {
  summary: WeeklySummary;
};

export default function AlertsPanel({ summary }: Props) {
  return (
    <div className="panel">
      <h2>Alertas</h2>
      <div className="grid-two">
        <div>
          <h4>Plan</h4>
          {summary.alerts.plan.length ? (
            <ul>
              {summary.alerts.plan.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">Sin alertas.</p>
          )}
        </div>
        <div>
          <h4>Real</h4>
          {summary.alerts.real_risk.length ? (
            <ul>
              {summary.alerts.real_risk.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">Sin alertas.</p>
          )}
        </div>
      </div>
    </div>
  );
}
