# MindPace v2 Docker Deploy

## Requisitos
- Docker + Docker Compose

## Arranque

```bash
docker compose up --build
```

Frontend: http://localhost:8080  
API: http://localhost:8000

## Logs

```bash
docker compose logs -f api
docker compose logs -f web
```

## Parar

```bash
docker compose down
```

## Notas
- El frontend llama a `/api/...` y Nginx lo proxy a `api:8000`.
- Persistencia SQLite: la DB vive en `./data/mindpace_dev.db` (montada en `/app/data`).
- Healthchecks activos para `api` y `web` (puedes verlos con `docker compose ps`).
- Variables de entorno futuras (DB, secrets) se pueden añadir en `docker-compose.yml`.
