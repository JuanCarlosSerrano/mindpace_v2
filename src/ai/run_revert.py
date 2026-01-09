import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.ai.coach_actions import revertir_coach_actions
from src.db.models import CoachAction

DATABASE_URL = "sqlite:///mindpace_dev.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


def _parse_ids(value: str) -> list[int]:
    return [int(x) for x in value.split(",") if x.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=int, default=2)
    parser.add_argument("--week", dest="semana", default="")
    parser.add_argument("--ids", type=_parse_ids, default=[])
    parser.add_argument("--last", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    session = Session()

    acciones = _resolve_actions(session, args)
    if args.dry_run:
        _print_dry_run(acciones)
        return

    if not acciones:
        print("✅ No hay acciones aplicadas para revertir.")
        return

    if not args.yes:
        scope = _format_scope(args)
        resumen = _summarize_actions(acciones)
        if resumen["acciones"] >= 5 or resumen["sesiones"] >= 10:
            print(
                f"⚠️ Vas a revertir {resumen['acciones']} acciones que afectan a "
                f"{resumen['sesiones']} sesiones."
            )
        resp = input(f"¿Confirmas revertir {scope}? [y/N]: ").strip().lower()
        if resp not in ("y", "yes", "s", "si"):
            print("❎ Cancelado.")
            return

    ids = [a.id for a in acciones]
    resumen = revertir_coach_actions(session, ids, motivo=args.reason or None)
    print("✅ Reversion completada:", resumen)


def _resolve_actions(session, args) -> list[CoachAction]:
    if args.semana:
        return (
            session.query(CoachAction)
            .filter(CoachAction.plan_id == args.plan)
            .filter(CoachAction.semana == args.semana)
            .filter(CoachAction.estado == "aplicada")
            .filter(CoachAction.tipo.in_(("semanal", "diaria")))
            .order_by(CoachAction.created_at.desc())
            .all()
        )

    if args.ids:
        return (
            session.query(CoachAction)
            .filter(CoachAction.id.in_(args.ids))
            .filter(CoachAction.estado == "aplicada")
            .filter(CoachAction.tipo.in_(("semanal", "diaria")))
            .order_by(CoachAction.created_at.desc())
            .all()
        )

    acciones = (
        session.query(CoachAction)
        .filter(CoachAction.plan_id == args.plan)
        .filter(CoachAction.estado == "aplicada")
        .filter(CoachAction.tipo.in_(("semanal", "diaria")))
        .order_by(CoachAction.created_at.desc())
        .limit(args.last)
        .all()
    )
    return list(acciones)


def _format_scope(args) -> str:
    if args.semana:
        return f"semana {args.semana} (plan {args.plan})"
    if args.ids:
        return f"acciones {args.ids}"
    return f"últimas {args.last} acciones (plan {args.plan})"


def _summarize_actions(acciones: list[CoachAction]) -> dict:
    sesiones = set()
    for a in acciones:
        cambios = (a.acciones or {}).get("cambios", [])
        for c in cambios:
            if c.get("entrenamiento_id") is not None:
                sesiones.add(c.get("entrenamiento_id"))
    return {"acciones": len(acciones), "sesiones": len(sesiones)}


def _print_dry_run(acciones: list[CoachAction]) -> None:
    if not acciones:
        print("✅ No hay acciones aplicadas para revertir.")
        return

    sesiones = set()
    total_borradas = 0
    print("⚠️ DRY RUN — no se aplicarán cambios")
    print(f"Se revertirían {len(acciones)} acciones:")
    for a in acciones:
        cambios = (a.acciones or {}).get("cambios", [])
        borradas = 0
        for c in cambios:
            if c.get("entrenamiento_id") is not None:
                sesiones.add(c.get("entrenamiento_id"))
            if c.get("deleted"):
                borradas += 1
                total_borradas += 1

        etiqueta = a.semana or (a.fecha.isoformat() if a.fecha else "sin_fecha")
        print(
            f"- Acción {a.id} ({etiqueta}): {len(cambios)} sesiones, "
            f"{borradas} eliminaciones"
        )
    print(f"Total sesiones afectadas: {len(sesiones)}")


if __name__ == "__main__":
    main()
