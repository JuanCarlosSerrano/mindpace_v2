from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analysis.plan_vs_real import generar_comparacion_plan_real
from src.db.base import Base
from src.db.models import (
    ComparacionPlanReal,
    Atleta,
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


def _crear_plan(session):
    coach = Usuario(email="coach@example.com", password_hash="x", rol="entrenador", activo=True)
    atleta_user = Usuario(email="athlete@example.com", password_hash="y", rol="atleta", activo=True)
    session.add_all([coach, atleta_user])
    session.flush()

    atleta = Atleta(usuario_id=atleta_user.id, entrenador_id=coach.id)
    session.add(atleta)
    session.flush()

    plantilla = PlantillaPlan(nombre="Base", descripcion=None)
    session.add(plantilla)
    session.flush()

    plan = PlanAtleta(atleta_id=atleta.id, plantilla_id=plantilla.id)
    session.add(plan)
    session.flush()
    return atleta, plan


def test_pct_dist_calculo():
    session = _session()
    atleta, plan = _crear_plan(session)

    planificado = EntrenamientoPlanificado(
        plan_id=plan.id,
        fecha=date(2026, 1, 10),
        tipo_sesion="rodaje",
        volumen_objetivo=10.0,
        ritmo_objetivo=None,
    )
    session.add(planificado)
    session.flush()

    realizado = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=planificado.fecha,
        distancia_km=8.0,
        tiempo_seg=2400,
        planificado_id=planificado.id,
    )
    session.add(realizado)
    session.commit()

    generar_comparacion_plan_real(session, plan_id=plan.id, atleta_id=atleta.id)
    comp = session.query(ComparacionPlanReal).first()
    assert float(comp.pct_dist) == 0.8


def test_upsert_comparacion_idempotente():
    session = _session()
    atleta, plan = _crear_plan(session)

    planificado = EntrenamientoPlanificado(
        plan_id=plan.id,
        fecha=date(2026, 1, 10),
        tipo_sesion="rodaje",
        volumen_objetivo=10.0,
        ritmo_objetivo=None,
    )
    session.add(planificado)
    session.flush()

    realizado = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=planificado.fecha,
        distancia_km=8.0,
        tiempo_seg=2400,
        planificado_id=planificado.id,
    )
    session.add(realizado)
    session.commit()

    resumen1 = generar_comparacion_plan_real(session, plan_id=plan.id, atleta_id=atleta.id)
    resumen2 = generar_comparacion_plan_real(session, plan_id=plan.id, atleta_id=atleta.id)

    assert resumen1["insertados"] == 1
    assert resumen2["actualizados"] == 1
    assert session.query(ComparacionPlanReal).count() == 1
