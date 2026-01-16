from datetime import date
from types import SimpleNamespace

from src.ai.coach import CoachRecommendation, apply_feedback_modulation


def test_pain_blocks_adjustments_adds_info():
    recs = [
        CoachRecommendation(
            semana="2026-W03",
            tipo="semanal",
            resumen="Ajuste de carga semanal",
            acciones=["Semana marcada como descarga"],
            explicacion="x",
        )
    ]
    weekly_summary = {
        "2026-W03": {
            "feedback": {"pain_days": 1, "avg_rpe": None, "high_fatigue_days": 0},
            "compliance": {"status": "OK"},
            "plan_entrenamientos": [],
        }
    }
    result = apply_feedback_modulation(recs, weekly_summary)
    assert len(result) == 1
    assert result[0].resumen.startswith("Dolor reportado")
    assert result[0].kind == "info"


def test_ok_feedback_negative_adds_daily_and_removes_descarga():
    recs = [
        CoachRecommendation(
            semana="2026-W03",
            tipo="semanal",
            resumen="Ajuste de carga semanal",
            acciones=["Semana marcada como descarga"],
            explicacion="x",
        )
    ]
    plan_entrenos = [
        SimpleNamespace(fecha=date(2026, 1, 13)),
        SimpleNamespace(fecha=date(2026, 1, 15)),
    ]
    weekly_summary = {
        "2026-W03": {
            "feedback": {"avg_rpe": 8, "high_fatigue_days": 0, "pain_days": 0},
            "compliance": {"status": "OK"},
            "plan_entrenamientos": plan_entrenos,
        }
    }
    result = apply_feedback_modulation(recs, weekly_summary)
    assert all(
        not (r.tipo == "semanal" and "descarga" in " ".join(r.acciones).lower())
        for r in result
    )
    assert any(r.tipo == "diaria" for r in result)
