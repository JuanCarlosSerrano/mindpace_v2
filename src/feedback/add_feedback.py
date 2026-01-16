import argparse
import json
import sys
from datetime import date

from src.feedback.repo import upsert_feedback
from src.db.session import SessionLocal


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    if value.lower() in ("true", "1", "yes", "y"):
        return True
    if value.lower() in ("false", "0", "no", "n"):
        return False
    raise ValueError("pain debe ser true/false")


def main():
    parser = argparse.ArgumentParser(description="Registrar feedback del atleta")
    parser.add_argument("--athlete", type=int, required=True)
    parser.add_argument("--plan", type=int, default=None)
    parser.add_argument("--date", required=True)
    parser.add_argument("--rpe", type=int, default=None)
    parser.add_argument("--mood", type=int, default=None)
    parser.add_argument("--fatigue", type=int, default=None)
    parser.add_argument("--soreness", type=int, default=None)
    parser.add_argument("--pain", default=None)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--json", dest="json_payload", default=None)
    args = parser.parse_args()

    payload = {}
    if args.json_payload:
        try:
            payload.update(json.loads(args.json_payload))
        except json.JSONDecodeError as exc:
            print(f"Error JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    payload.update(
        {
            "rpe": args.rpe,
            "mood": args.mood,
            "fatigue": args.fatigue,
            "soreness": args.soreness,
            "notes": args.notes,
        }
    )

    if args.pain is not None:
        try:
            payload["pain_flag"] = _parse_bool(args.pain)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)

    session = SessionLocal()
    try:
        feedback = upsert_feedback(
            session=session,
            athlete_id=args.athlete,
            plan_id=args.plan,
            session_date=_parse_date(args.date),
            payload=payload,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Feedback registrado | id={feedback.id}")


if __name__ == "__main__":
    main()
