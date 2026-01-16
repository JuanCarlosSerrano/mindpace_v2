up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec -T -e PYTHONPATH=/app api python /app/scripts/migrate.py

seed:
	docker compose exec api python3 -m src.fixtures.seed_data

smoke:
	docker compose exec api python3 -m src.dashboard.validate_week --plan 1 --week 2026-W03 --format json

fullflow:
	docker compose exec api python3 -m src.fixtures.seed_data
	docker compose exec api python3 -m src.planning.run_generate_plan
	docker compose exec api python3 -m src.import.csv_import --csv /app/docs/examples/mindpace_csv_v1_example.csv --plan 2
	docker compose exec api python3 -m src.planning.run_backfill_real_tipo
	docker compose exec api python3 -m src.planning.run_match_real_plan --atleta 1 --plan 2
	docker compose exec api python3 -m src.analysis.run_plan_vs_real --plan 2 --atleta 1
	docker compose exec api python3 -m src.analysis.run_cumplimiento --plan 2 --atleta 1
	docker compose exec api python3 -m src.ai.run_apply
	docker compose exec api python3 -m src.dashboard.validate_week --plan 2 --week 2026-W03 --format json
