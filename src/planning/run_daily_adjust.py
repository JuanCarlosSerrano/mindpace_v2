from sqlalchemy.orm import Session

from src.db.session import engine
from src.db.models import EntrenamientoPlanificado
from src.planning.week_view import obtener_plan_semanal
from src.planning.load_analysis import analizar_carga_semanal
from src.planning.trend_analysis import analizar_tendencia_semanal
from src.planning.daily_adjust import ajustar_entrenamientos_diarios

PLAN_ID = 1

with Session(engine) as session:
    plan = obtener_plan_semanal(session, PLAN_ID)
    carga = analizar_carga_semanal(plan)
    tendencia = analizar_tendencia_semanal(carga)

    for semana, data in tendencia.items():
        if not data["alertas"]:
            continue

        entrenamientos = data["entrenamientos"]
        ajustes = ajustar_entrenamientos_diarios(entrenamientos, data["alertas"])

        if ajustes:
            print(f"\n🗓 Ajustes diarios propuestos – {semana}")
            for a in ajustes:
                print(f"  {a['fecha']} ({a['tipo_original']})")
                for acc in a["acciones"]:
                    print(f"    - {acc}")
