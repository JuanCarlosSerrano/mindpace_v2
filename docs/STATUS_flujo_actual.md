# 🧠 MindPace v2 — Flujo actualizado end-to-end (Plan ↔ Real ↔ CoachAI)

**Proyecto:** MindPace v2  
**Autor:** Dirección SIGO  
**Estado:** Motor funcional (planificación + import real + matching + comparación + CoachAI + trazabilidad + undo)  
**Versión documento:** 1.0

---

## 1) Flujo completo (end-to-end)

Este es el flujo real actual del motor:

1. Seed DB (datos base)
2. Generación de plan desde plantilla
3. Importación CSV manual de entrenamientos reales
4. Backfill opcional de tipo_sesion en realizados (si falta)
5. Matching heurístico Planificado ↔ Realizado (v1)
6. Generación de Comparación Plan vs Real (v1)
7. CoachAI analiza, recomienda y aplica ajustes
8. Reanálisis (cerrar el bucle)
9. Trazabilidad total: historial, exportación y reversión

---

## 2) Estado verificado del flujo (último reporte)

### 2.1 Seed DB
✅ OK

### 2.2 Generar plan
✅ Plan generado: `plan_id=2` con `25 sesiones planificadas`

### 2.3 Import CSV
✅ insertadas=2, duplicadas=0, vinculadas=2

> Importación CSV valida columnas, rangos, fechas y duplicados internos.

### 2.4 Backfill tipo_sesion (realizados)
⚠️ Actualizados=0, Sin match=1

- Backfill solo actúa si `tipo_sesion IS NULL`
- El “sin match” indica que el texto no permitió inferencia para ese realizado

### 2.5 Matching plan vs real (heurístico)
✅ Vinculados=3  
✅ Conflictos=0

Detalle:
- Real 1 (2026-01-06) ↔ Plan 1 (2026-01-06) | método `fecha` | confianza 1.0 | tipo None
- Real 2 (2026-01-15) ↔ Plan 49 (2026-01-15) | método `fecha` | confianza 1.0 | tipo rodaje
- Real 3 (2026-01-17) ↔ Plan 30 (2026-01-17) | método `fecha` | confianza 1.0 | tipo series

Reglas v1:
- Regla 1: misma fecha → confianza 1.0
- Regla 2: ±1 día + tipo compatible → confianza 0.8
- No sobrescribe vínculos existentes
- Si hay conflicto (múltiples candidatos equivalentes) → no vincula

### 2.6 Comparación plan vs real
✅ Insertados=2, Actualizados=0, Ignorados=1

- El “ignorado” corresponde a un realizado vinculado a un planificado cuyo `plan_id` no coincide con el `plan_id` objetivo de la comparación.
- Política actual: no mezclar planes → se ignora conscientemente para evitar contaminación de métricas.

### 2.7 CoachAI
✅ 10 recomendaciones generadas y aplicadas  
✅ Reanálisis deja 2 recomendaciones (bucle de corrección funcionando)

### 2.8 Historial / Trazabilidad
✅ Acciones registradas en `coach_actions` correctamente  
Incluye:
- before/after por entrenamiento
- borrados
- reversiones
- exportación JSON/CSV
- revertir por semana / IDs / últimas N
- confirmación interactiva + `--yes`
- dry-run
- memoria v2 basada en historial

---

## 3) Conclusión

El motor ya soporta un ciclo completo:

**Planificar → Importar realidad → Vincular → Comparar → Ajustar → Registrar → Revertir**

El sistema es:
- explicable
- auditable
- reversible
- preparado para evolución (APIs, FIT/TCX, UI)

---

## 4) Próximos pasos recomendados

### Prioridad alta
1) Mejorar trazabilidad de “Ignorados” en Comparación plan vs real:
   - devolver detalles y motivo (ej. plan distinto)
2) Añadir métricas de cumplimiento semanal:
   - % volumen cumplido por semana
   - sesiones realizadas vs planificadas
3) Integrar cumplimiento en CoachAI v2:
   - si bajo cumplimiento → suavizar progresión
   - si exceso de intensidad real → descarga anticipada

### Prioridad media
4) Importación FIT/TCX (export original de Strava / Garmin)
5) Dashboard CLI/HTML para visualizar semanas y comparaciones

---
