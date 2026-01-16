import type { WeeklySummary } from "../api/types";

type Props = {
  summary: WeeklySummary;
};

function renderActions(actions: Array<{ actions: { code?: string; message?: string }[] }>) {
  return actions.flatMap((a) => a.actions.map((x) => x.message || x.code)).join(", ");
}

export default function ActionsHistory({ summary }: Props) {
  return (
    <div className="panel">
      <h2>Acciones e historial</h2>
      <div className="grid-two">
        <div>
          <h4>Aplicadas</h4>
          {summary.actions.applied.length ? (
            <ul>
              {summary.actions.applied.map((a) => (
                <li key={a.id}>
                  #{a.id} · {a.action_type} · {a.state} · {a.created_at}
                  <div className="muted">{renderActions([a])}</div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">Sin acciones aplicadas.</p>
          )}
        </div>
        <div>
          <h4>Historial</h4>
          {summary.history.length ? (
            <ul>
              {summary.history.map((a) => (
                <li key={`h-${a.id}`}>
                  #{a.id} · {a.action_type} · {a.state} · {a.created_at}
                  <div className="muted">{renderActions([a])}</div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">Sin historial.</p>
          )}
        </div>
      </div>
    </div>
  );
}
