import type { CoachRecommendation } from "../api/types";

type Props = {
  recommendations: CoachRecommendation[];
};

const severityClass: Record<string, string> = {
  high: "pill high",
  medium: "pill medium",
  low: "pill low",
  info: "pill info",
};

export default function RecommendationsList({ recommendations }: Props) {
  return (
    <div className="panel">
      <h2>Recomendaciones</h2>
      <div className="list">
        {recommendations.length === 0 ? (
          <p className="muted">Sin recomendaciones.</p>
        ) : (
          recommendations.map((rec, idx) => (
            <div className="list-item" key={`${rec.summary}-${idx}`}>
              <div className="flex">
                <span className={severityClass[rec.severity || "low"]}>
                  {rec.severity || "low"}
                </span>
                <span className="pill info">P{rec.priority ?? "-"}</span>
                <span className="pill">{rec.scope || rec.action_type}</span>
                <span className="pill">{rec.reason || "GENERAL"}</span>
              </div>
              <h4>{rec.summary}</h4>
              <p className="muted">{rec.explanation}</p>
              <ul>
                {rec.actions.map((action, actionIdx) => (
                  <li key={`${action.message}-${actionIdx}`}>
                    {action.message || action.code}
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
