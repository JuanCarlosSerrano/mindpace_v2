from sqlalchemy.orm import Session

from src.db.session import engine
from src.planning.week_view import obtener_plan_semanal
from src.planning.load_analysis import analizar_carga_semanal
from src.planning.trend_analysis import analizar_tendencia_semanal

PLAN_ID = 1

with Session(engine) as session:
    plan = obtener_plan_semanal(session, PLAN_ID)
    carga = analizar_carga_semanal(plan)
    tendencia = analizar_tendencia_semanal(carga)

    for semana, data in tendencia.items():
        print(f"\n📅 Semana {semana}")
        print(f"  Volumen: {data['volumen_total']} km")
        print(f"  Sesiones duras: {data['sesiones_duras']}")
        print(f"  Índice de carga: {data['indice_carga']}")
        print(f"  Tendencia: {data['tendencia']}")

        if data["variacion_pct"] is not None:
            print(f"  Variación: {data['variacion_pct']} %")

        if data["alertas"]:
            for a in data["alertas"]:
                print(f"  {a}")
        else:
            print("  ✅ Progresión correcta")
