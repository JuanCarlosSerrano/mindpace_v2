# Matching plan vs real (v1)

## Objetivo
Vincular entrenamientos realizados con planificados usando reglas explicables y seguras.

## Nuevo campo en realizados
Se introduce `tipo_sesion` en `EntrenamientoRealizado` para mejorar el matching.

Uso:
- `tipo_sesion` se rellena desde CSV cuando exista `tipo` o `tipo_sesion`.
- Si no existe, se puede backfillear desde comentarios.

## Backfill de tipo
Script:
```bash
python3 -m src.planning.run_backfill_real_tipo
python3 -m src.planning.run_backfill_real_tipo --atleta 1
python3 -m src.planning.run_backfill_real_tipo --dry-run
```

Reglas de inferencia (desde texto):
- rodaje / easy -> rodaje
- series / intervalos -> series
- tempo -> tempo
- umbral / threshold -> umbral

## Matching v1 (heuristico)
Reglas:
1) Misma fecha -> confianza 1.0, metodo `fecha`
2) Fecha ±1 dia + tipo compatible -> confianza 0.8, metodo `fecha_tipo`

Compatibilidad:
- rodaje ↔ rodaje
- series ↔ series/tempo/intervalos

Restricciones:
- no sobrescribir vinculos existentes
- un planificado solo se vincula una vez
- si hay multiples candidatos, no se vincula

## Runner
```bash
python3 -m src.planning.run_match_real_plan --atleta 1
python3 -m src.planning.run_match_real_plan --atleta 1 --inicio 2026-01-01 --fin 2026-02-01
python3 -m src.planning.run_match_real_plan --atleta 1 --dry-run
```
