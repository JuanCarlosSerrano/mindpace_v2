from src.ai.coach import CoachRecommendation, classify_recommendations


def test_classify_priority_by_reason():
    recs = [
        CoachRecommendation(
            semana="2026-W03",
            tipo="semanal",
            resumen="Dolor reportado",
            acciones=["Revisión manual del plan recomendada"],
            explicacion="x",
            reason="PAIN_FLAG",
            kind="info",
        ),
        CoachRecommendation(
            semana="2026-W03",
            tipo="diaria",
            resumen="Reducir intensidad",
            acciones=["Reducir intensidad (ritmo más conservador)"],
            explicacion="x",
            reason="FEEDBACK",
            kind="adjustment",
        ),
        CoachRecommendation(
            semana="2026-W03",
            tipo="semanal",
            resumen="Ajuste de carga semanal",
            acciones=["Semana marcada como descarga"],
            explicacion="x",
            reason="LOW",
            kind="adjustment",
        ),
        CoachRecommendation(
            semana="2026-W03",
            tipo="semanal",
            resumen="Datos reales insuficientes",
            acciones=["Importar entrenamientos reales para evaluar cumplimiento"],
            explicacion="x",
            reason="NO_DATA",
            kind="info",
        ),
        CoachRecommendation(
            semana="2026-W03",
            tipo="semanal",
            resumen="Info general",
            acciones=["Importar entrenamientos reales para evaluar cumplimiento"],
            explicacion="x",
            kind="info",
        ),
    ]
    ordered = classify_recommendations(recs)
    assert ordered[0].priority == 1
    assert ordered[1].priority == 2
    assert ordered[2].priority == 3
    assert ordered[3].priority == 4
    assert ordered[4].priority == 5
    assert ordered[0].severity == "high"
    assert ordered[1].severity == "medium"
    assert ordered[2].severity == "medium"
    assert ordered[3].severity == "info"
    assert ordered[4].severity == "info"
