from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.dashboard.weekly_builder import build_weekly_summary
from src.dashboard.weekly_contract import validate_weekly_summary
from src.db.base import Base
from src.db.models import (
    Atleta,
    EntrenamientoPlanificado,
    PlanAtleta,
    PlantillaPlan,
    Usuario,
)
from src.feedback.repo import get_feedback_range, upsert_feedback


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


def test_feedback_upsert_and_fetch():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)

    fecha = date(2026, 1, 15)
    fb1 = upsert_feedback(
        session,
        athlete_id=atleta.id,
        plan_id=plan.id,
        session_date=fecha,
        payload={"rpe": 7, "fatigue": 6, "notes": "Cansado"},
    )
    fb2 = upsert_feedback(
        session,
        athlete_id=atleta.id,
        plan_id=plan.id,
        session_date=fecha,
        payload={"rpe": 8, "fatigue": 8, "notes": "Mejor"},
    )
    assert fb1.id == fb2.id

    items = get_feedback_range(session, atleta.id, fecha, fecha)
    assert len(items) == 1
    assert items[0].rpe == 8
    assert items[0].fatigue == 8


def test_weekly_summary_includes_feedback_empty_when_none():
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
    feedback = summary["feedback"]
    assert feedback["count"] == 0
    assert feedback["coverage"] == 0.0
    assert feedback["avg_rpe"] is None
    assert feedback["pain_signal"] is False


def test_weekly_summary_includes_feedback_with_data():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)
    session.add_all(
        [
            EntrenamientoPlanificado(
                plan_id=plan.id, fecha=date(2026, 1, 6), tipo_sesion="rodaje"
            ),
            EntrenamientoPlanificado(
                plan_id=plan.id, fecha=date(2026, 1, 7), tipo_sesion="rodaje"
            ),
        ]
    )
    session.commit()

    upsert_feedback(
        session,
        athlete_id=atleta.id,
        plan_id=plan.id,
        session_date=date(2026, 1, 6),
        payload={"rpe": 8, "fatigue": 9, "notes": "Piernas cargadas"},
    )

    summary = build_weekly_summary(plan_id=plan.id, iso_week="2026-W02", session=session)
    feedback = summary["feedback"]
    assert feedback["count"] == 1
    assert feedback["avg_rpe"] == 8
    assert feedback["high_fatigue_days"] == 1
    assert feedback["pain_days"] == 0
    assert feedback["pain_signal"] is False
    assert feedback["coverage"] == 0.5
    assert feedback["notes_preview"]


def test_contract_validation_with_feedback():
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
    validate_weekly_summary(summary)
