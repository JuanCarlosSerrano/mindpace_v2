# Modelo de datos – Versión 2.0

## Objetivo del modelo
Definir una estructura de datos clara que permita:

- separar planificación y ejecución real del entrenamiento
- analizar la respuesta del atleta al plan
- facilitar ajustes progresivos y explicables
- servir de base para análisis e IA futura

El modelo prioriza la claridad conceptual sobre la complejidad técnica.

---

## Principios de diseño

- Separación estricta entre datos planificados y realizados
- Histórico inmutable de entrenamientos realizados
- Datos deportivos desacoplados de usuarios y autenticación
- Preparado para análisis temporal y comparaciones
- Escalable sin romper compatibilidad

---

## 1. Usuarios y roles

### usuarios
Representa a las personas que acceden al sistema.

Campos:
- id
- email
- password_hash
- rol (admin | entrenador | atleta)
- activo
- fecha_alta

Notas:
- No contiene datos deportivos
- Un usuario con rol atleta tendrá un registro asociado en la tabla atletas

---

## 2. Perfil deportivo del atleta

### atletas
Contiene la información deportiva necesaria para planificar y analizar.

Campos:
- id
- usuario_id (FK usuarios)
- entrenador_id (FK usuarios)

- fecha_nacimiento
- sexo
- altura_cm
- peso_kg

- experiencia_anios
- dias_entreno_semana

- volumen_actual_km
- vam
- ritmo_umbral

- categoria (sub16, sub18, sub20, absoluto, master…)

Notas:
- Estos campos son inputs directos del motor de planificación
- No se guardan aquí datos históricos de entrenamiento

---

## 3. Plantillas de planificación (conocimiento experto)

### plantillas_plan
Define estructuras base reutilizables.

Campos:
- id
- nombre
- descripcion
- distancia_objetivo (1500, 3000, 5k, 10k, cross…)
- nivel (base, intermedio, avanzado)
- duracion_semanas
- metodo (tradicional, polarizado, bloques…)

Notas:
- No tiene fechas reales
- No está asociada a un atleta concreto

---

### plantillas_sesiones
Define las sesiones tipo dentro de una plantilla.

Campos:
- id
- plantilla_id (FK plantillas_plan)
- semana
- dia_semana (1-7)

- tipo_sesion (rodaje, series, fuerza, descanso)
- volumen_base
- intensidad_pct_vam
- formato_series (ej: 6x400)
- recuperacion_seg

Notas:
- Representa conocimiento estructural
- Será ajustado por el motor de reglas

---

## 4. Planificación aplicada a un atleta

### planes_atleta
Instancia real de una planificación para un atleta.

Campos:
- id
- atleta_id
- plantilla_id

- fecha_inicio
- fecha_fin
- objetivo_descripcion

- estado (activo, completado, cancelado)

Notas:
- Un atleta puede tener varios planes a lo largo del tiempo
- Solo uno debería estar activo

---

### entrenamientos_planificados
Entrenamientos concretos con fecha real.

Campos:
- id
- plan_id
- fecha

- tipo_sesion
- volumen_objetivo
- ritmo_objetivo
- detalle_series

- comentarios_entrenador

Notas:
- Resultado final del motor de planificación
- No se edita automáticamente tras ser generado

---

## 5. Entrenamientos realizados

### entrenamientos_realizados
Datos reales del entrenamiento, manuales o importados.

Campos:
- id
- atleta_id
- fecha

- origen (manual | strava | garmin | polar)
- actividad_id_externa

- distancia_km
- tiempo_seg
- ritmo_medio
- fc_media
- fc_max
- desnivel_m

- sensacion (escala 1–10)
- comentarios

Notas:
- Nunca se borran ni sobrescriben
- Representan la “realidad” del entrenamiento

---

## 6. Relación planificado vs realizado

### comparacion_plan_real
Relaciona lo previsto con lo ejecutado.

Campos:
- id
- entrenamiento_planificado_id
- entrenamiento_realizado_id

- cumplimiento_pct
- desviacion_volumen
- desviacion_ritmo

- estado (ok | ajustado | fallido)

Notas:
- Clave para análisis y futuras decisiones automáticas
- Puede recalcularse si cambian métricas

---

## 7. Métricas y análisis

### metricas_atleta
Métricas agregadas por fecha o periodo.

Campos:
- id
- atleta_id
- fecha

- carga_semanal
- fatiga_estimada
- tendencia_rendimiento
- riesgo_lesion

Notas:
- Datos derivados, no editables manualmente
- Base para alertas y recomendaciones

---

## 8. Recomendaciones y ajustes (futuro)

### recomendaciones
Sugerencias generadas por reglas o IA.

Campos:
- id
- atleta_id
- fecha

- tipo (bajar_carga, subir_intensidad, descanso…)
- descripcion
- nivel_confianza

- aplicada (bool)

Notas:
- No modifica datos automáticamente
- Siempre supervisada por el entrenador

---

## Relación conceptual entre entidades

USUARIO
 └── ATLETA
      └── PLAN
           └── ENTRENAMIENTO_PLANIFICADO
                └── COMPARACIÓN
                     └── ENTRENAMIENTO_REALIZADO

---

## Conclusión

Este modelo permite:
- planificar con rigor
- analizar con sentido
- evolucionar hacia sistemas inteligentes
sin perder trazabilidad ni control humano.
