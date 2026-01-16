import argparse
from datetime import date

from src.analysis.plan_vs_real import generar_comparacion_plan_real
from src.db.session import SessionLocal


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=int, required=True)
    parser.add_argument("--atleta", type=int, required=True)
    parser.add_argument("--inicio", default=None)
    parser.add_argument("--fin", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-ignored", action="store_true")
    args = parser.parse_args()

    session = SessionLocal()
    resumen = generar_comparacion_plan_real(
        session,
        plan_id=args.plan,
        atleta_id=args.atleta,
        fecha_inicio=_parse_date(args.inicio),
        fecha_fin=_parse_date(args.fin),
        persist=not args.dry_run,
    )

    titulo = "📊 Comparacion plan vs real"
    if args.dry_run:
        titulo += " (dry-run)"
    print(titulo)
    print(f"Insertados: {resumen['insertados']}")
    print(f"Actualizados: {resumen['actualizados']}")
    print(f"Ignorados: {resumen['ignorados']}")
    if args.show_ignored and resumen["ignored_details"]:
        print("")
        print("Ignorados (detalle):")
        for d in resumen["ignored_details"]:
            print(
                f"- real_id={d['real_id']} planificado_id={d['planificado_id']} "
                f"plan_id_del_planificado={d['plan_id_del_planificado']} "
                f"plan_id_objetivo={d['plan_id_objetivo']} motivo={d['motivo']}"
            )


if __name__ == "__main__":
    main()
