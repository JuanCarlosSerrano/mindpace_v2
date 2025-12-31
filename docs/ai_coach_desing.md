# 🧠 Entrenador IA – Diseño y Arquitectura (Versión 1.0)

**Proyecto:** MindPace v2  
**Autor:** Dirección SIGO  
**Objetivo:** Definir la arquitectura y el funcionamiento de un entrenador digital inteligente,
explicable y orientado al rendimiento deportivo.

---

## 1. Introducción

El Entrenador IA de MindPace no pretende sustituir al entrenador humano, sino actuar como un
**copiloto inteligente**, capaz de:

- Analizar planes de entrenamiento
- Detectar riesgos y desequilibrios
- Proponer ajustes razonados
- Explicar cada decisión de forma clara

Este diseño prioriza la **explicabilidad**, la **progresión segura** y la **coherencia deportiva**.

---

## 2. Principios de diseño

El sistema se rige por los siguientes principios:

- **Explicabilidad:** ninguna decisión es opaca
- **Progresividad:** evitar cambios bruscos no justificados
- **Criterio deportivo:** basado en métodos contrastados
- **Evolutivo:** preparado para incorporar IA/ML en el futuro
- **Modular:** cada parte puede evolucionar de forma independiente

---

## 3. Arquitectura general

El Entrenador IA se estructura en **cuatro capas principales**:


Cada capa cumple una función clara y desacoplada.

---

## 4. Capa de Entradas (Inputs)

### 4.1 Datos del atleta

- Edad
- Sexo (opcional)
- Años de experiencia
- VAM (Velocidad Aeróbica Máxima)
- Ritmos por zona
- Historial de lesiones (futuro)
- Historial de entrenamientos

### 4.2 Objetivo deportivo

- Distancia objetivo (5K, 10K, 21K, cross, etc.)
- Fecha de competición
- Prioridad (marca, completar, forma general)

### 4.3 Contexto del plan

- Volumen semanal
- Distribución de sesiones
- Sesiones duras por semana
- Tendencia de carga
- Alertas activas

---

## 5. Capa de Interpretación (Razonamiento)

Esta capa interpreta los datos aplicando **criterio entrenable**, no modelos opacos.

Ejemplos de razonamiento:

- Atleta joven + VAM alta + poco volumen  
  → priorizar consistencia antes que intensidad

- Incrementos de carga consecutivos  
  → riesgo de lesión, recomendar descarga

- Objetivo cercano (≤8 semanas)  
  → limitar cambios estructurales del plan

Las reglas son explícitas, versionables y auditables.

---

## 6. Capa de Decisión (Acciones)

Las decisiones se expresan como **acciones estructuradas**, no como texto libre.

### Ejemplos de acciones

```json
{
  "accion": "reducir_volumen",
  "cantidad": "15%",
  "motivo": "Incremento de carga superior al 25% durante dos semanas consecutivas"
}

{
  "accion": "convertir_sesion",
  "origen": "series",
  "destino": "rodaje",
  "motivo": "Exceso de sesiones de alta intensidad"
}
