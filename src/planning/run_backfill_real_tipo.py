import argparse

from src.planning.backfill_real_tipo import backfill_tipo_sesion
from src.db.session import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--atleta", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    session = SessionLocal()
    resumen = backfill_tipo_sesion(
        session, atleta_id=args.atleta, dry_run=args.dry_run
    )

    titulo = "🔎 Backfill tipo_sesion"
    if args.dry_run:
        titulo += " (dry-run)"
    print(titulo)
    print(f"Actualizados: {resumen['actualizados']}")
    print(f"Sin match: {resumen['sin_match']}")


if __name__ == "__main__":
    main()
