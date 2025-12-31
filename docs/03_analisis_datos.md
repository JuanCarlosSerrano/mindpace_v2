# Análisis de datos de entrenamiento – Versión 2.0

## Objetivo del análisis
El módulo de análisis tiene como objetivo transformar los datos reales
de entrenamiento en información útil para:

- evaluar el cumplimiento del plan
- detectar tendencias de rendimiento o fatiga
- apoyar la toma de decisiones del entrenador
- alimentar ajustes futuros de la planificación

El análisis **no sustituye al criterio humano**, lo complementa.

---

## Principios del análisis

- Priorizar métricas comprensibles frente a métricas complejas
- Analizar siempre en relación con lo planificado
- Diferenciar señal (tendencias) de ruido (variabilidad diaria)
- Mantener trazabilidad entre datos, métricas y decisiones
- Preparar el terreno para IA explicable

---

## Fuentes de datos

### Entrenamientos realizados
Datos registrados manualmente o importados de plataformas externas:

- distancia
- tiempo
- ritmo
- frecuencia cardíaca
- desnivel
- sensaciones subjetivas

Estos datos representan la **realidad del entrenamiento**.

---

### Entrenamientos planificados
Datos generados por el motor de planificación:

- volumen objetivo
- ritmo objetivo
- tipo de sesión
- estructura de series

La comparación entre ambos es el eje del análisis.

---

## Comparación planificado vs realizado

La comparación permite medir el grado de cumplimiento del plan.

### Métricas básicas

- Cumplimiento de volumen (%)
- Cumplimiento de ritmo (%)
- Desviación absoluta y relativa
- Estado de la sesión (ok / ajustada / fallida)

Estas métricas se almacenan en la entidad `comparacion_plan_real`.

---

## Métricas de carga

El sistema calculará métricas agregadas por periodo (normalmente semanal).

Ejemplos:

- volumen total semanal
- número de sesiones intensas
- distribución de tipos de sesión
- carga relativa respecto a semanas anteriores

Estas métricas permiten detectar:
- aumentos bruscos de carga
- semanas excesivamente exigentes
- falta de estímulo suficiente

---

## Métricas de fatiga

La fatiga se estima combinando varias señales:

- acumulación de carga
- desviaciones repetidas del ritmo objetivo
- sensaciones subjetivas del atleta
- variabilidad de resultados recientes

El objetivo no es una cifra exacta,
sino una **estimación orientativa y coherente**.

---

## Tendencias de rendimiento

El análisis busca detectar tendencias, no resultados aislados.

Ejemplos:

- mejora progresiva del ritmo a igual carga
- estancamiento prolongado
- empeoramiento tras aumentos de volumen

Las tendencias se calculan sobre ventanas temporales
(semanas o bloques), no sesiones individuales.

---

## Alertas y señales relevantes

A partir de las métricas se generan señales simples:

- alerta de sobrecarga
- alerta de estancamiento
- alerta de bajo cumplimiento

Estas alertas:
- no modifican datos automáticamente
- se presentan como información al entrenador
- pueden generar recomendaciones futuras

---

## Visualización de datos

El sistema prioriza visualizaciones claras:

- evolución temporal de volumen y ritmo
- comparación plan vs real
- distribución de tipos de sesión
- indicadores de carga y fatiga

Las gráficas deben responder preguntas concretas,
no mostrar datos por mostrar.

---

## Relación con el motor de planificación

El análisis sirve como retroalimentación del sistema:

- valida la eficacia del plan
- detecta desviaciones sistemáticas
- sugiere ajustes de reglas o parámetros

El análisis **no reescribe el plan automáticamente**
en fases iniciales.

---

## Preparación para IA futura

Este módulo deja preparados los datos para:

- detección automática de patrones
- ajuste dinámico de coeficientes
- recomendaciones personalizadas

La IA utilizará métricas ya calculadas,
no datos crudos directamente.

---

## Conclusión

El análisis de datos es el puente entre:

- lo que se planifica
- lo que se ejecuta
- lo que se aprende

Un análisis bien diseñado permite mejorar la planificación
sin perder control ni explicabilidad.
