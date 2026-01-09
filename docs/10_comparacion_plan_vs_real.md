# Comparacion plan vs real (v1)

## Objetivo
Generar comparaciones planificado vs realizado para alimentar analisis y CoachAI.

## Datos calculados por sesion
- dist_plan_km
- dist_real_km
- pct_dist
- ritmo_plan
- ritmo_real
- delta_ritmo
- sensacion

## Logica de calculo
- pct_dist = dist_real / dist_plan (si dist_plan > 0)
- ritmo_real se calcula desde tiempo/distancia si no existe ritmo_medio
- delta_ritmo = ritmo_real - ritmo_plan

## Idempotencia
Si ya existe comparacion para el par (planificado_id, realizado_id), se actualiza.

## Uso
```bash
python3 -m src.analysis.run_plan_vs_real --plan 2 --atleta 1
python3 -m src.analysis.run_plan_vs_real --plan 2 --atleta 1 --dry-run
python3 -m src.analysis.run_plan_vs_real --plan 2 --atleta 1 --inicio 2026-01-01 --fin 2026-02-01
```

## Resumen semanal (para CoachAI)
Se agrega un resumen de cumplimiento semanal via:
`obtener_resumen_cumplimiento_semanal(...)`
