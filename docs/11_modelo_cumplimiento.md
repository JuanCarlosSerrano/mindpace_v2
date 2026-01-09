# 📊 Modelo de Cumplimiento Plan vs Real (v1)

**Proyecto:** MindPace v2  
**Autor:** Dirección SIGO  
**Estado:** Diseño funcional alineado con motor actual  
**Objetivo:** Medir cómo el atleta ejecuta el plan y usarlo para ajustar decisiones del CoachAI.

---

## 1. Qué es el cumplimiento

El **cumplimiento** mide la relación entre:

> **Lo que estaba planificado**  
> **vs**  
> **Lo que realmente se hizo**

No busca “castigar”, sino:
- detectar desviaciones relevantes
- entender causas (fatiga, exceso, falta de tiempo)
- adaptar la planificación futura

---

## 2. Nivel de análisis

El cumplimiento se evalúa en **tres niveles**:

1. **Sesión**
2. **Semana**
3. **Histórico (tendencia)**

La v1 se centra en **sesión y semana**, dejando histórico para v2.

---

## 3. Cumplimiento por sesión

Cada sesión planificada puede tener:
- 0 o 1 entrenamiento real vinculado (v1)
- o ninguno (no realizada)

### 3.1 Métricas por sesión

| Métrica | Descripción |
|------|------------|
| `realizada` | boolean |
| `volumen_ratio` | real_km / plan_km |
| `ritmo_diff` | real_ritmo − plan_ritmo (s/km) |
| `tipo_coincide` | mismo tipo_sesion |
| `confianza_match` | heredada del matching |
| `sensacion` | RPE si existe |

---

### 3.2 Clasificación de sesión (v1)

#### Volumen
- ✅ **Correcto:** 0.9 ≤ ratio ≤ 1.1
- ⚠️ **Corto:** ratio < 0.9
- 🚨 **Exceso:** ratio > 1.2

#### Intensidad (si hay ritmo objetivo)
- ✅ Dentro de ±5%
- ⚠️ Leve desviación
- 🚨 Muy rápido / muy lento

---

### 3.3 Resultado de sesión

Cada sesión se clasifica como:

- `cumplida`
- `subcumplida`
- `excesiva`
- `no_realizada`
- `no_evaluable` (datos insuficientes)

Este resultado es **explicable** y auditable.

---

## 4. Cumplimiento semanal

La semana es la **unidad principal de decisión** para el CoachAI.

### 4.1 Métricas semanales

| Métrica | Descripción |
|------|------------|
| `sesiones_planificadas` | nº |
| `sesiones_realizadas` | nº |
| `ratio_sesiones` | realizadas / planificadas |
| `volumen_planificado` | km |
| `volumen_real` | km |
| `ratio_volumen` | real / plan |
| `sesiones_excesivas` | nº |
| `sesiones_no_realizadas` | nº |

---

### 4.2 Clasificación semanal (v1)

| Estado | Condición |
|-----|---------|
| 🟢 **Cumplida** | ratio_volumen 0.9–1.1 y ≥80% sesiones |
| 🟡 **Parcial** | ratio 0.7–0.9 o sesiones faltantes |
| 🔴 **Bajo cumplimiento** | ratio <0.7 |
| 🚨 **Exceso** | ratio >1.2 o muchas sesiones excesivas |

---

## 5. Uso del cumplimiento en CoachAI

El cumplimiento **modula** las decisiones del CoachAI.

### 5.1 Reglas v1 (deterministas)

#### Bajo cumplimiento
- ❌ No subir volumen
- ❌ No añadir sesiones duras
- ✅ Simplificar semanas futuras
- ✅ Reducir intensidad antes que volumen

#### Exceso de cumplimiento
- 🚨 Riesgo de sobrecarga
- ✅ Forzar descarga anticipada
- ✅ Reducir sesiones duras

#### Cumplimiento estable
- ✅ Permitir progresión normal
- ✅ Mantener estructura del plan

---

## 6. Relación con el sistema actual

El modelo encaja directamente con lo ya implementado:

- Usa `ComparacionPlanReal`
- Usa matching existente
- Se integra antes de:
  - `analizar_carga_semanal`
  - `analizar_tendencia_semanal`
- Sus resultados alimentan:
  - `ajustar_plan_semanal`
  - `ajustar_entrenamientos_diarios`

No rompe nada existente.

---

## 7. Decisiones explícitas de diseño (v1)

- ❌ No se mezclan planes distintos
- ❌ No se pondera aún por importancia de sesión
- ❌ No se usa IA probabilística
- ❌ No se aprende automáticamente

Todo es:
- explicable
- reversible
- auditable

---

## 8. Evolución prevista (v2)

- Peso por tipo de sesión (series > rodaje)
- Historial de cumplimiento (rolling 4–6 semanas)
- Confianza dinámica del matching
- Ajustes predictivos
- Aprendizaje por atleta

---

## 9. Conclusión

El modelo de cumplimiento convierte a MindPace de:

> **“Generador de planes”**  
en  
> **“Entrenador que observa, entiende y corrige”**

Es el puente entre planificación, realidad y decisiones inteligentes.

---
