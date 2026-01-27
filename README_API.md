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

### Catálogo de plantillas
```
GET /api/v1/templates
```

Query params:
- `q`
- `goal`
- `level`
- `min_weeks`
- `max_weeks`
- `tag` (repetible)
- `sort` = `updated|load|duration|name`
- `limit`, `offset`

Ejemplo:
```bash
curl "http://127.0.0.1:8000/api/v1/templates?goal=10k&tag=series"
```

```
GET /api/v1/templates/{template_id}
```

```
GET /api/v1/templates/meta
```

### Crear plantilla (MVP editor)
```
POST /api/v1/templates
```

Body JSON (ejemplo):
```json
{
  "name": "Base 6 semanas",
  "goal": "base",
  "level": "intermedio",
  "duration_weeks": 6,
  "tags": ["rodaje", "base"],
  "sessions": [
    { "week": 1, "day_of_week": 2, "tipo_sesion": "rodaje", "volumen_base": 8 }
  ]
}
```

### Generar plan desde plantilla
```
POST /api/v1/templates/{template_id}/generate
```

Body JSON:
```json
{
  "athlete_id": 1,
  "start_date": "2026-01-05",
  "objetivo_descripcion": "Plan generado desde plantilla"
}
```

### Biblioteca de sesiones
```
GET /api/v1/sessions
```

Query params:
- `q`
- `tipo`
- `tag` (repetible)
- `sort` = `updated|name|load`
- `limit`, `offset`

```
GET /api/v1/sessions/{session_id}
```

```
POST /api/v1/sessions
```

```
PUT /api/v1/sessions/{session_id}
```

```
DELETE /api/v1/sessions/{session_id}
```

Body JSON (ejemplo):
```json
{
  "name": "Series 4x1000",
  "tipo_sesion": "series",
  "volumen_base": 8,
  "intensidad_pct_vam": 0.9,
  "formato_series": "4x1000",
  "recuperacion_seg": 120,
  "tags": ["series", "velocidad"],
  "blocks": [
    { "type": "warmup", "target": "distance", "value": 2, "unit": "km" },
    {
      "type": "repeat",
      "reps": 4,
      "steps": [
        {
          "type": "interval",
          "target": "distance",
          "value": 1000,
          "unit": "m",
          "zone": "Z4",
          "recovery_sec": 120
        }
      ]
    },
    { "type": "cooldown", "target": "distance", "value": 2, "unit": "km" }
  ]
}
```

### Presets de sesión por entrenador
```
GET /api/v1/session-presets?entrenador_id=1
```

```
POST /api/v1/session-presets
```

```
PUT /api/v1/session-presets/{preset_id}?entrenador_id=1
```

```
DELETE /api/v1/session-presets/{preset_id}?entrenador_id=1
```

Body JSON (ejemplo):
```json
{
  "entrenador_id": 1,
  "label": "4x1000 VAM",
  "tipo_sesion": "series",
  "volumen_base": 8,
  "intensidad_pct_vam": 0.9,
  "formato_series": "4x1000",
  "recuperacion_seg": 120,
  "tags": ["series", "velocidad"]
}
```
