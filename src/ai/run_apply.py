from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.ai.coach import CoachAI
from src.ai.apply_recommendations import (
    aplicar_ajustes_diarios,
    aplicar_ajustes_semanales,
)
from src.ai.coach_actions import registrar_coach_actions

DATABASE_URL = "sqlite:///mindpace_dev.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

PLAN_ID = 2  # cambia si quieres


def main():
    session = Session()

    coach = CoachAI()
    recomendaciones = coach.proponer_ajustes(session, PLAN_ID)

    if not recomendaciones:
        print("✅ No hay recomendaciones. Nada que aplicar.")
        return

    print(f"🧠 CoachAI: {len(recomendaciones)} recomendaciones (antes de aplicar)")
    for r in recomendaciones:
        print(f"- [{r.tipo}] {r.semana} | {r.resumen} | {', '.join(r.acciones)}")

    resumen_semanal, acciones_semanales = aplicar_ajustes_semanales(
        session, PLAN_ID, recomendaciones
    )
    resumen_diario, acciones_diarias = aplicar_ajustes_diarios(
        session, PLAN_ID, recomendaciones
    )
    print("✅ Ajustes semanales:", resumen_semanal)
    print("✅ Ajustes diarios:", resumen_diario)

    registrar_coach_actions(session, acciones_semanales + acciones_diarias)

    # Re-analizar
    rec2 = coach.proponer_ajustes(session, PLAN_ID)
    print(f"🔁 Reanálisis: {len(rec2)} recomendaciones tras aplicar")


if __name__ == "__main__":
    main()
