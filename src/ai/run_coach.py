import argparse

from sqlalchemy.orm import Session

from src.db.session import engine
from src.db.models import PlanAtleta
from src.ai.coach import CoachAI

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta CoachAI sobre un plan.")
    parser.add_argument(
        "--plan-id",
        type=int,
        default=None,
        help="ID del plan a evaluar. Si no se indica, usa el plan más reciente.",
    )
    return parser.parse_args()


def _get_latest_plan_id(session: Session) -> int:
    plan = session.query(PlanAtleta).order_by(PlanAtleta.id.desc()).first()
    if not plan:
        raise RuntimeError("No hay planes en la base de datos.")
    return plan.id

def main():
    args = _parse_args()
    coach = CoachAI()

    with Session(engine) as session:
        plan_id = args.plan_id or _get_latest_plan_id(session)
        recomendaciones = coach.proponer_ajustes(session, plan_id)

        if not recomendaciones:
            print(f"✅ CoachAI: no hay ajustes necesarios. Plan equilibrado (plan_id={plan_id}).")
            return

        print(f"🧠 CoachAI: {len(recomendaciones)} recomendaciones\n")

        for r in recomendaciones:
            print(f"📅 Semana {r.semana} | {r.tipo.upper()} | {r.resumen}")
            for acc in r.acciones:
                print(f"  - {acc}")
            print(f"  💬 {r.explicacion}\n")


if __name__ == "__main__":
    main()
