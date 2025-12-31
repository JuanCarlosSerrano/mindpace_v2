from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.planning.engine import generar_plan_desde_plantilla
from src.db.models import Atleta, PlantillaPlan, EntrenamientoPlanificado

DATABASE_URL = "sqlite:///mindpace_dev.db"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def main():
    session = Session()

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

    n = session.query(EntrenamientoPlanificado).filter_by(plan_id=plan_id).count()
    print(f"✅ Plan generado: plan_id={plan_id} con {n} entrenamientos planificados")

if __name__ == "__main__":
    main()
