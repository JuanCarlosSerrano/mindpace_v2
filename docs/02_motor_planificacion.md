# Motor de planificación – Versión 2.0

## Objetivo del motor
El motor de planificación tiene como objetivo generar planes de entrenamiento
personalizados para un atleta concreto, a partir de:

- métodos de entrenamiento contrastados
- parámetros individuales del atleta
- reglas claras y explicables

El motor **no sustituye al entrenador**, sino que automatiza la generación
de una propuesta inicial coherente y segura.

---

## Principios de diseño

- Separación entre conocimiento (plantillas) y decisión (reglas)
- Reglas simples, pequeñas y combinables
- Resultados explicables y ajustables
- Seguridad y progresión como prioridad
- Evolución incremental (sin IA compleja en fases iniciales)

---

## Inputs del motor

### Perfil del atleta
Datos necesarios para personalizar el plan:

- edad
- sexo
- experiencia_anios
- dias_entreno_semana
- volumen_actual_km
- VAM
- ritmo_umbral
- categoria

Estos datos proceden de la entidad `atletas`.

---

### Objetivo deportivo
Define el propósito del plan:

- distancia_objetivo (1500, 3000, 5k, 10k, cross…)
- fecha_objetivo
- prioridad (principal / secundaria)

---

### Preferencias (opcional)
Permiten adaptar el plan sin romper la lógica base:

- dias_descanso_preferidos
- incluir_fuerza (bool)
- nivel_riesgo (conservador | normal | agresivo)

---

## Flujo general del motor

El motor se ejecuta como una tubería de pasos independientes:

1. Normalización del contexto
2. Selección de plantilla base
3. Aplicación de reglas de ajuste
4. Generación del calendario con fechas reales
5. Salida del plan generado

Cada paso puede testearse y evolucionar de forma aislada.

---

## 1. Normalización del contexto

El objetivo de esta fase es transformar valores continuos en categorías
que simplifiquen las reglas.

Ejemplos de normalización:

- edad → grupo_edad (menor / adulto / master)
- volumen_actual_km → nivel_volumen (bajo / medio / alto)
- VAM → nivel_vam (baja / media / alta)

La normalización evita reglas excesivamente complejas y repetitivas.

---

## 2. Selección de plantilla base

A partir del objetivo y del contexto normalizado, se selecciona una
plantilla de planificación genérica.

Ejemplos de criterios:

- distancia_objetivo
- nivel del atleta
- época de la temporada

La plantilla define:
- duración en semanas
- estructura semanal
- tipos de sesiones

No define aún volúmenes ni intensidades finales.

---

## 3. Reglas de ajuste

Las reglas son funciones independientes que modifican el plan base.

### Tipos de reglas

#### Reglas de seguridad
Protegen al atleta de sobrecarga o riesgos innecesarios.

Ejemplos:
- limitar sesiones intensas en menores
- limitar volumen máximo semanal
- introducir semanas de descarga

---

#### Reglas de progresión
Aseguran una evolución gradual del estímulo.

Ejemplos:
- incremento de volumen controlado
- progresión de intensidad
- alternancia carga / descarga

---

#### Reglas de especialización
Adaptan el plan al objetivo concreto.

Ejemplos:
- mayor énfasis en fuerza y desnivel para cross
- mayor volumen de series específicas para 1500
- reducción de volumen previo a competición

---

### Aplicación de reglas

Las reglas se aplican de forma secuencial:

- primero a nivel de semana
- después a nivel de sesión

El orden de las reglas es explícito y controlado.

---

## 4. Generación del calendario

Una vez ajustado el plan por semanas y sesiones, se asignan fechas reales:

- a partir de la fecha de inicio
- respetando días de descanso
- alineando picos con la fecha objetivo

El resultado son entrenamientos planificados con fecha concreta.

---

## 5. Salida del motor

El motor devuelve una estructura de datos con:

- semanas de entrenamiento
- sesiones planificadas
- volúmenes e intensidades finales
- fechas asignadas

El motor **no guarda en base de datos**.
La persistencia se realiza en un módulo independiente.

---

## Relación con el análisis de datos

El motor genera el plan inicial.
El análisis posterior de entrenamientos realizados permitirá:

- evaluar el cumplimiento del plan
- detectar desviaciones
- ajustar reglas o parámetros en el futuro

Esta retroalimentación no modifica el motor base,
sino sus coeficientes y recomendaciones.

---

## Evolución futura hacia IA

En fases posteriores, la IA podrá:

- ajustar parámetros de reglas existentes
- sugerir cambios de carga
- detectar patrones de respuesta al entrenamiento

La IA no creará planes desde cero,
sino que actuará como un sistema de apoyo al motor de reglas.

---

## Conclusión

El motor de planificación es:

- explicable
- seguro
- evolutivo
- basado en conocimiento real

Sirve como núcleo del sistema y como punto de conexión
entre planificación, análisis y mejora continua.
