from sqlalchemy.orm import Session

from src.db.session import engine
from src.planning.week_view import obtener_plan_semanal
from src.planning.load_analysis import analizar_carga_semanal
from src.planning.trend_analysis import analizar_tendencia_semanal
from src.planning.auto_adjust import ajustar_plan_semanal

PLAN_ID = 1

with Session(engine) as session:
    plan = obtener_plan_semanal(session, PLAN_ID)
    carga = analizar_carga_semanal(plan)
    tendencia = analizar_tendencia_semanal(carga)
    ajustes = ajustar_plan_semanal(tendencia)

    if not ajustes:
        print("\n✅ No se requieren ajustes. Plan equilibrado.")
    else:
        for semana, a in ajustes.items():
            print(f"\n🛠 Ajustes propuestos para {semana}")
            for accion in a["acciones"]:
                print(f"  - {accion}")
