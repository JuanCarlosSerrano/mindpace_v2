from datetime import date
from src.db.session import SessionLocal
from decimal import Decimal
from src.db.base import Base
from src.planning.engine import generar_plan_desde_plantilla
from src.db.models import Atleta, PlantillaPlan, EntrenamientoPlanificado
from sqlalchemy import extract

def main():
    session = SessionLocal()

    atleta = session.query(Atleta).first()
    plantilla = session.query(PlantillaPlan).first()

    if not atleta or not plantilla:
        raise RuntimeError("No hay datos. Ejecuta primero: python3 -m src.fixtures.seed_data")

    plan_id = generar_plan_desde_plantilla(
        session=session,
        atleta_id=atleta.id,
        plantilla_id=plantilla.id,
        fecha_inicio=date(2026, 1, 5),
        objetivo_descripcion="Plan generado automáticamente (v1)",
    )

    # ⚠️ ESCENARIO DE PRUEBA: subida brusca de volumen en la semana 2026-W03
    entrenos_semana_3 = (
        session.query(EntrenamientoPlanificado)
        .filter(
            EntrenamientoPlanificado.plan_id == plan_id,
            extract("week", EntrenamientoPlanificado.fecha) == 3
        )
        .all()
    )

    for e in entrenos_semana_3:
        if e.volumen_objetivo:
            e.volumen_objetivo *= Decimal("2.0")  # +100% artificial
            entreno_extra = EntrenamientoPlanificado(
            plan_id=plan_id,
            fecha=date(2026, 1, 15),
            tipo_sesion="series",
            detalle_series="8x1000",
            ritmo_objetivo=190,
            volumen_objetivo=Decimal("16")
            )

    session.add(entreno_extra)
    session.commit()
    for e in entrenos_semana_3:
        print(
            f"[DEBUG] {e.fecha} | {e.tipo_sesion} | volumen={e.volumen_objetivo}"
        )

    print("🔥 Sesión dura extra añadida en semana 3")
    
    n = session.query(EntrenamientoPlanificado).filter_by(plan_id=plan_id).count()
    print(f"✅ Plan generado: plan_id={plan_id} con {n} entrenamientos planificados")
    print("Entrenos semana 3 encontrados:", len(entrenos_semana_3))

if __name__ == "__main__":
    main()
