from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.db.models import (
    Atleta,
    EntrenamientoPlanificado,
    EntrenamientoRealizado,
    PlanAtleta,
    PlantillaPlan,
    Usuario,
)
from src.planning.backfill_real_tipo import backfill_tipo_sesion, inferir_tipo_desde_texto
from src.planning.match_real_plan import vincular_real_vs_planificado


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


def test_inferir_tipo_desde_texto():
    assert inferir_tipo_desde_texto("Rodaje comodo") == "rodaje"
    assert inferir_tipo_desde_texto("EASY run") == "rodaje"
    assert inferir_tipo_desde_texto("Series controladas") == "series"
    assert inferir_tipo_desde_texto("Intervalos 8x400") == "series"
    assert inferir_tipo_desde_texto("Tempo progresivo") == "tempo"
    assert inferir_tipo_desde_texto("Threshold session") == "umbral"


def test_backfill_no_sobrescribe_tipo_existente():
    session = _session()
    atleta = _crear_atleta(session)

    r1 = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=date(2026, 1, 10),
        comentarios="Series fuertes",
        tipo_sesion="rodaje",
    )
    r2 = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=date(2026, 1, 11),
        comentarios="Series fuertes",
        tipo_sesion=None,
    )
    session.add_all([r1, r2])
    session.commit()

    resumen = backfill_tipo_sesion(session, atleta_id=atleta.id, dry_run=False)
    assert resumen["actualizados"] == 1

    session.refresh(r1)
    session.refresh(r2)
    assert r1.tipo_sesion == "rodaje"
    assert r2.tipo_sesion == "series"


def test_matching_regla2_funciona_con_tipo_explicito():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)

    fecha_plan = date(2026, 1, 11)
    planificado = EntrenamientoPlanificado(
        plan_id=plan.id,
        fecha=fecha_plan,
        tipo_sesion="series",
        volumen_objetivo=None,
    )
    session.add(planificado)
    session.flush()

    realizado = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=fecha_plan - timedelta(days=1),
        tipo_sesion="series",
    )
    session.add(realizado)
    session.commit()

    resumen = vincular_real_vs_planificado(session, atleta_id=atleta.id)
    assert resumen["vinculados"] == 1
    assert resumen["detalles"][0]["metodo"] == "fecha_tipo"
    session.refresh(realizado)
    session.refresh(planificado)
    assert realizado.planificado_id == planificado.id
    assert planificado.realizado_id == realizado.id


def test_matching_dry_run_no_persiste():
    session = _session()
    atleta = _crear_atleta(session)
    plan = _crear_plan(session, atleta.id)

    fecha_plan = date(2026, 2, 1)
    planificado = EntrenamientoPlanificado(
        plan_id=plan.id,
        fecha=fecha_plan,
        tipo_sesion="rodaje",
        volumen_objetivo=None,
    )
    session.add(planificado)
    session.flush()

    realizado = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=fecha_plan,
        tipo_sesion="rodaje",
    )
    session.add(realizado)
    session.commit()

    resumen = vincular_real_vs_planificado(session, atleta_id=atleta.id, persist=False)
    assert resumen["vinculados"] == 1

    session.refresh(realizado)
    session.refresh(planificado)
    assert realizado.planificado_id is None
    assert planificado.realizado_id is None
