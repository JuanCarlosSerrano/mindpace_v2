# MindPace v2 Frontend (MVP)

## Requisitos
- Node.js 18+

## Instalación

```bash
cd frontend
npm install
```

## Configuración

### Opción A (recomendada): proxy en Vite
- Arranca la API en `:8000`
- Ejecuta `npm run dev` en `:5173`
- El frontend llama a `/api/...` y Vite lo reenvía

### Opción B: base URL por env
Crear `.env` (opcional):

```
VITE_API_BASE_URL=http://localhost:8000
```

## Ejecutar

```bash
npm run dev
```

Abrir: http://localhost:5173

## Uso
- Define `plan_id`, `athlete_id`, `iso_week`
- Cargar semana
- Probar Dry-run / Aplicar / Revertir
- Enviar feedback y recargar

## Nota
- El frontend no recalcula métricas. Solo muestra el WeeklySummary JSON.
