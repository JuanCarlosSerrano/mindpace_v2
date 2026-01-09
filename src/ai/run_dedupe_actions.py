from collections import defaultdict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import CoachAction

DATABASE_URL = "sqlite:///mindpace_dev.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

PLAN_ID = 2  # cambia si quieres


def main():
    session = Session()
    acciones = (
        session.query(CoachAction)
        .filter(CoachAction.plan_id == PLAN_ID)
        .filter(CoachAction.tipo == "diaria")
        .filter(CoachAction.fecha.isnot(None))
        .order_by(CoachAction.created_at.asc(), CoachAction.id.asc())
        .all()
    )

    grupos = defaultdict(list)
    for a in acciones:
        key = (a.plan_id, a.tipo, a.fecha)
        grupos[key].append(a)

    duplicados = []
    for items in grupos.values():
        if len(items) > 1:
            duplicados.extend(items[1:])

    if not duplicados:
        print("✅ No hay duplicados diarios para eliminar.")
        return

    for a in duplicados:
        session.delete(a)

    session.commit()
    print(f"🧹 Eliminados {len(duplicados)} duplicados diarios.")


if __name__ == "__main__":
    main()
