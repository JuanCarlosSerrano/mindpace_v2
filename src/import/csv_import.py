from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import EntrenamientoRealizado, PlanAtleta
from src.planning.backfill_real_tipo import inferir_tipo_desde_texto

DATABASE_URL = "sqlite:///mindpace_dev.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

REQUIRED_COLUMNS = {"fecha", "distancia_km", "tiempo_seg"}
MIN_RITMO_SEG = 120
MAX_RITMO_SEG = 600
ALLOWED_TIPOS = {"rodaje", "series", "tempo", "umbral"}


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_int(value: str) -> int | None:
    if value == "" or value is None:
        return None
    return int(float(value))


def _parse_decimal(value: str) -> Decimal | None:
    if value == "" or value is None:
        return None
    return Decimal(str(value))


def _parse_time_to_sec(value: str) -> int | None:
    if value == "" or value is None:
        return None
    raw = value.strip()
    if ":" not in raw:
        return int(float(raw))
    parts = [int(p) for p in raw.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    return None


def _row_dict(row: dict) -> dict:
    return {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def _pick(row: dict, *keys: str) -> str | None:
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def _parse_tipo(value: str | None) -> str | None:
    if not value:
        return None
    t = value.strip().lower()
    alias = {
        "easy": "rodaje",
        "intervalos": "series",
        "threshold": "umbral",
    }
    return alias.get(t, t)


def _is_duplicate(
    session,
    atleta_id: int,
    origen: str,
    actividad_id_externa: str | None,
    fecha: date,
    distancia_km: Decimal | None,
    tiempo_seg: int | None,
) -> bool:
    q = session.query(EntrenamientoRealizado).filter(
        EntrenamientoRealizado.atleta_id == atleta_id,
        EntrenamientoRealizado.fecha == fecha,
    )
    if actividad_id_externa:
        q = q.filter(
            EntrenamientoRealizado.origen == origen,
            EntrenamientoRealizado.actividad_id_externa == actividad_id_externa,
        )
        return session.query(q.exists()).scalar()

    if distancia_km is not None:
        q = q.filter(EntrenamientoRealizado.distancia_km == distancia_km)
    if tiempo_seg is not None:
        q = q.filter(EntrenamientoRealizado.tiempo_seg == tiempo_seg)
    if distancia_km is None and tiempo_seg is None:
        return False
    return session.query(q.exists()).scalar()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--atleta", type=int, default=None)
    parser.add_argument("--plan", type=int, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    session = Session()

    atleta_id = args.atleta
    if args.plan and atleta_id is None:
        plan = session.get(PlanAtleta, args.plan)
        if plan is None:
            raise SystemExit("Plan no encontrado")
        atleta_id = plan.atleta_id

    if atleta_id is None:
        raise SystemExit("Debes indicar --atleta o --plan")

    insertadas = 0
    duplicadas = 0
    vinculadas = 0

    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("CSV sin cabeceras")

        headers = {h.strip().lower() for h in reader.fieldnames if h}
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise SystemExit(
                f"Faltan columnas obligatorias: {', '.join(sorted(missing))}"
            )

        seen = set()
        errores = []
        rows = []
        for idx, raw in enumerate(reader, start=2):
            row = _row_dict(raw)

            fecha_raw = _pick(row, "fecha", "date")
            fecha = _parse_date(fecha_raw or "")
            if fecha is None:
                msg = f"Linea {idx}: fecha invalida"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue

            origen = (_pick(row, "origen", "source") or "manual").lower()
            actividad_id_externa = _pick(row, "actividad_id_externa", "actividad_id", "external_id")

            distancia_km = _parse_decimal(_pick(row, "distancia_km", "distancia", "distance"))
            tiempo_seg = _parse_time_to_sec(_pick(row, "tiempo_seg", "tiempo", "duracion", "duration"))
            ritmo_medio = _parse_time_to_sec(_pick(row, "ritmo_medio", "ritmo", "pace"))

            if distancia_km is None or distancia_km <= 0:
                msg = f"Linea {idx}: distancia_km debe ser > 0"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue
            if tiempo_seg is None or tiempo_seg <= 0:
                msg = f"Linea {idx}: tiempo_seg debe ser > 0"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue

            fc_media = _parse_int(_pick(row, "fc_media", "hr_avg"))
            if fc_media is not None and not (80 <= fc_media <= 210):
                msg = f"Linea {idx}: fc_media fuera de rango (80-210)"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue

            if ritmo_medio is not None and not (MIN_RITMO_SEG <= ritmo_medio <= MAX_RITMO_SEG):
                msg = f"Linea {idx}: ritmo_medio fuera de rango ({MIN_RITMO_SEG}-{MAX_RITMO_SEG} s/km)"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue

            sensacion = _parse_int(_pick(row, "sensacion", "rpe"))
            if sensacion is not None and not (1 <= sensacion <= 10):
                msg = f"Linea {idx}: sensacion fuera de rango (1-10)"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue

            key = (fecha.isoformat(), str(distancia_km), str(tiempo_seg))
            if key in seen:
                msg = f"Linea {idx}: duplicado en CSV"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue
            seen.add(key)

            comentario = _pick(row, "comentario", "comentarios", "notes")
            tipo_sesion = _parse_tipo(_pick(row, "tipo_sesion", "tipo"))
            if not tipo_sesion:
                tipo_sesion = inferir_tipo_desde_texto(comentario or "")
            if tipo_sesion is not None and tipo_sesion not in ALLOWED_TIPOS:
                msg = f"Linea {idx}: tipo_sesion invalido ({tipo_sesion})"
                if args.strict:
                    raise SystemExit(msg)
                errores.append(msg)
                continue

            rows.append(
                {
                    "fecha": fecha,
                    "origen": origen,
                    "tipo_sesion": tipo_sesion,
                    "actividad_id_externa": actividad_id_externa,
                    "distancia_km": distancia_km,
                    "tiempo_seg": tiempo_seg,
                    "ritmo_medio": ritmo_medio,
                    "fc_media": fc_media,
                    "fc_max": _parse_int(_pick(row, "fc_max", "hr_max")),
                    "desnivel_m": _parse_int(_pick(row, "desnivel_m", "elev")),
                    "sensacion": sensacion,
                    "comentarios": comentario,
                }
            )

        if errores:
            msg = "Errores en CSV:\n" + "\n".join(errores[:20])
            raise SystemExit(msg)

        for row in rows:
            if _is_duplicate(
                session,
                atleta_id,
                row["origen"],
                row["actividad_id_externa"],
                row["fecha"],
                row["distancia_km"],
                row["tiempo_seg"],
            ):
                duplicadas += 1
                continue

            entreno = EntrenamientoRealizado(
                atleta_id=atleta_id,
                fecha=row["fecha"],
                origen=row["origen"],
                tipo_sesion=row["tipo_sesion"],
                actividad_id_externa=row["actividad_id_externa"],
                distancia_km=row["distancia_km"],
                tiempo_seg=row["tiempo_seg"],
                ritmo_medio=row["ritmo_medio"],
                fc_media=row["fc_media"],
                fc_max=row["fc_max"],
                desnivel_m=row["desnivel_m"],
                sensacion=row["sensacion"],
                comentarios=row["comentarios"],
            )
            session.add(entreno)
            session.flush()
            insertadas += 1

            if args.plan:
                vinculadas += 1

    session.commit()

    print(
        "✅ Importación CSV completada | "
        f"insertadas={insertadas} duplicadas={duplicadas} vinculadas={vinculadas}"
    )


if __name__ == "__main__":
    main()
