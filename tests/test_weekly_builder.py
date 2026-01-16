from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.dashboard.weekly_builder import build_weekly_summary
from src.db.base import Base
from src.db.models import (
    Atleta,
    ComparacionPlanReal,
    CoachAction,
    EntrenamientoPlanificado,
    EntrenamientoRealizado,
    PlanAtleta,
    PlantillaPlan,
    Usuario,
)


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _crear_atleta(session):
    entrenador = Usuario(
        email="coach@example.com", password_hash="x", rol="entrenador", activo=True
    )
    atleta_user = Usuario(
        email="athlete@example.com", password_hash="y", rol="atleta", activo=True
    )
    session.add_all([entrenador, atleta_user])
    session.flush()

    atleta = Atleta(usuario_id=atleta_user.id, entrenador_id=entrenador.id)
    session.add(atleta)
    session.flush()
    return atleta


def _crear_plan(session, atleta_id):
    plantilla = PlantillaPlan(nombre="Base", descripcion=None)
    session.add(plantilla)
    session.flush()
    plan = PlanAtleta(atleta_id=atleta_id, plantilla_id=plantilla.id)
    session.add(plan)
    session.flush()
    return plan


def test_weekly_dashboard_returns_week():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)

    session.add(
        EntrenamientoPlanificado(
            plan_id=plan.id, fecha=date(2026, 1, 6), tipo_sesion="rodaje"
        )
    )
    session.commit()

    summary = build_weekly_summary(plan_id=plan.id, iso_week="2026-W02", session=session)
    assert summary["week"]["iso"] == "2026-W02"
    assert summary["plan"]["sessions_count"] == 1


def test_weekly_dashboard_includes_no_data_state():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)

    session.add(
        EntrenamientoPlanificado(
            plan_id=plan.id, fecha=date(2026, 1, 6), tipo_sesion="rodaje"
        )
    )
    session.commit()

    summary = build_weekly_summary(plan_id=plan.id, iso_week="2026-W02", session=session)
    assert summary["compliance"]["status"] == "NO_DATA"


def test_low_week_has_no_pending_recommendations():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)

    planificado_1 = EntrenamientoPlanificado(
        plan_id=plan.id, fecha=date(2026, 1, 6), tipo_sesion="rodaje", volumen_objetivo=10
    )
    planificado_2 = EntrenamientoPlanificado(
        plan_id=plan.id, fecha=date(2026, 1, 7), tipo_sesion="rodaje", volumen_objetivo=10
    )
    session.add_all([planificado_1, planificado_2])
    session.flush()

    realizado = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=date(2026, 1, 6),
        planificado_id=planificado_1.id,
        distancia_km=2,
    )
    session.add(realizado)
    session.flush()

    session.add(
        ComparacionPlanReal(
            plan_id=plan.id,
            atleta_id=atleta.id,
            fecha=date(2026, 1, 6),
            entrenamiento_planificado_id=planificado_1.id,
            entrenamiento_realizado_id=realizado.id,
            dist_real_km=2,
            pct_dist=0.2,
        )
    )
    session.commit()

    summary = build_weekly_summary(plan_id=plan.id, iso_week="2026-W02", session=session)
    assert summary["compliance"]["status"] == "LOW"
    assert summary["coach"]["remaining_after_apply_count"] == 0


def test_actions_are_reflected_in_history():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)
    session.add(
        EntrenamientoPlanificado(
            plan_id=plan.id, fecha=date(2026, 1, 6), tipo_sesion="rodaje"
        )
    )
    session.commit()

    session.add(
        CoachAction(
            plan_id=plan.id,
            semana="2026-W02",
            tipo="semanal",
            acciones=["Semana marcada como descarga"],
        )
    )
    session.commit()

    summary = build_weekly_summary(plan_id=plan.id, iso_week="2026-W02", session=session)
    assert len(summary["actions"]["applied"]) == len(summary["history"])


def test_no_data_never_creates_aggressive_actions():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)
    session.add(
        EntrenamientoPlanificado(
            plan_id=plan.id, fecha=date(2026, 1, 6), tipo_sesion="rodaje"
        )
    )
    session.commit()

    summary = build_weekly_summary(plan_id=plan.id, iso_week="2026-W02", session=session)
    if summary["compliance"]["status"] == "NO_DATA":
        for action in summary["actions"]["applied"]:
            messages = " ".join(a["message"] for a in action["actions"]).lower()
            assert "eliminar" not in messages
