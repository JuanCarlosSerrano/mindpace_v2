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


def test_weekly_contract_validates_current_output():
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
