from src.ai.coach import CoachAI
from src.ai.apply_recommendations import (
    aplicar_ajustes_diarios,
    aplicar_ajustes_semanales,
)
from src.ai.coach_actions import registrar_coach_actions
from src.db.session import SessionLocal

PLAN_ID = 2  # cambia si quieres


def main():
    session = SessionLocal()

    coach = CoachAI()
    evaluacion = coach.evaluar_plan(session, PLAN_ID)
    cumplimiento = evaluacion.get("cumplimiento", {})
    no_data_semanas = [
        semana for semana, data in cumplimiento.items()
        if data.get("estado") == "datos_insuficientes"
    ]
    if no_data_semanas:
        print("ℹ️ Semanas NO_DATA:", ", ".join(sorted(no_data_semanas)))
    recomendaciones = coach.proponer_ajustes(session, PLAN_ID)

    if not recomendaciones:
        print("✅ No hay recomendaciones. Nada que aplicar.")
        return

    print(f"🧠 CoachAI: {len(recomendaciones)} recomendaciones (antes de aplicar)")
    for r in recomendaciones:
        no_data_tag = ""
        if r.semana in no_data_semanas:
            no_data_tag = " [NO_DATA]"
        print(f"- [{r.tipo}] {r.semana}{no_data_tag} | {r.resumen} | {', '.join(r.acciones)}")

    recomendaciones_aplicables = [
        r
        for r in recomendaciones
        if not (
            r.tipo == "semanal"
            and r.resumen == "Datos reales insuficientes"
        )
    ]

    resumen_semanal, acciones_semanales = aplicar_ajustes_semanales(
        session, PLAN_ID, recomendaciones_aplicables
    )
    resumen_diario, acciones_diarias = aplicar_ajustes_diarios(
        session, PLAN_ID, recomendaciones_aplicables
    )
    print("✅ Ajustes semanales:", resumen_semanal)
    print("✅ Ajustes diarios:", resumen_diario)

    registrar_coach_actions(session, acciones_semanales + acciones_diarias)

    # Re-analizar
    rec2 = coach.proponer_ajustes(session, PLAN_ID)
    print(f"🔁 Reanálisis: {len(rec2)} recomendaciones tras aplicar")


if __name__ == "__main__":
    main()
