# 📥 Importación de Datos Externos (Garmin / Strava / Polar)

**Proyecto:** MindPace v2  
**Autor:** Dirección SIGO  
**Versión:** 1.0  
**Objetivo:** Diseñar un sistema robusto y extensible para importar entrenamientos reales
desde plataformas externas y compararlos con la planificación.

---

## 1. Objetivo general

Permitir que atletas y entrenadores puedan:

- Importar entrenamientos realizados desde plataformas externas
- Normalizar los datos independientemente del proveedor
- Almacenar actividades reales en la base de datos
- Compararlas con los entrenamientos planificados
- Usar estos datos para análisis y decisiones del Entrenador IA

El sistema debe ser **agnóstico del proveedor** y fácilmente ampliable.

---

## 2. Principios de diseño

- **Proveedor-independiente:** Strava, Garmin, Polar, etc.
- **Datos normalizados:** mismo formato interno
- **Evitar duplicados**
- **Escalable:** preparado para nuevas métricas
- **Seguro:** tokens protegidos y aislados
- **Evolutivo:** primero importación simple, luego APIs oficiales

---

## 3. Arquitectura general

El sistema de importación se divide en **tres capas**:

### 3.1 Conectores

Responsables de:

- Autenticarse con el proveedor
- Descargar actividades
- Traducir datos “crudos”

Ejemplos:

- `StravaConnector`
- `GarminConnector`
- `PolarConnector`

---

### 3.2 Normalización

Todos los datos se convierten a un **modelo común interno**.

Ejemplo de estructura normalizada:

'''python
NormalizedActivity(
provider="strava",
external_id="123456789",
fecha=date,
distancia_km=10.2,
tiempo_seg=2450,
ritmo_medio=240,
fc_media=158,
fc_max=175,
desnivel_m=120
)'''

### 3.3 Persistencia

Los datos normalizados se almacenan en la base de datos.

**Tabla principal:** `entrenamientos_realizados`

**Campos clave:**

- `id` – identificador único
- `usuario_id` – referencia al atleta
- `proveedor` – origen (manual, strava, garmin, polar)
- `actividad_id_externa` – ID del proveedor externo
- `fecha` – fecha de la actividad
- `distancia_km` – distancia en kilómetros
- `tiempo_seg` – duración en segundos
- `ritmo_medio` – ritmo promedio
- `fc_media` – frecuencia cardíaca media
- `fc_max` – frecuencia cardíaca máxima
- `desnivel_m` – desnivel acumulado en metros
- `entrenamiento_planificado_id` – referencia opcional a entrenamiento planificado
- `created_at` – timestamp de creación
- `updated_at` – timestamp de actualización

Esta estructura permite:

- Trazabilidad del origen de datos
- Prevención de duplicados
- Vinculación con planes
- Historial completo de actividades reales

actividad_id_externa

métricas de entrenamiento

referencia opcional a entrenamiento planificado

## 4. Autenticación y seguridad

### 4.1 OAuth2 (Strava)

- OAuth2 estándar
- Tokens de acceso y refresh
- Scopes típicos: `activity:read_all`
- Los tokens se almacenan en una tabla dedicada

### 4.2 Garmin y Polar

Garmin y Polar no ofrecen APIs tan abiertas como Strava.

**Estrategia recomendada:**

- **v1:** importación manual de archivos (FIT / TCX / CSV)
- **v2:** integración oficial si se obtiene acceso a API

---

## 5. Modelo de datos adicional

**Tabla:** `integraciones`

Gestiona credenciales externas por usuario.

**Campos:**

- `id` – identificador único
- `usuario_id` – referencia al atleta
- `proveedor` – strava, garmin, polar
- `access_token` – token de acceso
- `refresh_token` – token de renovación
- `expires_at` – expiración del token
- `scope` – permisos autorizados
- `created_at` – timestamp de creación
- `updated_at` – timestamp de actualización

**Beneficios:**

- Múltiples proveedores por usuario
- Renovación automática de tokens
- Revocación segura

---

## 6. Prevención de duplicados

Antes de insertar una actividad:

1. Comprobar proveedor
2. Comprobar `actividad_id_externa`

**Si ya existe:**

- No se vuelve a insertar
- Se ignora o se actualiza según política

**Evita:**

- Duplicados
- Métricas infladas
- Errores de análisis

---

## 7. Vinculación con entrenamiento planificado

Una actividad real puede asociarse a un entrenamiento planificado.

**Heurística inicial (v1):**

- Misma fecha
- Distancia similar (±20%)
- Tipo de sesión compatible
- Selección manual por el usuario

**Si se vincula:**

- Se guarda en tabla de comparación plan vs real
- Se habilitan análisis de cumplimiento

---

## 8. Flujo de importación recomendado (v1)

**Fase 1 – Importación manual**

- CSV, FIT / TCX
- Rápida implementación
- Útil para pruebas y MVP

**Fase 2 – Strava API**

- OAuth2
- Descarga automática de actividades
- Sincronización periódica

**Fase 3 – Garmin / Polar**

- API oficial si es posible
- Alternativa: importación de archivos

---

## 9. Relación con el Entrenador IA

Los datos importados permiten al sistema:

- Evaluar cumplimiento del plan
- Detectar fatiga real
- Ajustar planificación futura
- Aprender de resultados reales
- Generar explicaciones más precisas

Esta capa es clave para una IA entrenadora fiable.

---

## 10. Conclusión

El sistema de importación de datos es un pilar fundamental de MindPace v2.

**Este diseño garantiza:**

- Independencia tecnológica
- Datos limpios y comparables
- Escalabilidad
- Integración directa con análisis y decisiones inteligentes

Sirve como base sólida para evolucionar hacia un sistema de entrenamiento verdaderamente adaptativo.
