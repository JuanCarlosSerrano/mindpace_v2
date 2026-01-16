import argparse
import json
import sys

from src.dashboard.serializers import serialize_week_json, serialize_week_text
from src.dashboard.weekly_builder import build_weekly_summary
from src.dashboard.weekly_contract import validate_weekly_summary


def run(plan_id: int, iso_week: str, fmt: str, validate: bool):
    summary = build_weekly_summary(plan_id=plan_id, iso_week=iso_week)

    if validate:
        try:
            validate_weekly_summary(summary)
        except ValueError as exc:
            errors = [line for line in str(exc).splitlines() if line.strip()]
            msg = f"❌ WeeklySummary inválido | plan={plan_id} week={iso_week}"
            stderr = "\n".join([msg] + [f"- {e}" for e in errors])
            return 1, "", stderr
        else:
            ok_msg = f"✅ WeeklySummary válido | plan={plan_id} week={iso_week}"
            stderr = ok_msg
    else:
        stderr = ""

    if fmt == "json":
        content = json.dumps(
            serialize_week_json(summary),
            indent=2,
            ensure_ascii=False,
        )
    else:
        content = serialize_week_text(summary)

    return 0, content, stderr


def main():
    parser = argparse.ArgumentParser(
        description="Dashboard semanal MindPace v2"
    )
    parser.add_argument("--plan", type=int, required=True)
    parser.add_argument("--week", type=str, required=True)
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    parser.add_argument("--output", default=None)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    exit_code, stdout, stderr = run(
        plan_id=args.plan,
        iso_week=args.week,
        fmt=args.format,
        validate=args.validate,
    )

    if stderr:
        print(stderr, file=sys.stderr)

    if exit_code != 0:
        sys.exit(exit_code)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(stdout)
    else:
        print(stdout)


if __name__ == "__main__":
    main()
