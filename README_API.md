# MindPace v2 API (MVP)

## Arranque

```bash
python3 -m src.api.app
```

O con uvicorn:

```bash
uvicorn src.api.app:app --reload
```

Variables:
- `API_HOST` (default `127.0.0.1`)
- `API_PORT` (default `8000`)

## Endpoints

### Dashboard semanal
```
GET /api/v1/plans/{plan_id}/weeks/{iso_week}
```

Query params:
- `format` = `json|text` (default `json`)
- `validate` = `true|false` (default `true`)

Ejemplo:
```bash
curl http://127.0.0.1:8000/api/v1/plans/2/weeks/2026-W03
```

### Feedback (upsert)
```
POST /api/v1/athletes/{athlete_id}/feedback
```

Body JSON:
```json
{
  "date": "2026-01-15",
  "plan_id": 2,
  "rpe": 8,
  "fatigue": 7,
  "soreness": 3,
  "pain": false,
  "notes": "Piernas cargadas"
}
```

### Coach apply
```
POST /api/v1/plans/{plan_id}/coach/apply
```

Body:
```json
{
  "week": "2026-W03",
  "dry_run": true
}
```

### Coach revert
```
POST /api/v1/plans/{plan_id}/coach/revert
```

Body:
```json
{
  "week": "2026-W03",
  "ids": [10, 11],
  "last": 3,
  "yes": true
}
```
