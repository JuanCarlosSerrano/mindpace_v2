from sqlalchemy.orm import Session

from src.db.session import engine
from src.planning.week_view import obtener_plan_semanal

PLAN_ID = 1  # ajusta si tienes otro

with Session(engine) as session:
    semanas = obtener_plan_semanal(session, PLAN_ID)

    for semana, data in semanas.items():
        print(f"\n📅 Semana {semana}")
        print(f"  Sesiones: {data['sesiones']}")
        print(f"  Volumen total: {data['volumen_total']} km")

        for tipo, n in data["por_tipo"].items():
            print(f"  - {tipo}: {n}")
