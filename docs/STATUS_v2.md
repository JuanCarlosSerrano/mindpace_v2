# 🧠 MindPace v2 — Estado del Proyecto y Flujo de Aplicación

**Proyecto:** MindPace v2  
**Autor:** Dirección SIGO  
**Versión del documento:** 1.0  
**Estado:** Motor funcional con IA explicable y reversible  
**Fecha:** 2026

---

## 1. Visión general

MindPace v2 es un sistema de planificación y análisis de entrenamiento de resistencia
con un **Entrenador IA explicable**, capaz de:

- Generar planes desde plantillas contrastadas
- Analizar carga y tendencia semanal
- Detectar riesgos de progresión
- Proponer ajustes semanales y diarios
- Aplicar ajustes en base de datos
- Registrar cada acción aplicada
- Revertir ajustes de forma granular
- Aprender del historial de decisiones (memoria v2)

El sistema está diseñado para evolucionar progresivamente hacia una IA entrenadora
fiable, auditable y segura.

---

## 2. Flujo general de la aplicación

### 2.1 Flujo completo (alto nivel)


---

## 3. Generación del plan

### Archivo clave
- `src/planning/engine.py`

### Qué hace
- Genera un `PlanAtleta`
- Expande sesiones desde `PlantillaSesion`
- Aplica reglas iniciales:
  - Ajuste por edad
  - Volumen actual
  - VAM
  - Descargas programadas
  - Límites de seguridad (menores, intensidad)

### Salida
- Tabla `entrenamientos_planificados`
- Fechas reales, volumen, ritmo e intensidad inicial

---

## 4. Vista semanal

### Archivo
- `src/planning/week_view.py`

### Función
Agrupa entrenamientos por semana ISO y calcula:
- Número de sesiones
- Volumen total semanal
- Distribución por tipo
- Lista completa de entrenamientos

Esta estructura es la **base de todo el análisis posterior**.

---

## 5. Análisis de carga

### Archivo
- `src/planning/load_analysis.py`

### Métricas calculadas
- Volumen semanal
- Número de sesiones duras
- Índice de carga (volumen + ponderación de intensidad)

### Alertas
- Demasiadas sesiones duras
- Aumento de volumen > 25%
- Subidas repetidas sin descarga

---

## 6. Análisis de tendencia

### Archivo
- `src/planning/trend_analysis.py`

### Qué añade
- Comparación entre semanas consecutivas
- Variación porcentual
- Tendencia visual (subida, bajada, estable)
- Alertas de progresión peligrosa o descargas excesivas

Este módulo es el **detector de riesgo longitudinal**.

---

## 7. CoachAI (núcleo inteligente)

### Archivo
- `src/ai/coach.py`

### Responsabilidades
- Orquestar análisis
- Proponer ajustes semanales
- Proponer ajustes diarios
- Explicar cada recomendación

### Características clave
- Totalmente explicable
- Basado en reglas (v1)
- Preparado para ML/IA futura
- Bloquea semanas ya ajustadas recientemente
- Usa memoria de acciones previas

---

## 8. Aplicación de ajustes

### Archivo
- `src/ai/apply_recommendations.py`

### Qué hace
Aplica **realmente en BD** los ajustes propuestos:

#### Ajustes semanales
- Reducción exacta de volumen (factor calculado)
- Eliminación de sesiones duras
- Marcado de semanas de descarga
- Reducción de intensidad

#### Ajustes diarios
- Reducción puntual de volumen
- Ritmos más conservadores

### Seguridad
- Validadores en modelos (cortafuegos de volumen)
- Precisión Decimal
- Snapshot before/after por sesión

---

## 9. Persistencia y trazabilidad

### Archivos
- `src/ai/coach_actions.py`
- `src/db/models.py`

### Qué se registra
Cada acción guarda:
- Tipo (semanal / diaria / reversión)
- Semana afectada
- Lista de entrenamientos tocados
- Before / After por campo
- Borrados realizados
- Timestamp
- Origen (CoachAI / usuario)

Esto permite:
- Auditoría completa
- Explicabilidad
- Reversión exacta

---

## 10. Reversión (Undo)

### Archivo
- `src/ai/run_revert.py`

### Modos soportados
- Revertir por semana
- Revertir por IDs de acción
- Revertir últimas N acciones
- Confirmación interactiva
- Flag `--yes` para automatización
- Dry-run (simulación sin cambios)

### Garantía
La reversión es **precisa, segura y trazable**.

---

## 11. Historial y exportación

### Archivo
- `src/ai/run_history.py`

### Funciones
- Listar acciones por plan
- Filtrar por semana
- Limitar número de registros
- Exportar a:
  - Texto
  - JSON
  - CSV

Pensado para:
- Análisis externo
- Informes
- Integración futura con frontend

---

## 12. Memoria del Coach (v2)

### Implementación
- Basada en `coach_actions`
- Ventana temporal (ej. 21 días)

### Comportamiento
- Reduce agresividad tras reversiones
- Evita repetir ajustes en la misma semana
- Prioriza intensidad sobre volumen si hay inestabilidad
- Simula “prudencia” del entrenador humano

---

## 13. Estado actual del sistema

### ✅ Completado
- Generación de planes
- Análisis semanal y tendencia
- CoachAI explicable
- Aplicación real de ajustes
- Persistencia y trazabilidad
- Reversión granular
- Exportación de historial
- Memoria de decisiones

### ❌ Aún no incluido
- Frontend
- Importación automática de Garmin/Strava
- ML basado en datos reales
- Feedback subjetivo avanzado

---

## 14. Próximos pasos recomendados

### Prioridad alta
1. Importación v1 de entrenamientos reales (CSV)
2. Comparación planificado vs realizado
3. Métricas de cumplimiento y fatiga

### Prioridad media
4. Dashboard semanal (CLI o web)
5. Configuración externa de reglas (YAML/JSON)
6. Ajustes progresivos multi-semana

### Prioridad futura
7. Modelo ML de predicción de carga
8. Integración con APIs externas
9. Frontend entrenador/atleta

---

## 15. Conclusión

MindPace v2 ya es:

- Un **motor de planificación inteligente**
- Con **decisiones explicables**
- **Reversibles**
- **Auditables**
- Y preparado para evolucionar hacia IA real

El núcleo está sólido.  
A partir de aquí, todo lo que se añada es crecimiento, no refactor.

---

