import argparse
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.planning.match_real_plan import vincular_real_vs_planificado

DATABASE_URL = "sqlite:///mindpace_dev.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--atleta", type=int, required=True)
    parser.add_argument("--plan", type=int, default=None)
    parser.add_argument("--inicio", default=None)
    parser.add_argument("--fin", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-ignored", action="store_true")
    args = parser.parse_args()

    session = Session()
    resumen = vincular_real_vs_planificado(
        session,
        atleta_id=args.atleta,
        plan_id=args.plan,
        fecha_inicio=_parse_date(args.inicio),
        fecha_fin=_parse_date(args.fin),
        persist=not args.dry_run,
    )

    print("🔗 Vinculacion plan vs real")
    if args.dry_run:
        print("⚠️ DRY RUN — no se aplicaran cambios")
        print(f"Vinculables: {resumen['vinculados']}")
        print(f"No vinculables: {resumen['no_vinculados']}")
        print(f"Conflictos: {resumen['conflictos']}")
    else:
        print(f"Vinculados: {resumen['vinculados']}")
        print(f"No vinculados: {resumen['no_vinculados']}")
        print(f"Conflictos: {resumen['conflictos']}")
    print("")

    for d in resumen["detalles"]:
        print(
            f"- Real {d['real_id']} ({d['fecha_real']}) ↔ "
            f"Plan {d['plan_id']} ({d['fecha_plan']}) | "
            f"{d['metodo']} | confianza {d['confianza']} | tipo {d['tipo']}"
        )

    if args.show_ignored and resumen.get("ignored_details"):
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
