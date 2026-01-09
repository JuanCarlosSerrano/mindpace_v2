import argparse
import csv
import json
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.ai.coach_actions import listar_coach_actions

DATABASE_URL = "sqlite:///mindpace_dev.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


def _to_dict(a):
    return {
        "id": a.id,
        "plan_id": a.plan_id,
        "tipo": a.tipo,
        "semana": a.semana,
        "fecha": a.fecha.isoformat() if a.fecha else None,
        "estado": a.estado,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "acciones": a.acciones,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=int, default=2)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--format", choices=["text", "json", "csv"], default="text")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    session = Session()
    acciones = listar_coach_actions(session, plan_id=args.plan, limit=args.limit)
    if not acciones:
        print("✅ No hay acciones registradas.")
        return

    if args.format == "text":
        for a in acciones:
            print(
                f"{a.id} | plan={a.plan_id} | {a.tipo} | semana={a.semana} | "
                f"fecha={a.fecha} | estado={a.estado} | created_at={a.created_at}"
            )
        return

    rows = [_to_dict(a) for a in acciones]

    if args.output == "-":
        out = sys.stdout
    else:
        out = open(args.output, "w", newline="", encoding="utf-8")

    try:
        if args.format == "json":
            json.dump(rows, out, ensure_ascii=True, indent=2)
            out.write("\n")
        else:
            writer = csv.DictWriter(out, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    finally:
        if out is not sys.stdout:
            out.close()


if __name__ == "__main__":
    main()
