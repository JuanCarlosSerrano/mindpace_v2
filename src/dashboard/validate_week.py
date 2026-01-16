import argparse
import json
import sys

from src.dashboard.weekly_builder import build_weekly_summary
from src.dashboard.weekly_contract import validate_weekly_summary


def run_validate(plan_id: int, iso_week: str):
    summary = build_weekly_summary(plan_id=plan_id, iso_week=iso_week)
    errors = []
    try:
        validate_weekly_summary(summary)
    except ValueError as exc:
        errors = [line for line in str(exc).splitlines() if line.strip()]
    return len(errors) == 0, errors, summary


def main():
    parser = argparse.ArgumentParser(
        description="Validar WeeklySummary (contrato)"
    )
    parser.add_argument("--plan", type=int, required=True)
    parser.add_argument("--week", type=str, required=True)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--print", action="store_true", dest="print_summary")
    args = parser.parse_args()

    ok, errors, summary = run_validate(args.plan, args.week)

    if args.format == "json":
        payload = {
            "ok": ok,
            "plan_id": args.plan,
            "week": args.week,
            "errors": errors,
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        if ok:
            print(f"✅ WeeklySummary válido | plan={args.plan} week={args.week}")
            print(f"keys: {', '.join(summary.keys())}")
        else:
            print(f"❌ WeeklySummary inválido | plan={args.plan} week={args.week}")
            for e in errors:
                print(f"- {e}")

    if args.print_summary:
        print(json.dumps(summary, ensure_ascii=True, indent=2))

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
