from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.cli.run_weekly_dashboard import build_weekly_dashboard_rows
from src.db.base import Base
from src.db.models import (
    Atleta,
    EntrenamientoPlanificado,
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


def test_weekly_dashboard_returns_weeks():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)

    session.add_all(
        [
            EntrenamientoPlanificado(
                plan_id=plan.id, fecha=date(2026, 1, 6), tipo_sesion="rodaje"
            ),
            EntrenamientoPlanificado(
                plan_id=plan.id, fecha=date(2026, 1, 13), tipo_sesion="rodaje"
            ),
        ]
    )
    session.commit()

    rows = build_weekly_dashboard_rows(session, plan_id=plan.id)
    semanas = {r["semana"] for r in rows}
    assert len(semanas) == 2


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

    rows = build_weekly_dashboard_rows(session, plan_id=plan.id)
    assert rows[0]["estado_cumplimiento"] == "datos_insuficientes"
