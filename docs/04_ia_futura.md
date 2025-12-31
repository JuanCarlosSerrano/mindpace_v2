# Inteligencia Artificial – Versión 2.0

## Propósito de la IA en el sistema
La Inteligencia Artificial en este proyecto tiene un objetivo claro:

> **Asistir al entrenador en la toma de decisiones**,  
> utilizando datos reales de entrenamiento y planificación.

La IA **no sustituye al entrenador**,  
no toma decisiones finales  
y no actúa de forma automática sin supervisión.

---

## Principios fundamentales

- IA explicable: cada recomendación debe poder justificarse
- IA progresiva: se introduce por fases, no de forma abrupta
- IA basada en datos reales, no en supuestos teóricos
- IA como apoyo, no como autoridad
- Seguridad del atleta como prioridad absoluta

---

## Qué NO hará la IA

Desde el diseño inicial, quedan explícitamente fuera:

- Crear planes completos desde cero sin reglas base
- Modificar entrenamientos sin intervención humana
- Tomar decisiones opacas tipo “caja negra”
- Priorizar rendimiento sobre salud
- Sustituir el criterio del entrenador

Estas limitaciones son una decisión consciente del diseño.

---

## Qué SÍ hará la IA (de forma progresiva)

### 1. Detección de patrones
La IA analizará históricos de entrenamiento para identificar:

- respuestas positivas o negativas a ciertos estímulos
- estancamientos prolongados
- mejoras rápidas no esperadas
- acumulación de fatiga

Estas detecciones se presentan como información,
no como acciones automáticas.

---

### 2. Recomendaciones asistidas
A partir de métricas y patrones, la IA podrá sugerir:

- reducir o aumentar carga
- introducir semanas de descarga
- ajustar intensidades
- modificar distribución de sesiones

Las recomendaciones tendrán:
- descripción clara
- nivel de confianza
- justificación basada en datos

---

### 3. Ajuste de parámetros del motor
La IA no cambia el motor de reglas,
pero puede sugerir ajustes en:

- coeficientes de progresión
- límites de carga
- tolerancia a desviaciones

Esto permite personalización sin romper el sistema base.

---

## Tipos de IA previstos

### IA basada en reglas (fase inicial)
- Reglas dinámicas
- Umbrales adaptativos
- Lógica explicable

Es la base y puede convivir siempre con el sistema.

---

### IA estadística / ML ligero (fase intermedia)
- modelos de regresión
- clasificación simple
- detección de anomalías

Aplicada sobre métricas ya calculadas,
no sobre datos crudos.

---

### IA avanzada (fase futura)
Solo si se cumplen estas condiciones:
- suficiente volumen de datos
- validación clara de utilidad
- mantenimiento de explicabilidad

Nunca será obligatoria para el funcionamiento del sistema.

---

## Relación con otros módulos

La IA se apoya en:

- métricas del módulo de análisis
- comparaciones plan vs real
- histórico del atleta

La IA **no accede directamente a los datos brutos**
sin pasar por el análisis previo.

---

## Control humano

Toda recomendación generada por IA:

- puede aceptarse o rechazarse
- queda registrada
- no se aplica automáticamente

El entrenador mantiene siempre el control final.

---

## Evaluación de la IA

La eficacia de la IA se evaluará por:

- coherencia de las recomendaciones
- reducción de errores de planificación
- mejora del cumplimiento del plan
- percepción de utilidad por el entrenador

No por complejidad técnica.

---

## Evolución controlada

La introducción de IA se hará de forma incremental:

- primero como observadora
- luego como asesora
- nunca como decisora autónoma

Este enfoque garantiza estabilidad y confianza.

---

## Conclusión

La IA en este proyecto es:

- una herramienta
- un apoyo
- un sistema de aprendizaje

Nunca un sustituto del conocimiento humano.

Su valor reside en **mejorar decisiones**,  
no en tomar decisiones por sí misma.
