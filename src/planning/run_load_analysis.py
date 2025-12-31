from sqlalchemy.orm import Session

from src.db.session import engine
from src.planning.week_view import obtener_plan_semanal
from src.planning.load_analysis import analizar_carga_semanal

PLAN_ID = 1

with Session(engine) as session:
    plan_semanal = obtener_plan_semanal(session, PLAN_ID)
    analisis = analizar_carga_semanal(plan_semanal)

    for semana, data in analisis.items():
        print(f"\n📅 Semana {semana}")
        print(f"  Volumen: {data['volumen_total']} km")
        print(f"  Sesiones duras: {data['sesiones_duras']}")
        print(f"  Índice de carga: {data['indice_carga']}")

        if data["alertas"]:
            for a in data["alertas"]:
                print(f"  {a}")
        else:
            print("  ✅ Carga controlada")
